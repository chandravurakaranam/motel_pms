from datetime import datetime
from datetime import date

from fastapi import FastAPI, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session, joinedload

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
    # Total Rooms
    rooms_count = db.query(models.Room).count()

    # Total Guests
    guests_count = db.query(models.Guest).count()

    # Rooms currently occupied
    occupied_count = (
        db.query(models.Room)
        .filter(models.Room.status == "occupied")
        .count()
    )

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
    request: Request,
    number: str = Form(...),
    room_type: str = Form("Standard"),
    status_value: str = Form("available"),
    db: Session = Depends(get_db),
):
    # 1) Check if room already exists
    existing = (
        db.query(models.Room)
        .filter(models.Room.number == number)
        .first()
    )

    if existing:
        rooms = db.query(models.Room).all()
        # Re-render page with error -> JS alert in template
        return templates.TemplateResponse(
            "rooms.html",
            {
                "request": request,
                "rooms": rooms,
                "error": f"Room {number} already exists.",
            },
            status_code=400,
        )

    # 2) Otherwise create new room
    new_room = models.Room(
        number=number,
        room_type=room_type,
        status=status_value,
    )
    db.add(new_room)
    db.commit()
    db.refresh(new_room)

    return RedirectResponse("/rooms", status_code=303)
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


@app.get("/reservations", response_class=HTMLResponse)
def reservations_page(request: Request, db: Session = Depends(get_db)):
    rooms = (
        db.query(models.Room)
        .filter(models.Room.status == "available")  # only available rooms
        .all()
    )
    guests = db.query(models.Guest).all()
    reservations = (
        db.query(models.Reservation)
        .options(
            joinedload(models.Reservation.room),
            joinedload(models.Reservation.guest),
        )
        .all()
    )

    return templates.TemplateResponse(
        "reservations.html",
        {
            "request": request,
            "rooms": rooms,
            "guests": guests,
            "reservations": reservations,
        },
    )


@app.post("/reservations/{reservation_id}/cancel")
def cancel_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
):
    reservation = db.query(models.Reservation).filter(
        models.Reservation.id == reservation_id
    ).first()

    if not reservation:
        # If somehow not found, just go back
        return RedirectResponse(url="/reservations", status_code=303)

    # Mark reservation as cancelled
    reservation.status = "cancelled"

    # Free up the room
    if reservation.room:
        reservation.room.status = "available"

    db.commit()
    return RedirectResponse(url="/reservations", status_code=303)


@app.post("/reservations")
def create_reservation(
    request: Request,
    room_id: int = Form(...),
    guest_id: int = Form(...),
    check_in: str = Form(...),
    check_out: str = Form(...),
    db: Session = Depends(get_db),
):
    # ---- Parse dates ----
    check_in_date = datetime.strptime(check_in, "%Y-%m-%d").date()
    check_out_date = datetime.strptime(check_out, "%Y-%m-%d").date()

    # ---- BASIC DATE VALIDATION ----
    if check_out_date <= check_in_date:
        rooms = db.query(models.Room).filter(
            models.Room.status == "available").all()
        guests = db.query(models.Guest).all()
        reservations = (
            db.query(models.Reservation)
            .options(
                joinedload(models.Reservation.room),
                joinedload(models.Reservation.guest),
            )
            .all()
        )

        return templates.TemplateResponse(
            "reservations.html",
            {
                "request": request,
                "rooms": rooms,
                "guests": guests,
                "reservations": reservations,
                "error": "Check-out date must be AFTER check-in date.",
            },
            status_code=400,
        )

    # ---- Ensure room exists ----
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # ---- Block reservation if room is NOT available ----
    if room.status != "available":
        rooms = db.query(models.Room).filter(
            models.Room.status == "available").all()
        guests = db.query(models.Guest).all()
        reservations = (
            db.query(models.Reservation)
            .options(
                joinedload(models.Reservation.room),
                joinedload(models.Reservation.guest),
            )
            .all()
        )

        return templates.TemplateResponse(
            "reservations.html",
            {
                "request": request,
                "rooms": rooms,
                "guests": guests,
                "reservations": reservations,
                "error": f"Room {room.number} is not available.",
            },
            status_code=400,
        )

    # ---- Create reservation ----
    reservation = models.Reservation(
        room_id=room_id,
        guest_id=guest_id,
        check_in=check_in_date,
        check_out=check_out_date,
        status="booked",
    )

    db.add(reservation)

    # ---- Auto-change room status ----
    room.status = "occupied"

    db.commit()

    return RedirectResponse("/reservations", status_code=303)
