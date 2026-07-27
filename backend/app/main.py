"""Samadhan-Agent — FastAPI backend + static frontend host.

Endpoints
    POST /api/grievances            submit a grievance (runs the agent)
    GET  /api/grievances            list all cases (officials' dashboard)
    GET  /api/grievances/{id}       single case
    GET  /api/track/{tracking_id}   public citizen tracking
    PATCH /api/grievances/{id}/status   official updates status
    GET  /api/stats                 dashboard metrics
    GET  /api/health                health + which AI mode is active
The React frontend (zero-build, CDN) is served from "/".
"""
import datetime as dt
import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy.orm import Session

load_dotenv()

# Shared secret for the Government Portal. Override in production via env var.
OFFICIAL_KEY = os.getenv("OFFICIAL_KEY", "samadhan-admin")


def require_official(x_official_key: str = Header(default="")):
    """Gate officials-only endpoints behind the shared government key."""
    if x_official_key != OFFICIAL_KEY:
        raise HTTPException(401, "Unauthorized — government login required")
    return True

from . import agent, extract, models, providers, schemas  # noqa: E402
from .database import Base, engine, get_db                 # noqa: E402

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Samadhan-Agent", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")


def _make_tracking_id(db: Session) -> str:
    year = dt.datetime.utcnow().year
    count = db.query(models.Grievance).count() + 1
    return f"SAM-{year}-{count:04d}"


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "provider": providers.active_provider(),
        "model": providers.active_model(),
    }


@app.get("/api/_diag")
def diag():
    """TEMP diagnostic: probe candidate Gemini models with the live key to find
    one that actually works on this account/plan. Remove after configuring."""
    if providers.active_provider() != "gemini":
        return {"provider": providers.active_provider(), "note": "Gemini key not set."}
    from google import genai
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    candidates = [
        "gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-2.0-flash-001",
        "gemini-2.5-flash-lite", "gemini-1.5-flash", "gemini-flash-latest",
    ]
    out = {}
    for m in candidates:
        try:
            r = client.models.generate_content(model=m, contents=["ping"])
            out[m] = "OK: " + (r.text or "")[:20]
        except Exception as e:  # noqa: BLE001
            out[m] = str(e)[:140]
    return out


@app.post("/api/official/login")
def official_login(payload: schemas.OfficialLogin):
    """Government Portal login. Returns the access key on success."""
    if payload.password != OFFICIAL_KEY:
        raise HTTPException(401, "Invalid government access code")
    return {"ok": True, "token": OFFICIAL_KEY}


@app.post("/api/extract")
async def extract_file(file: UploadFile = File(...)):
    """OCR an uploaded image / scanned PDF / handwritten letter into text.

    Public endpoint used by the citizen intake form for non-web channels.
    """
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(413, "File too large (max 10 MB).")
    result = extract.extract_text(data, file.content_type or "", file.filename or "")
    result["filename"] = file.filename
    return result


@app.post("/api/grievances", response_model=schemas.GrievanceOut)
def create_grievance(payload: schemas.GrievanceCreate, db: Session = Depends(get_db)):
    result = agent.analyze(payload.raw_text, payload.location or "")

    g = models.Grievance(
        tracking_id=_make_tracking_id(db),
        citizen_name=payload.citizen_name or "Anonymous",
        citizen_contact=payload.citizen_contact or "",
        channel=payload.channel or "web",
        raw_text=payload.raw_text,
        attachment_note=payload.attachment_note or "",
        status="Routed",
        **result,
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    return g


@app.get("/api/grievances", response_model=list[schemas.GrievanceOut])
def list_grievances(
    status: str | None = None,
    department: str | None = None,
    db: Session = Depends(get_db),
    _: bool = Depends(require_official),
):
    q = db.query(models.Grievance)
    if status:
        q = q.filter(models.Grievance.status == status)
    if department:
        q = q.filter(models.Grievance.department == department)
    # Critical first, then newest
    order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    rows = q.all()
    rows.sort(key=lambda g: (order.get(g.priority, 9), -g.id))
    return rows


@app.get("/api/grievances/{gid}", response_model=schemas.GrievanceOut)
def get_grievance(gid: int, db: Session = Depends(get_db), _: bool = Depends(require_official)):
    g = db.query(models.Grievance).get(gid)
    if not g:
        raise HTTPException(404, "Grievance not found")
    return g


@app.get("/api/track/{tracking_id}", response_model=schemas.GrievanceOut)
def track(tracking_id: str, db: Session = Depends(get_db)):
    g = db.query(models.Grievance).filter(models.Grievance.tracking_id == tracking_id).first()
    if not g:
        raise HTTPException(404, "No case with that tracking id")
    return g


@app.patch("/api/grievances/{gid}/status", response_model=schemas.GrievanceOut)
def update_status(
    gid: int,
    payload: schemas.StatusUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(require_official),
):
    g = db.query(models.Grievance).get(gid)
    if not g:
        raise HTTPException(404, "Grievance not found")
    valid = {"Submitted", "Routed", "In Progress", "Resolved", "Rejected"}
    if payload.status not in valid:
        raise HTTPException(400, f"Invalid status. Must be one of {sorted(valid)}")
    g.status = payload.status
    db.commit()
    db.refresh(g)
    return g


@app.get("/api/stats")
def stats(db: Session = Depends(get_db), _: bool = Depends(require_official)):
    total = db.query(models.Grievance).count()
    by_status = dict(
        db.query(models.Grievance.status, func.count()).group_by(models.Grievance.status).all()
    )
    by_dept = dict(
        db.query(models.Grievance.department, func.count()).group_by(models.Grievance.department).all()
    )
    by_priority = dict(
        db.query(models.Grievance.priority, func.count()).group_by(models.Grievance.priority).all()
    )
    resolved = by_status.get("Resolved", 0)
    return {
        "total": total,
        "resolved": resolved,
        "pending": total - resolved,
        "resolution_rate": round((resolved / total) * 100) if total else 0,
        "by_status": by_status,
        "by_department": by_dept,
        "by_priority": by_priority,
    }


# ---- Serve the frontend --------------------------------------------------
@app.get("/")
def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
