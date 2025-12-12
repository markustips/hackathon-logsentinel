"""Anomaly detection endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
import logging

from database import get_session
from models import LogFile, LogRecord, Anomaly, AnomalyResponse
from services.anomaly import AnomalyDetector
from services.mitre import MitreMapper

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/detect-anomalies/{file_id}")
async def detect_anomalies(
    file_id: str,
    session: Session = Depends(get_session)
):
    """
    Detect anomalies in a log file.

    Args:
        file_id: File identifier
        session: Database session

    Returns:
        Anomaly detection results
    """
    # Get file
    log_file = session.get(LogFile, file_id)
    if not log_file:
        raise HTTPException(status_code=404, detail="File not found")

    # Get records
    statement = select(LogRecord).where(LogRecord.file_id == file_id)
    records = session.exec(statement).all()

    if not records:
        raise HTTPException(status_code=404, detail="No records found for file")

    # Convert to dict format
    record_dicts = [
        {
            'id': r.id,
            'message': r.message,
            'log_level': r.log_level,
            'timestamp': r.timestamp,
            'embedding_vector': r.embedding_vector
        }
        for r in records
    ]

    # Run anomaly detection
    logger.info(f"Running anomaly detection on {len(record_dicts)} records")
    detector = AnomalyDetector()
    anomalies = detector.detect_anomalies(record_dicts)

    # Map to MITRE ATT&CK
    mapper = MitreMapper()

    # Get full record details for anomalies
    record_map = {r.id: r for r in records}
    enriched_anomalies = []

    for anomaly in anomalies:
        record = record_map.get(anomaly['record_id'])
        if not record:
            continue

        # Map to MITRE
        techniques = mapper.map_message(record.message)
        technique_ids = [t['id'] for t in techniques]

        # Create and save anomaly record
        db_anomaly = Anomaly(
            file_id=file_id,
            record_id=record.id,
            anomaly_type=anomaly['anomaly_type'],
            score=anomaly['score'],
            severity=anomaly['severity'],
            description=anomaly['description'],
            mitre_techniques=technique_ids
        )
        session.add(db_anomaly)
        enriched_anomalies.append(db_anomaly)

    session.commit()

    logger.info(f"Detected {len(enriched_anomalies)} anomalies")

    return {
        "file_id": file_id,
        "total_anomalies": len(enriched_anomalies),
        "anomalies": enriched_anomalies[:100]  # Return top 100
    }


@router.get("/anomalies", response_model=List[AnomalyResponse])
async def get_anomalies(
    file_id: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    min_score: float = Query(0.0, ge=0.0, le=100.0),
    session: Session = Depends(get_session)
):
    """
    Get detected anomalies.

    Args:
        file_id: Optional file filter
        limit: Maximum number of results
        min_score: Minimum anomaly score
        session: Database session

    Returns:
        List of anomalies
    """
    # Build query
    statement = select(Anomaly).where(Anomaly.score >= min_score)

    if file_id:
        statement = statement.where(Anomaly.file_id == file_id)

    statement = statement.order_by(Anomaly.score.desc()).limit(limit)

    anomalies = session.exec(statement).all()

    # Enrich with record details
    result = []
    for anomaly in anomalies:
        record = session.get(LogRecord, anomaly.record_id)
        if record:
            result.append(AnomalyResponse(
                id=anomaly.id,
                record_id=anomaly.record_id,
                timestamp=record.timestamp,
                anomaly_type=anomaly.anomaly_type,
                score=anomaly.score,
                severity=anomaly.severity,
                description=anomaly.description,
                message=record.message,
                mitre_techniques=anomaly.mitre_techniques
            ))

    return result


@router.get("/anomalies/{anomaly_id}")
async def get_anomaly(
    anomaly_id: str,
    session: Session = Depends(get_session)
):
    """Get details for a specific anomaly."""
    anomaly = session.get(Anomaly, anomaly_id)
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")

    record = session.get(LogRecord, anomaly.record_id)

    return {
        "anomaly": anomaly,
        "record": record,
        "mitre_details": [
            MitreMapper().get_technique_details(tid)
            for tid in anomaly.mitre_techniques
        ]
    }
