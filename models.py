from sqlalchemy import Column, Integer, String, Boolean, DateTime
from database import Base


class ResultConfiguration(Base):
    __tablename__ = "result_configuration"

    id = Column(Integer, primary_key=True, index=True)

    result_id = Column(String, unique=True, nullable=False)
    result_name = Column(String, nullable=False)

    result_type = Column(String, nullable=False)
    requires_execution = Column(Boolean, default=True)

    active = Column(Boolean, default=True)


class Occurrence(Base):
    __tablename__ = "occurrences"

    id = Column(Integer, primary_key=True, index=True)

    occurrence_id = Column(String, unique=True, nullable=False)

    result_id = Column(String, nullable=False)
    result_name = Column(String, nullable=False)

    created_datetime = Column(DateTime, nullable=False)

    status = Column(String, default="Pending")

    execution_datetime = Column(DateTime, nullable=True)

    punishment_type = Column(String, nullable=True)

    punishment_days = Column(Integer, nullable=True)
    punishment_hours = Column(Integer, nullable=True)
    punishment_minutes = Column(Integer, nullable=True)

    undo_datetime = Column(DateTime, nullable=True)


class ProcessedEvent(Base):
    __tablename__ = "processed_events"

    id = Column(Integer, primary_key=True, index=True)

    event_id = Column(String, unique=True, nullable=False)
    source = Column(String, nullable=False)

    processed_datetime = Column(DateTime, nullable=False)
