"""File upload endpoint."""
import os
import json
import shutil
from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlmodel import Session, select
import logging

from database import get_session
from models import LogFile, LogRecord, FileUploadResponse
from services.parser import LogParser
from services.indexer import LogIndexer
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()

# Create upload directory
UPLOAD_DIR = "./data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=FileUploadResponse)
async def upload_log_file(
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    """
    Upload and process a log file.

    Args:
        file: Uploaded file
        session: Database session

    Returns:
        Upload response with file ID and status
    """
    try:
        # Create log file record
        log_file = LogFile(
            filename=file.filename or "unknown",
            file_size=0,
            status="processing"
        )
        session.add(log_file)
        session.commit()
        session.refresh(log_file)

        # Save uploaded file
        file_path = os.path.join(UPLOAD_DIR, f"{log_file.id}_{file.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Get file size
        log_file.file_size = os.path.getsize(file_path)
        session.add(log_file)
        session.commit()

        # Parse file
        logger.info(f"Parsing file: {file.filename}")
        parser = LogParser()
        records = parser.parse_file(file_path)

        if not records:
            log_file.status = "failed"
            log_file.error_message = "No records parsed from file"
            session.add(log_file)
            session.commit()
            raise HTTPException(status_code=400, detail="No records found in file")

        # Create indexer
        indexer = LogIndexer(
            embedding_model_name=settings.embedding_model,
            index_path=settings.faiss_index_path
        )

        # Create chunks
        chunks = indexer.create_chunks(records, settings.chunk_window_minutes)

        # Process records and create embeddings
        logger.info(f"Creating embeddings for {len(records)} records")
        messages = [r.get('message', '') for r in records]
        embeddings = indexer.create_embeddings(messages)

        # Save records to database
        db_records = []
        for idx, record in enumerate(records):
            # Find chunk_id
            chunk_id = "no_timestamp"
            for cid, chunk_records in chunks.items():
                if record in chunk_records:
                    chunk_id = cid
                    break

            # Create database record
            db_record = LogRecord(
                file_id=log_file.id,
                chunk_id=chunk_id,
                timestamp=record.get('timestamp'),
                log_level=record.get('log_level'),
                source=record.get('source'),
                message=record.get('message', ''),
                raw_text=record.get('raw_text', ''),
                embedding_vector=json.dumps(embeddings[idx].tolist()) if idx < len(embeddings) else None,
                extra_data=record.get('extra_data', {})
            )
            db_records.append(db_record)

        session.add_all(db_records)
        session.commit()

        # Refresh to get IDs
        for db_record in db_records:
            session.refresh(db_record)

        # Build FAISS index
        logger.info("Building FAISS index")
        indexer.build_index(log_file.id, [
            {
                'id': r.id,
                'embedding_vector': r.embedding_vector
            }
            for r in db_records if r.embedding_vector
        ])

        # Update file status
        log_file.status = "indexed"
        log_file.total_records = len(records)
        session.add(log_file)
        session.commit()

        logger.info(f"Successfully processed file {file.filename}: {len(records)} records")

        return FileUploadResponse(
            file_id=log_file.id,
            status="indexed",
            message=f"Successfully processed {len(records)} records"
        )

    except Exception as e:
        logger.error(f"Error processing file: {e}", exc_info=True)

        # Update file status to failed
        if 'log_file' in locals():
            log_file.status = "failed"
            log_file.error_message = str(e)
            session.add(log_file)
            session.commit()

        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.get("/files")
async def list_files(session: Session = Depends(get_session)):
    """List all uploaded files."""
    statement = select(LogFile).order_by(LogFile.upload_time.desc())
    files = session.exec(statement).all()
    return {"files": files}


@router.get("/files/{file_id}")
async def get_file(file_id: str, session: Session = Depends(get_session)):
    """Get file metadata."""
    file = session.get(LogFile, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file


@router.delete("/files/{file_id}")
async def delete_file(file_id: str, session: Session = Depends(get_session)):
    """
    Delete a file and all its associated data.

    Args:
        file_id: File identifier
        session: Database session

    Returns:
        Success message
    """
    from models import Anomaly

    # Get the file
    file = session.get(LogFile, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        # Delete associated log records
        statement = select(LogRecord).where(LogRecord.file_id == file_id)
        records = session.exec(statement).all()
        for record in records:
            session.delete(record)

        # Delete associated anomalies
        statement = select(Anomaly).where(Anomaly.file_id == file_id)
        anomalies = session.exec(statement).all()
        for anomaly in anomalies:
            session.delete(anomaly)

        # Delete the uploaded file from disk
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
        if os.path.exists(file_path):
            os.remove(file_path)

        # Delete FAISS index file if exists
        index_file = os.path.join(settings.faiss_index_path, f"{file_id}.index")
        if os.path.exists(index_file):
            os.remove(index_file)

        # Delete the file record
        session.delete(file)
        session.commit()

        logger.info(f"Successfully deleted file {file_id} and {len(records)} associated records")

        return {
            "success": True,
            "message": f"File '{file.filename}' deleted successfully",
            "deleted_records": len(records),
            "deleted_anomalies": len(anomalies)
        }

    except Exception as e:
        logger.error(f"Error deleting file: {e}", exc_info=True)
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")
