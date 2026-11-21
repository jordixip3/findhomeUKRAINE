import os, sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.models.database import init_db
from app.routers import api

app = FastAPI(title="FindHome Ukraine API", description="Розумна спільна оренда квартир та перевірені сусіди по всій Україні", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    try:
        init_db()
    except Exception as e:
        print(f"[FindHome Ukraine] DB init warning: {e}")

app.include_router(api.router)

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    app.mount("/UKRAINE/static", StaticFiles(directory=static_dir), name="static_routed")
    app.mount("/ukraine/static", StaticFiles(directory=static_dir), name="static_routed_lower")

@app.get("/", include_in_schema=False)
@app.get("/UKRAINE", include_in_schema=False)
@app.get("/UKRAINE/", include_in_schema=False)
@app.get("/ukraine", include_in_schema=False)
@app.get("/ukraine/", include_in_schema=False)
async def serve_home():
    idx = os.path.join(static_dir, "index.html")
    if os.path.exists(idx):
        return FileResponse(idx, headers={"Cache-Control": "no-cache"})
    return {"message": "FindHome Ukraine operational"}
