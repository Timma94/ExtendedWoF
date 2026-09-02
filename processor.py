from datetime import datetime

from models import (
    ResultConfiguration,
    Occurrence,
    ProcessedEvent
)


def generate_occurrence_id(db):
    """
    Generates the next occurrence number.
    Example: #00001
    """

    latest = (
        db.query(Occurrence)
        .order_by(Occurrence.id.desc())
        .first()
    )

    if latest is None:
        number = 1
    else:
        number = latest.id + 1

    return f"#{number:05d}"


def process_wheel_event(
    db,
    event_id: str,
    event_type: str,
    result: str,
    timestamp: datetime,
    source: str = "Chastify"
):
    """
    Processes a WheelEvent.

    Later, game.js / Chastify can send events
    to this same processing function through the API.
    """

    # Only process Wheel Spun events
    if event_type != "Wheel Spun":
        return {
            "success": True,
            "action": "ignored",
            "reason": "Event is not a Wheel Spun event."
        }

    # Prevent duplicate processing
    existing_event = (
        db.query(ProcessedEvent)
        .filter(
            ProcessedEvent.event_id == event_id
        )
        .first()
    )

    if existing_event:
        return {
            "success": True,
            "action": "duplicate",
            "reason": "Event has already been processed."
        }

    # Find the result in our configuration
    configuration = (
        db.query(ResultConfiguration)
        .filter(
            ResultConfiguration.result_name == result,
            ResultConfiguration.active == True
        )
        .first()
    )

    # Unknown result
    if configuration is None:

        processed = ProcessedEvent(
            event_id=event_id,
            source=source,
            processed_datetime=datetime.now()
        )

        db.add(processed)
        db.commit()

        return {
            "success": False,
            "action": "unknown_result",
            "result": result,
            "reason": "Result is not configured."
        }

    # Automatic result
    if not configuration.requires_execution:

        processed = ProcessedEvent(
            event_id=event_id,
            source=source,
            processed_datetime=datetime.now()
        )

        db.add(processed)
        db.commit()

        return {
            "success": True,
            "action": "ignored",
            "reason": "Automatic result."
        }

    # Create a new occurrence
    occurrence_id = generate_occurrence_id(db)

    occurrence = Occurrence(
        occurrence_id=occurrence_id,
        result_id=configuration.result_id,
        result_name=configuration.result_name,
        created_datetime=timestamp,
        status="Pending"
    )

    db.add(occurrence)

    # Mark the Chastify event as processed
    processed = ProcessedEvent(
        event_id=event_id,
        source=source,
        processed_datetime=datetime.now()
    )

    db.add(processed)

    db.commit()

    return {
        "success": True,
        "action": "occurrence_created",
        "occurrence_id": occurrence_id,
        "result": configuration.result_name
    }
