# websql/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from websql.templating import templates
from websql.routes import dashboard, entities, trace, health, tracking

app = FastAPI(title="Tracelet - Parcel Tracking UI")
app.mount("/static", StaticFiles(directory="websql/static"), name="static")

app.include_router(dashboard.router)
app.include_router(tracking.router)
app.include_router(entities.router)
app.include_router(trace.router)
app.include_router(health.router)