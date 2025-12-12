"""Log file parsing service."""
import csv
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class LogParser:
    """Parse various log file formats."""

    SYSLOG_PATTERN = re.compile(
        r'^(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+'
        r'(?P<host>\S+)\s+'
        r'(?P<process>\S+?)(\[(?P<pid>\d+)\])?:\s+'
        r'(?P<message>.+)$'
    )

    LOG_LEVEL_PATTERN = re.compile(
        r'\b(DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL)\b',
        re.IGNORECASE
    )

    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse a log file and return structured records.

        Args:
            file_path: Path to the log file

        Returns:
            List of parsed log records
        """
        file_path_obj = Path(file_path)
        extension = file_path_obj.suffix.lower()

        if extension == '.csv':
            return self.parse_csv(file_path)
        elif extension in ['.json', '.jsonl', '.ndjson']:
            return self.parse_json_lines(file_path)
        else:
            return self.parse_plain_text(file_path)

    def parse_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse CSV log file."""
        records = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    record = self._normalize_record(row)
                    records.append(record)
        except Exception as e:
            logger.error(f"Error parsing CSV file: {e}")
            raise
        return records

    def parse_json_lines(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse JSON Lines log file."""
        records = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        record = self._normalize_record(obj)
                        records.append(record)
                    except json.JSONDecodeError:
                        logger.warning(f"Skipping invalid JSON line: {line[:100]}")
        except Exception as e:
            logger.error(f"Error parsing JSON Lines file: {e}")
            raise
        return records

    def parse_plain_text(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse plain text log file (syslog format or generic)."""
        records = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    # Try syslog format first
                    match = self.SYSLOG_PATTERN.match(line)
                    if match:
                        record = {
                            'timestamp': self._parse_timestamp(match.group('timestamp')),
                            'source': match.group('host'),
                            'process': match.group('process'),
                            'message': match.group('message'),
                            'raw_text': line
                        }
                    else:
                        # Generic plain text
                        record = {
                            'message': line,
                            'raw_text': line,
                            'line_number': line_num
                        }

                    # Extract log level
                    level_match = self.LOG_LEVEL_PATTERN.search(line)
                    if level_match:
                        record['log_level'] = level_match.group(1).upper()

                    record = self._normalize_record(record)
                    records.append(record)
        except Exception as e:
            logger.error(f"Error parsing plain text file: {e}")
            raise
        return records

    def _normalize_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a raw record to standard format.

        Args:
            raw_record: Raw record dictionary

        Returns:
            Normalized record
        """
        normalized = {}

        # Timestamp (try various field names)
        timestamp_fields = ['timestamp', 'time', 'datetime', '@timestamp', 'ts']
        for field in timestamp_fields:
            if field in raw_record:
                ts = self._parse_timestamp(raw_record[field])
                if ts:
                    normalized['timestamp'] = ts
                    break

        # Log level
        level_fields = ['level', 'log_level', 'severity', 'priority']
        for field in level_fields:
            if field in raw_record:
                normalized['log_level'] = str(raw_record[field]).upper()
                break

        # Source
        source_fields = ['source', 'host', 'hostname', 'server', 'device']
        for field in source_fields:
            if field in raw_record:
                normalized['source'] = str(raw_record[field])
                break

        # Message
        message_fields = ['message', 'msg', 'text', 'description', 'event']
        for field in message_fields:
            if field in raw_record:
                normalized['message'] = str(raw_record[field])
                break

        # If no message found, concatenate all fields
        if 'message' not in normalized:
            normalized['message'] = ' '.join(
                f"{k}={v}" for k, v in raw_record.items()
                if k not in timestamp_fields + level_fields + source_fields
            )

        # Raw text
        if 'raw_text' not in normalized:
            normalized['raw_text'] = json.dumps(raw_record)

        # Store all other fields as extra_data
        normalized['extra_data'] = {
            k: v for k, v in raw_record.items()
            if k not in ['timestamp', 'log_level', 'source', 'message', 'raw_text']
        }

        return normalized

    def _parse_timestamp(self, ts_str: Any) -> Optional[datetime]:
        """Parse timestamp from various formats."""
        if isinstance(ts_str, datetime):
            return ts_str

        if not isinstance(ts_str, str):
            ts_str = str(ts_str)

        # Common timestamp formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%S.%f%z',
            '%d/%b/%Y:%H:%M:%S',
            '%b %d %H:%M:%S',
            '%Y-%m-%d',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(ts_str.strip(), fmt)
            except ValueError:
                continue

        # Try ISO format
        try:
            return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        except ValueError:
            pass

        logger.warning(f"Could not parse timestamp: {ts_str}")
        return None
