"""Anomaly detection engine."""
import json
import numpy as np
from typing import List, Dict, Any, Tuple
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Detect anomalies in log data using multiple techniques."""

    LOG_LEVEL_SCORES = {
        'DEBUG': 0,
        'INFO': 1,
        'WARN': 2,
        'WARNING': 2,
        'ERROR': 3,
        'CRITICAL': 4,
        'FATAL': 4
    }

    def detect_anomalies(
        self,
        records: List[Dict[str, Any]],
        methods: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies using multiple methods.

        Args:
            records: List of log records with embeddings
            methods: List of detection methods to use

        Returns:
            List of anomaly detections
        """
        if methods is None:
            methods = ['isolation_forest', 'rare_message', 'spike']

        anomalies = []

        if 'isolation_forest' in methods:
            anomalies.extend(self.detect_isolation_forest(records))

        if 'rare_message' in methods:
            anomalies.extend(self.detect_rare_messages(records))

        if 'spike' in methods:
            anomalies.extend(self.detect_spikes(records))

        # Deduplicate and sort by score
        seen = set()
        unique_anomalies = []
        for anomaly in sorted(anomalies, key=lambda x: x['score'], reverse=True):
            if anomaly['record_id'] not in seen:
                seen.add(anomaly['record_id'])
                unique_anomalies.append(anomaly)

        return unique_anomalies

    def detect_isolation_forest(
        self,
        records: List[Dict[str, Any]],
        contamination: float = 0.1
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies using Isolation Forest on embeddings.

        Args:
            records: Log records with embeddings
            contamination: Expected proportion of anomalies

        Returns:
            List of anomaly detections
        """
        try:
            from sklearn.ensemble import IsolationForest
        except ImportError:
            logger.error("scikit-learn not installed")
            return []

        # Extract features
        features = []
        valid_records = []

        for record in records:
            if not record.get('embedding_vector'):
                continue

            # Parse embedding
            try:
                embedding = json.loads(record['embedding_vector'])
            except (json.JSONDecodeError, TypeError):
                continue

            # Additional features
            feature_vector = list(embedding)

            # Add log level score
            log_level = record.get('log_level', 'INFO')
            feature_vector.append(self.LOG_LEVEL_SCORES.get(log_level, 1))

            # Add time delta (if available)
            if record.get('timestamp') and len(valid_records) > 0:
                prev_ts = valid_records[-1].get('timestamp')
                if prev_ts:
                    if isinstance(record['timestamp'], str):
                        curr_ts = datetime.fromisoformat(record['timestamp'])
                    else:
                        curr_ts = record['timestamp']

                    if isinstance(prev_ts, str):
                        prev_ts = datetime.fromisoformat(prev_ts)

                    delta = (curr_ts - prev_ts).total_seconds()
                    feature_vector.append(min(delta, 3600))  # Cap at 1 hour
                else:
                    feature_vector.append(0)
            else:
                feature_vector.append(0)

            features.append(feature_vector)
            valid_records.append(record)

        if len(features) < 10:
            logger.warning("Not enough records for Isolation Forest")
            return []

        # Train Isolation Forest
        X = np.array(features)
        clf = IsolationForest(contamination=contamination, random_state=42)
        predictions = clf.fit_predict(X)
        scores = clf.score_samples(X)

        # Normalize scores to 0-100
        min_score = scores.min()
        max_score = scores.max()
        if max_score > min_score:
            normalized_scores = 100 * (scores - min_score) / (max_score - min_score)
        else:
            normalized_scores = np.zeros_like(scores)

        # Create anomaly records
        anomalies = []
        for i, (pred, score) in enumerate(zip(predictions, normalized_scores)):
            if pred == -1:  # Anomaly
                record = valid_records[i]
                severity = self._calculate_severity(score)

                anomalies.append({
                    'record_id': record['id'],
                    'anomaly_type': 'isolation_forest',
                    'score': float(score),
                    'severity': severity,
                    'description': f'Anomalous pattern detected with score {score:.1f}/100'
                })

        logger.info(f"Isolation Forest detected {len(anomalies)} anomalies")
        return anomalies

    def detect_rare_messages(
        self,
        records: List[Dict[str, Any]],
        percentile: float = 5.0
    ) -> List[Dict[str, Any]]:
        """
        Detect rare/unusual messages based on frequency.

        Args:
            records: Log records
            percentile: Messages below this frequency percentile are rare

        Returns:
            List of anomaly detections
        """
        # Count message frequencies (normalized)
        message_counts = Counter()
        for record in records:
            message = record.get('message', '')
            # Normalize message (remove numbers, IPs, etc.)
            normalized = self._normalize_message(message)
            message_counts[normalized] += 1

        if not message_counts:
            return []

        # Calculate frequency threshold
        frequencies = list(message_counts.values())
        threshold = np.percentile(frequencies, percentile)

        # Find rare messages
        anomalies = []
        seen_normalized = set()

        for record in records:
            message = record.get('message', '')
            normalized = self._normalize_message(message)

            if normalized in seen_normalized:
                continue

            count = message_counts[normalized]
            if count <= threshold:
                # Calculate rarity score
                score = 100 * (1 - count / max(frequencies))
                severity = self._calculate_severity(score)

                anomalies.append({
                    'record_id': record['id'],
                    'anomaly_type': 'rare_message',
                    'score': float(score),
                    'severity': severity,
                    'description': f'Rare message pattern (appears {count} times, {percentile}th percentile)'
                })

                seen_normalized.add(normalized)

        logger.info(f"Rare message detection found {len(anomalies)} anomalies")
        return anomalies

    def detect_spikes(
        self,
        records: List[Dict[str, Any]],
        window_minutes: int = 5,
        std_threshold: float = 3.0
    ) -> List[Dict[str, Any]]:
        """
        Detect spikes in error rates or log volume.

        Args:
            records: Log records
            window_minutes: Time window for aggregation
            std_threshold: Number of standard deviations for spike detection

        Returns:
            List of anomaly detections
        """
        # Group by time windows
        windows = defaultdict(lambda: {'total': 0, 'errors': 0, 'records': []})

        for record in records:
            timestamp = record.get('timestamp')
            if not timestamp:
                continue

            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)

            # Round to window
            window_start = timestamp.replace(
                minute=(timestamp.minute // window_minutes) * window_minutes,
                second=0,
                microsecond=0
            )

            window_key = window_start.isoformat()
            windows[window_key]['total'] += 1
            windows[window_key]['records'].append(record)

            # Count errors
            log_level = record.get('log_level', 'INFO')
            if log_level in ['ERROR', 'CRITICAL', 'FATAL']:
                windows[window_key]['errors'] += 1

        if len(windows) < 3:
            logger.warning("Not enough time windows for spike detection")
            return []

        # Calculate statistics
        error_rates = []
        volumes = []
        for window in windows.values():
            error_rate = window['errors'] / max(window['total'], 1)
            error_rates.append(error_rate)
            volumes.append(window['total'])

        mean_error_rate = np.mean(error_rates)
        std_error_rate = np.std(error_rates)
        mean_volume = np.mean(volumes)
        std_volume = np.std(volumes)

        # Detect spikes
        anomalies = []
        for window_key, window in windows.items():
            error_rate = window['errors'] / max(window['total'], 1)
            volume = window['total']

            # Check for error rate spike
            if std_error_rate > 0:
                error_z_score = (error_rate - mean_error_rate) / std_error_rate
                if error_z_score > std_threshold:
                    # Mark records in this window
                    score = min(100, 50 + 10 * error_z_score)
                    severity = self._calculate_severity(score)

                    for record in window['records']:
                        if record.get('log_level') in ['ERROR', 'CRITICAL', 'FATAL']:
                            anomalies.append({
                                'record_id': record['id'],
                                'anomaly_type': 'spike',
                                'score': float(score),
                                'severity': severity,
                                'description': f'Error rate spike detected ({error_rate:.1%} vs {mean_error_rate:.1%} avg, {error_z_score:.1f}σ)'
                            })

            # Check for volume spike
            if std_volume > 0:
                volume_z_score = (volume - mean_volume) / std_volume
                if volume_z_score > std_threshold:
                    score = min(100, 40 + 10 * volume_z_score)
                    severity = self._calculate_severity(score)

                    # Mark first record in window
                    if window['records']:
                        anomalies.append({
                            'record_id': window['records'][0]['id'],
                            'anomaly_type': 'spike',
                            'score': float(score),
                            'severity': severity,
                            'description': f'Log volume spike ({volume} vs {mean_volume:.0f} avg, {volume_z_score:.1f}σ)'
                        })

        logger.info(f"Spike detection found {len(anomalies)} anomalies")
        return anomalies

    def _normalize_message(self, message: str) -> str:
        """Normalize message by removing variable parts."""
        import re

        # Remove IPs
        message = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', 'IP', message)

        # Remove numbers
        message = re.sub(r'\b\d+\b', 'NUM', message)

        # Remove timestamps
        message = re.sub(r'\d{4}-\d{2}-\d{2}', 'DATE', message)
        message = re.sub(r'\d{2}:\d{2}:\d{2}', 'TIME', message)

        # Remove UUIDs
        message = re.sub(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            'UUID',
            message,
            flags=re.IGNORECASE
        )

        return message.strip()

    def _calculate_severity(self, score: float) -> str:
        """Calculate severity level from score."""
        if score >= 80:
            return 'critical'
        elif score >= 60:
            return 'high'
        elif score >= 40:
            return 'medium'
        else:
            return 'low'
