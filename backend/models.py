"""Database models and schemas for LogSentinel AI."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Column, JSON
from pydantic import BaseModel
import uuid


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


# Database Models
class LogFile(SQLModel, table=True):
    """Log file metadata."""
    __tablename__ = "log_files"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    filename: str
    file_size: int
    upload_time: datetime = Field(default_factory=datetime.utcnow)
    status: str = "processing"  # processing, indexed, failed
    total_records: int = 0
    error_message: Optional[str] = None


class LogRecord(SQLModel, table=True):
    """Individual log record."""
    __tablename__ = "log_records"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    file_id: str = Field(foreign_key="log_files.id", index=True)
    chunk_id: str = Field(index=True)  # Time-based chunk identifier
    timestamp: Optional[datetime] = Field(default=None, index=True)
    log_level: Optional[str] = None
    source: Optional[str] = None
    message: str
    raw_text: str
    embedding_vector: Optional[str] = None  # JSON serialized
    extra_data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))


class Anomaly(SQLModel, table=True):
    """Detected anomaly."""
    __tablename__ = "anomalies"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    file_id: str = Field(foreign_key="log_files.id", index=True)
    record_id: str = Field(foreign_key="log_records.id")
    anomaly_type: str  # isolation_forest, rare_message, spike
    score: float = Field(index=True)  # 0-100
    severity: str  # low, medium, high, critical
    description: str
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    mitre_techniques: List[str] = Field(default_factory=list, sa_column=Column(JSON))


# API Schemas
class FileUploadResponse(BaseModel):
    """Response for file upload."""
    file_id: str
    status: str
    message: str


class SearchRequest(BaseModel):
    """Search request."""
    file_id: str
    query: str
    k: int = 10


class SearchResult(BaseModel):
    """Single search result."""
    record_id: str
    chunk_id: str
    timestamp: Optional[datetime]
    log_level: Optional[str]
    source: Optional[str]
    message: str
    score: float


class SearchResponse(BaseModel):
    """Search response."""
    results: List[SearchResult]
    total: int


class AnomalyResponse(BaseModel):
    """Anomaly response."""
    id: str
    record_id: str
    timestamp: Optional[datetime]
    anomaly_type: str
    score: float
    severity: str
    description: str
    message: str
    mitre_techniques: List[str]


class TimelineEvent(BaseModel):
    """Timeline event."""
    timestamp: datetime
    event_type: str
    severity: str
    count: int


class TimelineResponse(BaseModel):
    """Timeline response."""
    events: List[TimelineEvent]


class CopilotMessage(BaseModel):
    """Copilot chat message."""
    role: str  # user, assistant
    content: str
    agent: Optional[str] = None  # orchestrator, log_analyst, anomaly_hunter, threat_mapper
    references: List[str] = []  # Record IDs referenced


class CopilotRequest(BaseModel):
    """Copilot chat request."""
    file_id: str
    message: str
    history: List[CopilotMessage] = []


class CopilotResponse(BaseModel):
    """Copilot chat response."""
    message: str
    agent: str
    references: List[str]
    mitre_techniques: List[Dict[str, str]] = []


class MitreTechnique(BaseModel):
    """MITRE ATT&CK technique."""
    id: str
    name: str
    tactic: str
    url: str
