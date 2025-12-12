"""Tools for agents to interact with the backend."""
from typing import List, Dict, Any, Optional
from sqlmodel import Session, select
import logging

from models import LogRecord, Anomaly
from services.indexer import LogIndexer
from services.mitre_web_enhanced import WebEnhancedMitreMapper
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AgentTools:
    """Tools available to agents."""

    def __init__(self, session: Session):
        """Initialize tools with database session."""
        self.session = session
        self.indexer = LogIndexer(
            embedding_model_name=settings.embedding_model,
            index_path=settings.faiss_index_path
        )
        self.mapper = WebEnhancedMitreMapper(use_web_api=True)

    def search_logs(self, file_id: str, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """
        Search logs using semantic similarity.

        Args:
            file_id: File identifier
            query: Search query
            k: Number of results

        Returns:
            List of search results
        """
        logger.info(f"[Tool] Searching logs: {query}")

        try:
            # Perform search
            results = self.indexer.search(file_id, query, k)

            if not results:
                return []

            # Get record details
            record_ids = [r[0] for r in results]
            statement = select(LogRecord).where(LogRecord.id.in_(record_ids))
            records = self.session.exec(statement).all()

            # Build results
            record_map = {r.id: r for r in records}
            score_map = {r[0]: r[1] for r in results}

            search_results = []
            for record_id in record_ids:
                record = record_map.get(record_id)
                if record:
                    search_results.append({
                        'record_id': record.id,
                        'timestamp': record.timestamp.isoformat() if record.timestamp else None,
                        'log_level': record.log_level,
                        'source': record.source,
                        'message': record.message,
                        'score': score_map[record_id]
                    })

            return search_results

        except Exception as e:
            logger.error(f"Error in search_logs: {e}")
            return []

    def get_log_window(
        self,
        file_id: str,
        chunk_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get logs within a time window or chunk.

        Args:
            file_id: File identifier
            chunk_id: Optional chunk identifier
            start_time: Optional start timestamp
            end_time: Optional end timestamp
            limit: Maximum records

        Returns:
            List of log records
        """
        logger.info(f"[Tool] Getting log window: chunk_id={chunk_id}, start={start_time}, end={end_time}")

        try:
            from datetime import datetime

            statement = select(LogRecord).where(LogRecord.file_id == file_id)

            if chunk_id:
                statement = statement.where(LogRecord.chunk_id == chunk_id)

            if start_time:
                start_dt = datetime.fromisoformat(start_time)
                statement = statement.where(LogRecord.timestamp >= start_dt)

            if end_time:
                end_dt = datetime.fromisoformat(end_time)
                statement = statement.where(LogRecord.timestamp <= end_dt)

            statement = statement.order_by(LogRecord.timestamp).limit(limit)
            records = self.session.exec(statement).all()

            return [
                {
                    'record_id': r.id,
                    'timestamp': r.timestamp.isoformat() if r.timestamp else None,
                    'log_level': r.log_level,
                    'source': r.source,
                    'message': r.message
                }
                for r in records
            ]

        except Exception as e:
            logger.error(f"Error in get_log_window: {e}")
            return []

    def get_anomalies(
        self,
        file_id: str,
        limit: int = 50,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Get detected anomalies.

        Args:
            file_id: File identifier
            limit: Maximum results
            min_score: Minimum anomaly score

        Returns:
            List of anomalies
        """
        logger.info(f"[Tool] Getting anomalies: min_score={min_score}")

        try:
            statement = select(Anomaly).where(
                Anomaly.file_id == file_id,
                Anomaly.score >= min_score
            ).order_by(Anomaly.score.desc()).limit(limit)

            anomalies = self.session.exec(statement).all()

            # Enrich with record details
            results = []
            for anomaly in anomalies:
                record = self.session.get(LogRecord, anomaly.record_id)
                if record:
                    results.append({
                        'anomaly_id': anomaly.id,
                        'record_id': anomaly.record_id,
                        'timestamp': record.timestamp.isoformat() if record.timestamp else None,
                        'anomaly_type': anomaly.anomaly_type,
                        'score': anomaly.score,
                        'severity': anomaly.severity,
                        'description': anomaly.description,
                        'message': record.message,
                        'mitre_techniques': anomaly.mitre_techniques
                    })

            return results

        except Exception as e:
            logger.error(f"Error in get_anomalies: {e}")
            return []

    def map_to_mitre(self, message: str) -> List[Dict[str, str]]:
        """
        Map log message to MITRE ATT&CK techniques.

        Args:
            message: Log message

        Returns:
            List of MITRE techniques
        """
        logger.info(f"[Tool] Mapping to MITRE: {message[:100]}")

        try:
            return self.mapper.map_message(message)
        except Exception as e:
            logger.error(f"Error in map_to_mitre: {e}")
            return []

    def map_to_mitre_enhanced(self, message: str) -> List[Dict[str, Any]]:
        """
        Map log message to MITRE ATT&CK techniques with confidence scores.

        Args:
            message: Log message

        Returns:
            List of MITRE techniques with confidence scores
        """
        logger.info(f"[Tool] Enhanced MITRE mapping: {message[:100]}")

        try:
            return self.mapper.map_message_with_confidence(message)
        except Exception as e:
            logger.error(f"Error in map_to_mitre_enhanced: {e}")
            return []

    def get_technique_description(self, technique_id: str) -> str:
        """
        Get detailed description for a MITRE technique.

        Args:
            technique_id: MITRE technique ID

        Returns:
            Technique description
        """
        logger.info(f"[Tool] Getting technique description: {technique_id}")

        try:
            return self.mapper.get_technique_description(technique_id)
        except Exception as e:
            logger.error(f"Error in get_technique_description: {e}")
            return f"MITRE ATT&CK technique {technique_id}"

    def get_timeline(self, file_id: str) -> List[Dict[str, Any]]:
        """
        Get timeline of events.

        Args:
            file_id: File identifier

        Returns:
            Timeline events
        """
        logger.info(f"[Tool] Getting timeline")

        try:
            from collections import defaultdict

            statement = select(LogRecord).where(LogRecord.file_id == file_id).order_by(LogRecord.timestamp)
            records = self.session.exec(statement).all()

            # Group by chunk
            events_by_chunk = defaultdict(lambda: {
                'total': 0,
                'errors': 0,
                'timestamp': None,
                'messages': []
            })

            for record in records:
                chunk_id = record.chunk_id
                events_by_chunk[chunk_id]['total'] += 1

                if record.timestamp and not events_by_chunk[chunk_id]['timestamp']:
                    events_by_chunk[chunk_id]['timestamp'] = record.timestamp

                if record.log_level in ['ERROR', 'CRITICAL', 'FATAL']:
                    events_by_chunk[chunk_id]['errors'] += 1
                    events_by_chunk[chunk_id]['messages'].append(record.message[:100])

            # Convert to list
            timeline = []
            for chunk_id, data in events_by_chunk.items():
                if data['timestamp']:
                    timeline.append({
                        'timestamp': data['timestamp'].isoformat(),
                        'total_events': data['total'],
                        'error_count': data['errors'],
                        'sample_errors': data['messages'][:3]
                    })

            timeline.sort(key=lambda x: x['timestamp'])
            return timeline

        except Exception as e:
            logger.error(f"Error in get_timeline: {e}")
            return []

    def get_events_after(
        self,
        file_id: str,
        timestamp: str,
        minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Get all events that occurred after a specific timestamp.

        Args:
            file_id: File identifier
            timestamp: Starting timestamp (ISO format)
            minutes: Number of minutes after timestamp to retrieve

        Returns:
            List of log records
        """
        logger.info(f"[Tool] Getting events after {timestamp} for {minutes} minutes")

        try:
            from datetime import datetime, timedelta

            # Parse timestamp
            start_dt = datetime.fromisoformat(timestamp)
            end_dt = start_dt + timedelta(minutes=minutes)

            statement = select(LogRecord).where(
                LogRecord.file_id == file_id,
                LogRecord.timestamp >= start_dt,
                LogRecord.timestamp <= end_dt
            ).order_by(LogRecord.timestamp)

            records = self.session.exec(statement).all()

            return [
                {
                    'record_id': r.id,
                    'timestamp': r.timestamp.isoformat() if r.timestamp else None,
                    'log_level': r.log_level,
                    'source': r.source,
                    'message': r.message
                }
                for r in records
            ]

        except Exception as e:
            logger.error(f"Error in get_events_after: {e}")
            return []

    def search_by_ip(
        self,
        file_id: str,
        ip_address: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Find all log entries containing a specific IP address.

        Args:
            file_id: File identifier
            ip_address: IP address to search for
            limit: Maximum results

        Returns:
            List of log records
        """
        logger.info(f"[Tool] Searching for IP: {ip_address}")

        try:
            # Search using semantic search and text matching
            results = []

            # First try semantic search
            semantic_results = self.search_logs(file_id, f"IP {ip_address}", k=limit)
            results.extend(semantic_results)

            # Also do text matching to catch exact IP occurrences
            statement = select(LogRecord).where(
                LogRecord.file_id == file_id,
                LogRecord.message.contains(ip_address)
            ).order_by(LogRecord.timestamp).limit(limit)

            records = self.session.exec(statement).all()

            # Add text matches that aren't in semantic results
            result_ids = {r['record_id'] for r in results}
            for record in records:
                if record.id not in result_ids:
                    results.append({
                        'record_id': record.id,
                        'timestamp': record.timestamp.isoformat() if record.timestamp else None,
                        'log_level': record.log_level,
                        'source': record.source,
                        'message': record.message,
                        'score': 1.0  # Text match
                    })

            return results[:limit]

        except Exception as e:
            logger.error(f"Error in search_by_ip: {e}")
            return []

    def search_by_user(
        self,
        file_id: str,
        username: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Find all log entries for a specific username.

        Args:
            file_id: File identifier
            username: Username to search for
            limit: Maximum results

        Returns:
            List of log records
        """
        logger.info(f"[Tool] Searching for user: {username}")

        try:
            # Search using semantic search and text matching
            results = []

            # First try semantic search
            semantic_results = self.search_logs(file_id, f"user {username}", k=limit)
            results.extend(semantic_results)

            # Also do text matching
            statement = select(LogRecord).where(
                LogRecord.file_id == file_id,
                LogRecord.message.contains(username)
            ).order_by(LogRecord.timestamp).limit(limit)

            records = self.session.exec(statement).all()

            # Add text matches that aren't in semantic results
            result_ids = {r['record_id'] for r in results}
            for record in records:
                if record.id not in result_ids:
                    results.append({
                        'record_id': record.id,
                        'timestamp': record.timestamp.isoformat() if record.timestamp else None,
                        'log_level': record.log_level,
                        'source': record.source,
                        'message': record.message,
                        'score': 1.0  # Text match
                    })

            return results[:limit]

        except Exception as e:
            logger.error(f"Error in search_by_user: {e}")
            return []

    def get_all_events_chronological(
        self,
        file_id: str,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get all events in chronological order for attack chain analysis.

        Args:
            file_id: File identifier
            limit: Maximum records

        Returns:
            List of log records in chronological order
        """
        logger.info(f"[Tool] Getting all events chronologically")

        try:
            statement = select(LogRecord).where(
                LogRecord.file_id == file_id
            ).order_by(LogRecord.timestamp).limit(limit)

            records = self.session.exec(statement).all()

            return [
                {
                    'record_id': r.id,
                    'timestamp': r.timestamp.isoformat() if r.timestamp else None,
                    'log_level': r.log_level,
                    'source': r.source,
                    'message': r.message
                }
                for r in records
            ]

        except Exception as e:
            logger.error(f"Error in get_all_events_chronological: {e}")
            return []
