from fastapi.responses import FileResponse
import os
import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.getenv('DB_PATH', './app.db')

class WaitlistItem(BaseModel):
    email: str

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS waitlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS toners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            printer_model TEXT UNIQUE,
            toner_model TEXT,
            brand TEXT,
            page_yield TEXT
        )
    ''')
    cursor.executemany(
        "INSERT OR IGNORE INTO toners (printer_model, toner_model, brand, page_yield) VALUES (?,?,?,?)",
        [
            ("HP LaserJet Pro M15", "HP 48A (CF248A)", "HP", "~1000 páginas"),
            ("HP LaserJet Pro M404", "HP 58A (CF258A)", "HP", "~3000 páginas"),
            ("Canon PIXMA MG2520", "Canon PG-245 / CL-246", "Canon", "~180 páginas"),
            ("Canon PIXMA TS3120", "Canon PG-243 / CL-244", "Canon", "~180 páginas"),
            ("Epson EcoTank ET-2720", "Epson 502 Ink Set", "Epson", "~7500 páginas"),
            ("Brother HL-L2350DW", "Brother TN-730", "Brother", "~1200 páginas"),
        ]
    )
    conn.commit()
    conn.close()

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/recommendations")
def get_recommendations(model: str = ""):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if model.strip():
        cursor.execute(
            "SELECT * FROM toners WHERE LOWER(printer_model) LIKE LOWER(?)",
            (f"%{model.strip()}%",)
        )
    else:
        cursor.execute("SELECT * FROM toners LIMIT 6")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

@app.get("/toners")
def list_toners():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM toners")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

@app.post("/waitlist", response_model=dict)
def add_to_waitlist(item: WaitlistItem):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO waitlist (email) VALUES (?)', (item.email,))
    conn.commit()
    cursor.execute('SELECT COUNT(*) as count FROM waitlist')
    total = cursor.fetchone()['count']
    conn.close()
    return {"ok": True, "total": total}

@app.get("/waitlist/count", response_model=dict)
def get_waitlist_count():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as count FROM waitlist')
    count = cursor.fetchone()['count']
    conn.close()
    return {"count": count}

class RecommendationRequest(BaseModel):
    printer_model: str

class RecommendationResponse(BaseModel):
    toner: str

@app.post("/recommend", response_model=RecommendationResponse)
def recommend_toner(request: RecommendationRequest):
    recommendations = {
        "model_a": "Toner A",
        "model_b": "Toner B",
        "model_c": "Toner C"
    }
    toner = recommendations.get(request.printer_model.lower())
    if not toner:
        raise HTTPException(status_code=404, detail="No recommendations found for this printer model.")
    return RecommendationResponse(toner=toner)

@app.get("/", include_in_schema=False)
@app.get("/{_spa_path:path}", include_in_schema=False)
async def _serve_spa(_spa_path: str = ""):
    import os as _os
    _idx = _os.path.join(_os.path.dirname(__file__), "..", "frontend", "index.html")
    if not _os.path.exists(_idx):
        _idx = "frontend/index.html"
    if _os.path.exists(_idx):
        return FileResponse(_idx, media_type="text/html")
    from fastapi.responses import JSONResponse
    return JSONResponse({"error": "frontend not found"}, status_code=404)
