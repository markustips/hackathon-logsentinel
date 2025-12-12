"""Search endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
import logging

from database import get_session
from models import (
    LogFile, LogRecord, SearchRequest, SearchResponse, SearchResult,
    TimelineResponse, TimelineEvent
)
from services.indexer import LogIndexer
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search_logs(
    request: SearchRequest,
    session: Session = Depends(get_session)
):
    """
    Search logs using semantic similarity.

    Args:
        request: Search request
        session: Database session

    Returns:
        Search results
    """
    # Verify file exists
    log_file = session.get(LogFile, request.file_id)
    if not log_file:
        raise HTTPException(status_code=404, detail="File not found")

    if log_file.status != "indexed":
        raise HTTPException(status_code=400, detail="File not indexed yet")

    # Create indexer
    indexer = LogIndexer(
        embedding_model_name=settings.embedding_model,
        index_path=settings.faiss_index_path
    )

    # Search
    logger.info(f"Searching for: {request.query}")
    results = indexer.search(request.file_id, request.query, request.k)

    if not results:
        return SearchResponse(results=[], total=0)

    # Get record details
    record_ids = [r[0] for r in results]
    statement = select(LogRecord).where(LogRecord.id.in_(record_ids))
    records = session.exec(statement).all()

    # Create result map
    record_map = {r.id: r for r in records}
    score_map = {r[0]: r[1] for r in results}

    # Build response
    search_results = []
    for record_id in record_ids:
        record = record_map.get(record_id)
        if record:
            search_results.append(SearchResult(
                record_id=record.id,
                chunk_id=record.chunk_id,
                timestamp=record.timestamp,
                log_level=record.log_level,
                source=record.source,
                message=record.message,
                score=score_map[record_id]
            ))

    return SearchResponse(
        results=search_results,
        total=len(search_results)
    )


@router.get("/timeline/{file_id}", response_model=TimelineResponse)
async def get_timeline(
    file_id: str,
    session: Session = Depends(get_session)
):
    """
    Get timeline of events for a file.

    Args:
        file_id: File identifier
        session: Database session

    Returns:
        Timeline events
    """
    # Verify file exists
    log_file = session.get(LogFile, file_id)
    if not log_file:
        raise HTTPException(status_code=404, detail="File not found")

    # Get all records grouped by chunk
    statement = select(LogRecord).where(LogRecord.file_id == file_id).order_by(LogRecord.timestamp)
    records = session.exec(statement).all()

    # Group by chunk and severity
    from collections import defaultdict
    from datetime import datetime

    events_by_chunk = defaultdict(lambda: {
        'total': 0,
        'debug': 0,
        'info': 0,
        'warn': 0,
        'error': 0,
        'critical': 0,
        'timestamp': None
    })

    for record in records:
        chunk_id = record.chunk_id
        events_by_chunk[chunk_id]['total'] += 1

        if record.timestamp and not events_by_chunk[chunk_id]['timestamp']:
            events_by_chunk[chunk_id]['timestamp'] = record.timestamp

        level = (record.log_level or 'info').lower()
        if level in events_by_chunk[chunk_id]:
            events_by_chunk[chunk_id][level] += 1

    # Convert to timeline events
    events = []
    for chunk_id, data in events_by_chunk.items():
        if not data['timestamp']:
            continue

        # Determine severity
        if data['critical'] > 0:
            severity = 'critical'
            event_type = 'critical_error'
        elif data['error'] > 0:
            severity = 'high'
            event_type = 'error'
        elif data['warn'] > 0:
            severity = 'medium'
            event_type = 'warning'
        else:
            severity = 'low'
            event_type = 'info'

        events.append(TimelineEvent(
            timestamp=data['timestamp'],
            event_type=event_type,
            severity=severity,
            count=data['total']
        ))

    # Sort by timestamp
    events.sort(key=lambda e: e.timestamp)

    return TimelineResponse(events=events)
