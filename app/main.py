from datetime import date

from fastapi import FastAPI, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .db import Base, engine, SessionLocal
from . import models

# --- DB setup: create tables based on models ---
Base.metadata.create_all(bind=engine)

# --- FastAPI app instance ---
app = FastAPI(title="Motel PMS")

# --- Static files (for CSS, etc.) ---
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# --- Templates (Jinja2) ---
templates = Jinja2Templates(directory="app/templates")


# --- Dependency: get DB session for each request ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Dashboard route ---
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    # Total rooms from DB
    rooms_count = db.query(models.Room).count()

    # We'll wire these up properly later when we add Guest + Reservation models
    guests_count = 0
    occupied_count = 0

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
# --- Rooms list page ---


@app.get("/rooms", response_class=HTMLResponse)
def list_rooms(request: Request, db: Session = Depends(get_db)):
    rooms = db.query(models.Room).order_by(models.Room.number).all()
    return templates.TemplateResponse(
        "rooms.html",
        {
            "request": request,
            "rooms": rooms,
        },
    )


# --- Create room (form POST) ---
@app.post("/rooms")
def create_room(
    number: str = Form(...),
    room_type: str = Form("Standard"),
    status_value: str = Form("available"),
    db: Session = Depends(get_db),
):
    room = models.Room(
        number=number,
        room_type=room_type,
        status=status_value,
    )
    db.add(room)
    db.commit()
    db.refresh(room)

    return RedirectResponse(url="/rooms", status_code=302)
# --- Guests page ---


@app.get("/guests", response_class=HTMLResponse)
def list_guests(request: Request, db: Session = Depends(get_db)):
    guests = db.query(models.Guest).order_by(models.Guest.name).all()
    return templates.TemplateResponse(
        "guests.html",
        {
            "request": request,
            "guests": guests,
        },
    )


@app.post("/guests")
def create_guest(
    name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(None),
    id_proof: str = Form(None),
    address: str = Form(None),
    db: Session = Depends(get_db),
):
    guest = models.Guest(
        name=name,
        phone=phone,
        email=email,
        id_proof=id_proof,
        address=address,
    )
    db.add(guest)
    db.commit()
    db.refresh(guest)

    return RedirectResponse(url="/guests", status_code=302)
# --- Guests Page ---


@app.get("/guests", response_class=HTMLResponse)
def guests_page(request: Request, db: Session = Depends(get_db)):
    guests = db.query(models.Guest).all()

    return templates.TemplateResponse(
        "guests.html",
        {
            "request": request,
            "guests": guests,
        }
    )


@app.post("/guests", response_class=HTMLResponse)
def create_guest(
    request: Request,
    full_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    id_proof: str = Form(...),
    address: str = Form(...),
    db: Session = Depends(get_db)
):
    new_guest = models.Guest(
        name=full_name,
        phone=phone,
        email=email,
        id_proof=id_proof,
        address=address
    )

    db.add(new_guest)
    db.commit()
    db.refresh(new_guest)

    return RedirectResponse(url="/guests", status_code=302)
