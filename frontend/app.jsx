const { useState, useEffect } = React;
const API = ""; // same origin

const SAMPLES = [
  "There has been no water supply in our entire street in Gandhi Nagar for the last 4 days. Elderly residents are struggling.",
  "A live electric wire has fallen on the road near the school in Sector 7. It is very dangerous, children pass here.",
  "Garbage has not been collected for two weeks near the market. It is overflowing and there is a bad smell and mosquitoes.",
  "Huge pothole on the main road caused a bike accident yesterday. Someone was injured. Please repair urgently.",
  "I applied for my income certificate 20 days ago at the revenue office but there is still no response.",
];

/* ---- helpers ---- */
function priBadge(p){ return <span className={"badge p-"+p}>{p}</span>; }
function stBadge(s){ return <span className={"st st-"+s.replace(" ","")}>{s}</span>; }
// Always render timestamps in India Standard Time regardless of the viewer's locale.
function fmtIST(iso){
  try {
    return new Date(iso).toLocaleString("en-IN", {
      timeZone: "Asia/Kolkata", day: "2-digit", month: "short", year: "numeric",
      hour: "2-digit", minute: "2-digit", hour12: true,
    }) + " IST";
  } catch(e){ return iso; }
}
const govKey = () => localStorage.getItem("gov_key") || "";
function govFetch(url, opts={}){
  const headers = Object.assign({}, opts.headers, { "X-Official-Key": govKey() });
  return fetch(url, Object.assign({}, opts, { headers }));
}

