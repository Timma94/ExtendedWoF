from datetime import datetime
from random import randint

from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import engine, Base, get_db
from models import ResultConfiguration, Occurrence
from processor import process_wheel_event


# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="Extended Wheel of Fortune API",
    version="1.0.0"
)


# ============================================================
# STATIC FRONTEND
# ============================================================

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


@app.get("/")
def homepage():
    return FileResponse("static/index.html")


# ============================================================
# DATA MODELS
# ============================================================

class WheelEvent(BaseModel):
    event_id: str
    event_type: str
    result: str
    timestamp: datetime
    source: str = "Chastify"


class ResultCreate(BaseModel):
    result_id: str
    result_name: str
    result_type: str
    requires_execution: bool


class PunishmentRequest(BaseModel):
    punishment_type: str

    new_task_name: str | None = None

    minimum_days: int = 0
    minimum_hours: int = 0
    minimum_minutes: int = 0

    maximum_days: int = 0
    maximum_hours: int = 0
    maximum_minutes: int = 0


# ============================================================
# RESULT CONFIGURATION
# ============================================================

@app.get("/api/results")
def get_results(db: Session = Depends(get_db)):

    results = (
        db.query(ResultConfiguration)
        .order_by(ResultConfiguration.id)
        .all()
    )

    return results


@app.post("/api/results")
def create_result(
    result: ResultCreate,
    db: Session = Depends(get_db)
):

    existing = (
        db.query(ResultConfiguration)
        .filter(
            ResultConfiguration.result_id == result.result_id
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Result ID already exists."
        )

    new_result = ResultConfiguration(
        result_id=result.result_id,
        result_name=result.result_name,
        result_type=result.result_type,
        requires_execution=result.requires_execution
    )

    db.add(new_result)
    db.commit()
    db.refresh(new_result)

    return new_result


# ============================================================
# WHEEL EVENT
# ============================================================

@app.post("/api/wheel-event")
def receive_wheel_event(
    event: WheelEvent,
    db: Session = Depends(get_db)
):

    return process_wheel_event(
        db=db,
        event_id=event.event_id,
        event_type=event.event_type,
        result=event.result,
        timestamp=event.timestamp,
        source=event.source
    )


# ============================================================
# ACTIVE OCCURRENCES
# ============================================================

@app.get("/api/occurrences/active")
def get_active_occurrences(
    db: Session = Depends(get_db)
):

    occurrences = (
        db.query(Occurrence)
        .filter(
            Occurrence.status == "Pending"
        )
        .order_by(
            Occurrence.created_datetime
        )
        .all()
    )

    return occurrences


# ============================================================
# HISTORY
# ============================================================

@app.get("/api/occurrences/history")
def get_history(
    db: Session = Depends(get_db)
):

    occurrences = (
        db.query(Occurrence)
        .filter(
            Occurrence.status != "Pending"
        )
        .order_by(
            Occurrence.created_datetime.desc()
        )
        .all()
    )

    return occurrences


# ============================================================
# EXECUTE OCCURRENCE
# ============================================================

@app.post("/api/occurrences/{occurrence_id}/execute")
def execute_occurrence(
    occurrence_id: str,
    db: Session = Depends(get_db)
):

    occurrence = (
        db.query(Occurrence)
        .filter(
            Occurrence.occurrence_id == occurrence_id
        )
        .first()
    )

    if occurrence is None:
        raise HTTPException(
            status_code=404,
            detail="Occurrence not found."
        )

    if occurrence.status != "Pending":
        raise HTTPException(
            status_code=400,
            detail="Occurrence is not pending."
        )

    occurrence.status = "Executed"
    occurrence.execution_datetime = datetime.now()

    db.commit()

    return {
        "success": True,
        "occurrence_id": occurrence_id,
        "status": "Executed"
    }


# ============================================================
# UNDO EXECUTION
# ============================================================

@app.post("/api/occurrences/{occurrence_id}/undo")
def undo_occurrence(
    occurrence_id: str,
    db: Session = Depends(get_db)
):

    occurrence = (
        db.query(Occurrence)
        .filter(
            Occurrence.occurrence_id == occurrence_id
        )
        .first()
    )

    if occurrence is None:
        raise HTTPException(
            status_code=404,
            detail="Occurrence not found."
        )

    if occurrence.status != "Executed":
        raise HTTPException(
            status_code=400,
            detail="Only executed occurrences can be undone."
        )

    occurrence.status = "Pending"
    occurrence.undo_datetime = datetime.now()

    db.commit()

    return {
        "success": True,
        "occurrence_id": occurrence_id,
        "status": "Pending"
    }


# ============================================================
# PUNISHMENT
# ============================================================

@app.post("/api/occurrences/{occurrence_id}/punishment")
def apply_punishment(
    occurrence_id: str,
    punishment: PunishmentRequest,
    db: Session = Depends(get_db)
):

    occurrence = (
        db.query(Occurrence)
        .filter(
            Occurrence.occurrence_id == occurrence_id
        )
        .first()
    )

    if occurrence is None:
        raise HTTPException(
            status_code=404,
            detail="Occurrence not found."
        )

    if occurrence.status != "Pending":
        raise HTTPException(
            status_code=400,
            detail="Occurrence is not pending."
        )

    # --------------------------------------------------------
    # LOCK TIME PUNISHMENT
    # --------------------------------------------------------

    if punishment.punishment_type == "Lock Time":

        minimum = (
            punishment.minimum_days * 24 * 60
            + punishment.minimum_hours * 60
            + punishment.minimum_minutes
        )

        maximum = (
            punishment.maximum_days * 24 * 60
            + punishment.maximum_hours * 60
            + punishment.maximum_minutes
        )

        if maximum < minimum:
            raise HTTPException(
                status_code=400,
                detail="Maximum punishment must be greater than minimum."
            )

        generated_minutes = randint(
            minimum,
            maximum
        )

        days = generated_minutes // (24 * 60)

        remaining = generated_minutes % (24 * 60)

        hours = remaining // 60

        minutes = remaining % 60

        occurrence.punishment_type = "Lock Time"
        occurrence.punishment_days = days
        occurrence.punishment_hours = hours
        occurrence.punishment_minutes = minutes
        occurrence.status = "Punishment"

        db.commit()

        return {
            "success": True,
            "punishment_type": "Lock Time",
            "days": days,
            "hours": hours,
            "minutes": minutes
        }


    # --------------------------------------------------------
    # NEW TASK PUNISHMENT
    # --------------------------------------------------------

    if punishment.punishment_type == "New Task":

        occurrence.punishment_type = "New Task"
        occurrence.status = "Punishment"

        db.commit()

        return {
            "success": True,
            "punishment_type": "New Task"
        }


    raise HTTPException(
        status_code=400,
        detail="Invalid punishment type."
    )
