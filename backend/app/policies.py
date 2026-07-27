"""Mock government policy knowledge base for the RAG layer.

In production this would be a vector store over official policy PDFs,
municipal by-laws, and citizen-charter SLA documents. Here it is a small
in-memory corpus keyed by department so every AI action can be grounded
in (and cite) an official policy — the deck's core differentiator.
"""

POLICY_CORPUS = [
    {
        "department": "Water Supply & Sewerage",
        "title": "Citizen Charter — Water Supply SLA",
        "keywords": ["water", "pipe", "leak", "sewage", "drainage", "tap", "supply", "contamination", "drinking"],
        "text": "Under the Citizen Charter, water-supply disruptions must be acknowledged within 24 hours "
                "and resolved within 72 hours. Contaminated or unsafe drinking water is a Critical-priority "
                "issue requiring resolution within 12 hours and immediate field inspection.",
    },
    {
        "department": "Electricity Board",
        "title": "Electricity (Supply) Grievance Norms",
        "keywords": ["electricity", "power", "outage", "transformer", "voltage", "wire", "current", "streetlight", "meter", "shock"],
        "text": "Power outages must be restored within 6 hours in urban and 24 hours in rural areas. "
                "Exposed live wires or electrocution hazards are Critical and mandate dispatch within 1 hour "
                "with the area isolated for public safety.",
    },
    {
        "department": "Sanitation & Waste Management",
        "title": "Solid Waste Management Rules — Grievance SLA",
        "keywords": ["garbage", "waste", "trash", "sanitation", "sewer", "clean", "dump", "toilet", "sweeping", "overflow"],
        "text": "Uncollected waste and public-sanitation complaints must be resolved within 48 hours. "
                "Overflowing sewage or garbage near schools, hospitals, or water sources is escalated to "
                "High priority for same-day action.",
    },
    {
        "department": "Public Works (Roads & Buildings)",
        "title": "PWD Road Maintenance Standards",
        "keywords": ["road", "pothole", "footpath", "bridge", "construction", "pavement", "manhole", "accident", "repair", "collapse"],
        "text": "Potholes and damaged roads are logged for repair within 7 working days. Open manholes, "
                "collapsed structures, or accident-prone road defects are Critical and cordoned off within "
                "4 hours pending permanent repair.",
    },
    {
        "department": "Health & Medical Services",
        "title": "Public Health Response Protocol",
        "keywords": ["health", "hospital", "disease", "medicine", "doctor", "dengue", "malaria", "outbreak", "clinic", "ambulance", "mosquito"],
        "text": "Public-health grievances are triaged within 24 hours. Suspected disease outbreaks, "
                "contamination, or vector-borne clusters trigger Critical priority with a health-team "
                "inspection within 12 hours.",
    },
    {
        "department": "Police / Public Safety",
        "title": "Public Safety Grievance Handling",
        "keywords": ["police", "safety", "crime", "harassment", "theft", "violence", "threat", "traffic", "encroachment", "noise"],
        "text": "Public-safety complaints are acknowledged immediately and routed to the jurisdictional "
                "station. Threats to life or ongoing incidents are Critical and forwarded for immediate "
                "field response.",
    },
    {
        "department": "Revenue & Land Records",
        "title": "Revenue Services Citizen Charter",
        "keywords": ["land", "revenue", "certificate", "property", "tax", "record", "mutation", "encroachment", "survey", "document"],
        "text": "Land-record and certificate requests must be processed within 15 working days. Disputes "
                "involving fraud or unauthorized mutation are flagged High for supervisory review.",
    },
    {
        "department": "General Administration",
        "title": "General Grievance Redressal Guidelines",
        "keywords": [],
        "text": "All grievances not mapped to a specialised department are handled by General Administration, "
                "acknowledged within 24 hours and either resolved or reassigned within 5 working days under "
                "the state's public grievance redressal mechanism.",
    },
]


def retrieve_policy(text: str, department: str | None = None) -> dict:
    """Lightweight keyword retrieval — stands in for a vector search.

    Returns the single most relevant policy document. If a department is
    already known, that policy is preferred; otherwise the best keyword
    overlap wins, falling back to General Administration.
    """
    text_l = (text or "").lower()

    if department:
        for doc in POLICY_CORPUS:
            if doc["department"] == department:
                return doc

    best, best_score = None, 0
    for doc in POLICY_CORPUS:
        score = sum(1 for kw in doc["keywords"] if kw in text_l)
        if score > best_score:
            best, best_score = doc, score

    return best or POLICY_CORPUS[-1]  # General Administration fallback
