from datetime import date
from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .db import Base, engine, SessionLocal
from . import models

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Motel PMS")

# static files (css)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    rooms_count = db.query(models.Room).count()
    guests_count = 0          # we'll wire this later when Guest model exists
    occupied_count = 0        # we'll wire this later with reservations

    today_label = date.today().strftime("%b %d, %Y")

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "rooms_count": rooms_count,
            "guests_count": guests_count,
            "occupied_count": occupied_count,
            "today_label": today_label,
        },
    )
