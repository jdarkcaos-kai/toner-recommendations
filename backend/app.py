from fastapi.responses import FileResponse
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PrinterModel(BaseModel):
    model: str
    toner: str

printer_data = [
    PrinterModel(model="HP LaserJet Pro M15", toner="HP 48A"),
    PrinterModel(model="Canon PIXMA MG2520", toner="Canon PG-245"),
]

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/recommendations/{model}")
def get_recommendation(model: str):
    for printer in printer_data:
        if printer.model.lower() == model.lower():
            return {"model": printer.model, "toner": printer.toner}
    return {"error": "No recommendations found for this model."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv('PORT', 8001)))

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
