"""Log retrieval endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
import logging

from database import get_session
from models import LogRecord

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/logs/{record_id}")
async def get_log_record(
    record_id: str,
    session: Session = Depends(get_session)
):
    """
    Get a specific log record.

    Args:
        record_id: Record identifier
        session: Database session

    Returns:
        Log record details
    """
    record = session.get(LogRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Log record not found")

    return record


@router.get("/logs/chunk/{chunk_id}")
async def get_chunk_logs(
    chunk_id: str,
    file_id: Optional[str] = Query(None),
    session: Session = Depends(get_session)
):
    """
    Get all logs in a time chunk.

    Args:
        chunk_id: Chunk identifier
        file_id: Optional file filter
        session: Database session

    Returns:
        List of log records in the chunk
    """
    statement = select(LogRecord).where(LogRecord.chunk_id == chunk_id)

    if file_id:
        statement = statement.where(LogRecord.file_id == file_id)

    statement = statement.order_by(LogRecord.timestamp)

    records = session.exec(statement).all()

    return {"chunk_id": chunk_id, "records": records, "total": len(records)}


@router.get("/logs/window/{file_id}")
async def get_log_window(
    file_id: str,
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    session: Session = Depends(get_session)
):
    """
    Get logs within a time window.

    Args:
        file_id: File identifier
        start_time: Start timestamp (ISO format)
        end_time: End timestamp (ISO format)
        limit: Maximum number of records
        session: Database session

    Returns:
        List of log records
    """
    from datetime import datetime

    statement = select(LogRecord).where(LogRecord.file_id == file_id)

    if start_time:
        start_dt = datetime.fromisoformat(start_time)
        statement = statement.where(LogRecord.timestamp >= start_dt)

    if end_time:
        end_dt = datetime.fromisoformat(end_time)
        statement = statement.where(LogRecord.timestamp <= end_dt)

    statement = statement.order_by(LogRecord.timestamp).limit(limit)

    records = session.exec(statement).all()

    return {
        "file_id": file_id,
        "start_time": start_time,
        "end_time": end_time,
        "records": records,
        "total": len(records)
    }