/* ---------------- Citizen: submit ---------------- */
function SubmitForm(){
  const [form, setForm] = useState({ citizen_name:"", citizen_contact:"", location:"", channel:"web", raw_text:"" });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const upd = (k,v)=> setForm({ ...form, [k]:v });

  async function submit(e){
    e.preventDefault();
    setErr("");
    if(!form.raw_text.trim()){ setErr("Please describe your grievance."); return; }
    if(!form.location.trim()){ setErr("Location is required so we can route your case to the correct ward."); return; }
    setLoading(true); setResult(null);
    try {
      const r = await fetch(API+"/api/grievances", {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify(form),
      });
      if(!r.ok){ const d = await r.json().catch(()=>({})); throw new Error(d.detail?.[0]?.msg || d.detail || "Submission failed"); }
      setResult(await r.json());
    } catch(e){ setErr(String(e.message||e)); }
    setLoading(false);
  }

  return (
    <div className="grid2">
      <div className="card card-pad">
        <h2 className="section">File a Grievance</h2>
        <p className="sub">Describe your civic issue in your own words. The AI agent extracts the details,
          routes it to the right department, and grounds the action in official policy.</p>
        <form onSubmit={submit}>
          <div className="row">
            <div><label>Your name</label>
              <input value={form.citizen_name} onChange={e=>upd("citizen_name",e.target.value)} placeholder="Optional" /></div>
            <div><label>Contact</label>
              <input value={form.citizen_contact} onChange={e=>upd("citizen_contact",e.target.value)} placeholder="Phone / email (optional)" /></div>
          </div>
          <div className="row">
            <div><label>Location <span className="req">*</span></label>
              <input value={form.location} onChange={e=>upd("location",e.target.value)}
                className={!form.location.trim() && err ? "invalid" : ""}
                placeholder="Area / ward / landmark (required)" /></div>
            <div><label>Channel</label>
              <select value={form.channel} onChange={e=>upd("channel",e.target.value)}>
                <option value="web">Web form</option>
                <option value="voice">Voice note (transcribed)</option>
                <option value="image">Image / scanned letter (OCR)</option>
                <option value="letter">Handwritten letter</option>
              </select></div>
          </div>
          <label>Grievance details <span className="req">*</span></label>
          <textarea value={form.raw_text} onChange={e=>upd("raw_text",e.target.value)}
            placeholder="e.g. No water supply in our street for 4 days..." />
          <div className="chips">
            <span className="muted-sm" style={{width:"100%"}}>Try a sample:</span>
            {SAMPLES.map((s,i)=>(
              <span key={i} className="chip" onClick={()=>upd("raw_text",s)}>{s.slice(0,38)}…</span>
            ))}
          </div>
          {err && <p className="form-err">{err}</p>}
          <button className="btn" disabled={loading}>{loading ? "Agent analysing…" : "Submit to Samadhan-Agent"}</button>
        </form>
      </div>

      <div className="card card-pad">
        <h2 className="section">Agent Decision</h2>
        <p className="sub">Live output from the agentic pipeline.</p>
        {!result && <div className="empty">Submit a grievance to see the AI routing, priority and policy grounding.</div>}
        {result && (
          <div className="result">
            <div className="result-head">
              <span className="track-id">{result.tracking_id}</span>
              {priBadge(result.priority)} {stBadge(result.status)}
              <span className="spacer"></span>
              <span className={"mode-badge "+(result.ai_mode==="llm"?"mode-llm":"mode-rule")}>
                {result.ai_mode==="llm" ? "LLM" : "rule-based"}
              </span>
            </div>
            <div className="result-body">
              <dl className="kv">
                <dt>Summary</dt><dd>{result.summary}</dd>
                <dt>Department</dt><dd><b>{result.department}</b></dd>
                <dt>Category</dt><dd>{result.category}</dd>
                <dt>Sentiment</dt><dd>{result.sentiment}</dd>
                <dt>Location</dt><dd>{result.location || "—"}</dd>
                <dt>Next action</dt><dd>{result.suggested_action}</dd>
              </dl>
              <div className="policy">
                <b>📜 Policy basis (RAG-grounded)</b>{result.policy_basis}
              </div>
              <p className="muted-sm" style={{marginTop:12}}>
                Track this case anytime with id <span className="track-id">{result.tracking_id}</span> ·
                filed {fmtIST(result.created_at)}.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ---------------- Citizen: track ---------------- */
function Track(){
  const [tid, setTid] = useState("");
  const [res, setRes] = useState(null);
  const [err, setErr] = useState("");
  async function look(){
    setErr(""); setRes(null);
    if(!tid.trim()) return;
    const r = await fetch(API+"/api/track/"+tid.trim());
    if(r.ok) setRes(await r.json()); else setErr("No case found with that tracking id.");
  }
  return (
    <div className="card card-pad" style={{maxWidth:640, margin:"0 auto"}}>
      <h2 className="section">Track your grievance</h2>
      <p className="sub">Enter the tracking id you received, e.g. SAM-2026-0001.</p>
      <div className="toolbar">
        <input value={tid} onChange={e=>setTid(e.target.value)} placeholder="SAM-2026-0001" style={{flex:1}} />
        <button className="btn" style={{marginTop:0, width:120}} onClick={look}>Track</button>
      </div>
      {err && <p className="form-err">{err}</p>}
      {res && (
        <div className="result">
          <div className="result-head">
            <span className="track-id">{res.tracking_id}</span>{priBadge(res.priority)} {stBadge(res.status)}
          </div>
          <div className="result-body">
            <dl className="kv">
              <dt>Status</dt><dd><b>{res.status}</b></dd>
              <dt>Department</dt><dd>{res.department}</dd>
              <dt>Summary</dt><dd>{res.summary}</dd>
              <dt>Location</dt><dd>{res.location || "—"}</dd>
              <dt>Filed on</dt><dd>{fmtIST(res.created_at)}</dd>
              <dt>Last update</dt><dd>{fmtIST(res.updated_at)}</dd>
            </dl>
          </div>
        </div>
      )}
    </div>
  );
}

/* ---------------- Government: login ---------------- */
function GovLogin({ onAuth }){
  const [pw, setPw] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);
  async function login(e){
    e.preventDefault();
    setErr(""); setLoading(true);
    try {
      const r = await fetch(API+"/api/official/login", {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ password: pw }),
      });
      if(!r.ok) throw new Error("Invalid government access code.");
      const d = await r.json();
      localStorage.setItem("gov_key", d.token);
      onAuth();
    } catch(e){ setErr(String(e.message||e)); }
    setLoading(false);
  }
  return (
    <div className="card card-pad" style={{maxWidth:420, margin:"40px auto"}}>
      <div className="gov-lock">🔒</div>
      <h2 className="section" style={{textAlign:"center"}}>Government Portal</h2>
      <p className="sub" style={{textAlign:"center"}}>Restricted access for authorised officials only.</p>
      <form onSubmit={login}>
        <label>Access code</label>
        <input type="password" value={pw} onChange={e=>setPw(e.target.value)} placeholder="Enter government access code" autoFocus />
        {err && <p className="form-err">{err}</p>}
        <button className="btn" disabled={loading}>{loading ? "Verifying…" : "Sign in"}</button>
      </form>
      <p className="muted-sm" style={{textAlign:"center", marginTop:14}}>Citizens don’t need this — use the Citizen Portal to file or track a grievance.</p>
    </div>
  );
}

/* ---------------- Government: dashboard ---------------- */
const STATUSES = ["Submitted","Routed","In Progress","Resolved","Rejected"];

function Dashboard({ onLogout }){
  const [cases, setCases] = useState([]);
  const [stats, setStats] = useState(null);
  const [fDept, setFDept] = useState("");
  const [fStatus, setFStatus] = useState("");
  const [toast, setToast] = useState("");

  async function load(){
    const qs = new URLSearchParams();
    if(fDept) qs.set("department", fDept);
    if(fStatus) qs.set("status", fStatus);
    const [cr, sr] = await Promise.all([
      govFetch(API+"/api/grievances?"+qs),
      govFetch(API+"/api/stats"),
    ]);
    if(cr.status===401 || sr.status===401){ onLogout(); return; }
    setCases(await cr.json()); setStats(await sr.json());
  }
  useEffect(()=>{ load(); }, [fDept, fStatus]);

  async function setStatus(id, status){
    await govFetch(API+"/api/grievances/"+id+"/status", {
      method:"PATCH", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({ status }),
    });
    setToast("Status updated → "+status);
    setTimeout(()=>setToast(""), 1800);
    load();
  }

  const depts = stats ? Object.keys(stats.by_department) : [];

  return (
    <div>
      <div className="gov-bar">
        <span>🏛 <b>Government Portal</b> · Officials’ case management</span>
        <span className="spacer"></span>
        <button className="link-btn" onClick={onLogout}>Sign out</button>
      </div>
      {stats && (
        <div className="stats">
          <div className="stat"><div className="n">{stats.total}</div><div className="l">Total cases</div></div>
          <div className="stat"><div className="n red">{stats.by_priority?.Critical||0}</div><div className="l">Critical priority</div></div>
          <div className="stat"><div className="n orange">{stats.pending}</div><div className="l">Pending resolution</div></div>
          <div className="stat"><div className="n green">{stats.resolution_rate}%</div><div className="l">Resolution rate</div></div>
        </div>
      )}
      <div className="toolbar">
        <select value={fStatus} onChange={e=>setFStatus(e.target.value)}>
          <option value="">All statuses</option>
          {STATUSES.map(s=><option key={s}>{s}</option>)}
        </select>
        <select value={fDept} onChange={e=>setFDept(e.target.value)}>
          <option value="">All departments</option>
          {depts.map(d=><option key={d}>{d}</option>)}
        </select>
        <button className="btn btn-ghost" style={{marginTop:0,width:"auto",padding:"9px 16px"}} onClick={load}>Refresh</button>
      </div>

      {cases.length===0 && <div className="empty">No cases yet. File one from the Citizen Portal to populate the dashboard.</div>}
      {cases.map(c=>(
        <div className="case" key={c.id}>
          <div className="case-top">
            <span className="track-id">{c.tracking_id}</span>
            {priBadge(c.priority)} {stBadge(c.status)}
            <span className="spacer"></span>
            <span className="muted-sm">{fmtIST(c.created_at)}</span>
          </div>
          <div className="case-sum">{c.summary}</div>
          <div className="case-meta">
            <span>🏛 <b>{c.department}</b></span>
            <span>📍 {c.location || "—"}</span>
            <span>🙂 {c.sentiment}</span>
            <span>📨 {c.channel}</span>
            <span>👤 {c.citizen_name}</span>
          </div>
          <div className="raw"><b>Policy basis:</b> {c.policy_basis}</div>
          <div className="case-actions">
            <span className="muted-sm">Update status:</span>
            <select value={c.status} onChange={e=>setStatus(c.id, e.target.value)}>
              {STATUSES.map(s=><option key={s}>{s}</option>)}
            </select>
          </div>
        </div>
      ))}
      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}

function GovPortal(){
  const [authed, setAuthed] = useState(!!govKey());
  function logout(){ localStorage.removeItem("gov_key"); setAuthed(false); }
  return authed
    ? <Dashboard onLogout={logout} />
    : <GovLogin onAuth={()=>setAuthed(true)} />;
}

/* ---------------- App shell ---------------- */
function App(){
  const [portal, setPortal] = useState("citizen");   // citizen | gov
  const [ctab, setCtab] = useState("submit");         // submit | track
  const [health, setHealth] = useState(null);

  useEffect(()=>{ fetch(API+"/api/health").then(r=>r.json()).then(setHealth).catch(()=>{}); }, []);

  return (
    <div>
      <div className={"topbar "+(portal==="gov"?"gov":"")}>
        <div className="topbar-strip"></div>
        <div className="topbar-inner">
          <div className="logo">स</div>
          <div className="brand">
            <h1>Samadhan-Agent</h1>
            <p>AI-first public grievance redressal · AI for Bharat</p>
          </div>
          <span className="spacer"></span>
          <div className="portal-switch">
            <button className={portal==="citizen"?"on":""} onClick={()=>setPortal("citizen")}>👥 Citizen Portal</button>
            <button className={portal==="gov"?"on":""} onClick={()=>setPortal("gov")}>🏛 Government Portal</button>
          </div>
          {health && (
            <span className={"mode-badge "+(health.ai_mode==="llm"?"mode-llm":"mode-rule")}>
              AI: {health.ai_mode==="llm" ? "LLM" : "rule-based"}
            </span>
          )}
        </div>
        {portal==="citizen" && (
          <div className="tabs">
            <button className={"tab "+(ctab==="submit"?"active":"")} onClick={()=>setCtab("submit")}>📝 File Grievance</button>
            <button className={"tab "+(ctab==="track"?"active":"")} onClick={()=>setCtab("track")}>🔍 Track</button>
          </div>
        )}
      </div>
      <div className="wrap">
        {portal==="citizen" && ctab==="submit" && <SubmitForm />}
        {portal==="citizen" && ctab==="track" && <Track />}
        {portal==="gov" && <GovPortal />}
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
