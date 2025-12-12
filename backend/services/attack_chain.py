"""Attack chain correlation and severity scoring service."""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class AttackSequence:
    """Detected attack sequence."""
    name: str
    events: List[Dict[str, Any]]
    severity: int
    mitre_techniques: List[str]
    assessment: str
    attack_stage: str
    time_span_minutes: float


# Known attack patterns - the SECRET SAUCE for winning
ATTACK_PATTERNS = {
    "brute_force_success": {
        "description": "Brute force attack succeeded - attacker gained access",
        "sequence": [
            {"pattern": r"(failed|unsuccessful|invalid).*login|authentication.*fail", "min_count": 3, "name": "failed_logins"},
            {"pattern": r"(successful|accepted).*login|authentication.*success", "min_count": 1, "max_gap_minutes": 10, "name": "successful_login"},
        ],
        "severity": 80,
        "techniques": ["T1110", "T1078"],
        "attack_stage": "Mid-Stage"
    },

    "persistence_established": {
        "description": "Attacker established persistence via new account",
        "sequence": [
            {"pattern": r"(successful|accepted).*login", "min_count": 1, "name": "initial_access"},
            {"pattern": r"(user|account).*(created|added|new)|backdoor.*user", "min_count": 1, "max_gap_minutes": 30, "name": "account_creation"},
        ],
        "severity": 85,
        "techniques": ["T1078", "T1136"],
        "attack_stage": "Late-Stage"
    },

    "privilege_escalation_chain": {
        "description": "Attacker escalated privileges after initial access",
        "sequence": [
            {"pattern": r"(successful|accepted).*login", "min_count": 1, "name": "initial_access"},
            {"pattern": r"privilege.*(grant|escalat)|admin.*added|sudo.*grant", "min_count": 1, "max_gap_minutes": 30, "name": "privilege_escalation"},
        ],
        "severity": 88,
        "techniques": ["T1078", "T1068", "T1098"],
        "attack_stage": "Late-Stage"
    },

    "ot_safety_bypass": {
        "description": "CRITICAL: Safety systems compromised in OT environment",
        "sequence": [
            {"pattern": r"(config|parameter).*(change|modif)", "min_count": 1, "name": "config_change"},
            {"pattern": r"(alarm|safety).*(suppress|override|disable|bypass)|interlock.*bypass", "min_count": 1, "max_gap_minutes": 30, "name": "safety_bypass"},
        ],
        "severity": 95,
        "techniques": ["T0836", "T0878"],
        "attack_stage": "Impact"
    },

    "plc_compromise": {
        "description": "CRITICAL: PLC control compromised - physical process at risk",
        "sequence": [
            {"pattern": r"plc.*(write|program|upload|download)|ladder.*logic|firmware.*update", "min_count": 1, "name": "plc_programming"},
            {"pattern": r"setpoint.*(change|modif)|parameter.*(force|alter)", "min_count": 1, "max_gap_minutes": 30, "name": "setpoint_modification"},
        ],
        "severity": 95,
        "techniques": ["T0843", "T0836"],
        "attack_stage": "Impact"
    },

    "complete_ot_breach": {
        "description": "CRITICAL: Complete OT/SCADA compromise with physical impact",
        "sequence": [
            {"pattern": r"(failed|unsuccessful).*login", "min_count": 3, "name": "brute_force"},
            {"pattern": r"(successful|accepted).*login", "min_count": 1, "max_gap_minutes": 10, "name": "successful_access"},
            {"pattern": r"(user|account).*(created|added)", "min_count": 1, "max_gap_minutes": 30, "name": "persistence"},
            {"pattern": r"plc.*(upload|program|write)|config.*download", "min_count": 1, "max_gap_minutes": 60, "name": "plc_access"},
            {"pattern": r"(alarm|safety).*(suppress|disable)", "min_count": 1, "max_gap_minutes": 60, "name": "safety_suppression"},
            {"pattern": r"setpoint.*change|parameter.*(force|modif)|emergency.*shutdown", "min_count": 1, "max_gap_minutes": 60, "name": "process_manipulation"},
        ],
        "severity": 100,
        "techniques": ["T1110", "T1078", "T1136", "T0843", "T0878", "T0836"],
        "attack_stage": "Impact"
    },

    "lateral_movement_detected": {
        "description": "Attacker moving laterally across network",
        "sequence": [
            {"pattern": r"(successful|accepted).*login", "min_count": 1, "name": "initial_access"},
            {"pattern": r"(rdp|smb|ssh|remote).*(connect|access|login)", "min_count": 2, "max_gap_minutes": 60, "name": "lateral_movement"},
        ],
        "severity": 82,
        "techniques": ["T1078", "T1021"],
        "attack_stage": "Mid-Stage"
    },

    "data_exfiltration": {
        "description": "Data exfiltration detected after compromise",
        "sequence": [
            {"pattern": r"(successful|accepted).*login", "min_count": 1, "name": "initial_access"},
            {"pattern": r"(data|file).*(transfer|upload|exfil|send)", "min_count": 1, "max_gap_minutes": 120, "name": "exfiltration"},
        ],
        "severity": 90,
        "techniques": ["T1078", "T1041"],
        "attack_stage": "Impact"
    },

    "command_and_control": {
        "description": "Attacker establishing command and control communication",
        "sequence": [
            {"pattern": r"(successful|accepted).*login|initial.access", "min_count": 1, "name": "initial_access"},
            {"pattern": r"(outbound.connection|beacon|c2|domain.lookup).*(ip|domain|port)", "min_count": 2, "max_gap_minutes": 60, "name": "c2_traffic"},
        ],
        "severity": 85, # Moderate to High
        "techniques": ["T1071", "T1105", "T1095"], # Application Layer Protocol, Ingress Tool Transfer, Network Service Scanning
        "attack_stage": "Mid-Stage"
    },

    "defense_evasion": {
        "description": "Attacker attempting to cover tracks",
        "sequence": [
            {"pattern": r"(successful|accepted).*login", "min_count": 1, "name": "initial_access"},
            {"pattern": r"(log|audit).*(clear|delete|wipe|disable)|antivirus.*(disable|stop)", "min_count": 1, "max_gap_minutes": 60, "name": "evasion"},
        ],
        "severity": 87,
        "techniques": ["T1078", "T1070", "T1562"],
        "attack_stage": "Late-Stage"
    }
}


def detect_attack_sequences(events: List[Dict[str, Any]]) -> List[AttackSequence]:
    """
    Detect known attack patterns in event sequence.

    Args:
        events: List of log events with timestamps, messages, etc.

    Returns:
        List of detected attack sequences sorted by severity
    """
    logger.info(f"Analyzing {len(events)} events for attack sequences")

    detected = []

    for pattern_name, pattern_def in ATTACK_PATTERNS.items():
        matches = match_sequence(events, pattern_def["sequence"])

        if matches:
            # Calculate time span
            timestamps = [e.get('timestamp') for e in matches if e.get('timestamp')]
            time_span = 0.0

            if len(timestamps) >= 2:
                # Parse timestamps
                parsed_timestamps = []
                for ts in timestamps:
                    if isinstance(ts, str):
                        try:
                            parsed_timestamps.append(datetime.fromisoformat(ts))
                        except:
                            continue
                    elif isinstance(ts, datetime):
                        parsed_timestamps.append(ts)

                if len(parsed_timestamps) >= 2:
                    time_span = (max(parsed_timestamps) - min(parsed_timestamps)).total_seconds() / 60.0

            detected.append(AttackSequence(
                name=pattern_name,
                events=matches,
                severity=pattern_def["severity"],
                mitre_techniques=pattern_def["techniques"],
                assessment=pattern_def["description"],
                attack_stage=pattern_def.get("attack_stage", "Unknown"),
                time_span_minutes=time_span
            ))

            logger.info(f"Detected attack sequence: {pattern_name} (severity: {pattern_def['severity']})")

    # Sort by severity (highest first)
    detected.sort(key=lambda x: x.severity, reverse=True)

    return detected


def match_sequence(events: List[Dict[str, Any]], sequence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Match a sequence of patterns in events.

    Args:
        events: List of log events
        sequence: Pattern sequence to match

    Returns:
        List of matched events (empty if sequence not found)
    """
    if not events or not sequence:
        return []

    matched_events = []
    current_step = 0
    last_match_time = None

    for event in events:
        if current_step >= len(sequence):
            break

        step = sequence[current_step]
        pattern = step["pattern"]
        message = event.get('message', '').lower()

        # Check if pattern matches
        if re.search(pattern, message, re.IGNORECASE):
            # Check time gap constraint
            if last_match_time and step.get('max_gap_minutes'):
                event_time = event.get('timestamp')
                if event_time:
                    if isinstance(event_time, str):
                        try:
                            event_time = datetime.fromisoformat(event_time)
                        except:
                            event_time = None

                    if event_time and isinstance(last_match_time, datetime):
                        gap_minutes = (event_time - last_match_time).total_seconds() / 60.0
                        if gap_minutes > step['max_gap_minutes']:
                            # Gap too large, reset
                            matched_events = []
                            current_step = 0
                            last_match_time = None
                            continue

            # Check minimum count
            min_count = step.get('min_count', 1)

            # Count how many times we've seen this pattern
            if current_step < len(matched_events):
                # Already have some matches for this step
                step_matches = [e for e in matched_events if e.get('_step') == current_step]
                if len(step_matches) + 1 >= min_count:
                    # Move to next step
                    matched_events.append({**event, '_step': current_step})
                    current_step += 1

                    # Update last match time
                    event_time = event.get('timestamp')
                    if event_time:
                        if isinstance(event_time, str):
                            try:
                                last_match_time = datetime.fromisoformat(event_time)
                            except:
                                pass
                        else:
                            last_match_time = event_time
                else:
                    # Still collecting matches for this step
                    matched_events.append({**event, '_step': current_step})
            else:
                # First match for this step
                if min_count <= 1:
                    # Only need one match, move to next step
                    matched_events.append({**event, '_step': current_step})
                    current_step += 1

                    # Update last match time
                    event_time = event.get('timestamp')
                    if event_time:
                        if isinstance(event_time, str):
                            try:
                                last_match_time = datetime.fromisoformat(event_time)
                            except:
                                pass
                        else:
                            last_match_time = event_time
                else:
                    # Need multiple matches, start collecting
                    matched_events.append({**event, '_step': current_step})

    # Check if we matched the entire sequence
    if current_step >= len(sequence):
        return matched_events

    return []


def calculate_severity_score(
    attack_sequences: List[AttackSequence],
    techniques: List[str],
    is_ot_environment: bool = True
) -> int:
    """
    Calculate overall severity score (0-100) based on attack chain analysis.

    Args:
        attack_sequences: Detected attack sequences
        techniques: MITRE techniques identified
        is_ot_environment: Whether this is an OT/SCADA environment

    Returns:
        Severity score from 0-100
    """
    score = 0

    # Base score from highest severity sequence
    if attack_sequences:
        score = attack_sequences[0].severity
    else:
        score = 30  # Base score for any suspicious activity

    # Attack succeeded? (detected a success pattern)
    attack_succeeded = any(
        seq.name in ['brute_force_success', 'persistence_established', 'complete_ot_breach']
        for seq in attack_sequences
    )
    if attack_succeeded:
        score = min(score + 30, 100)

    # Multiple techniques used
    unique_techniques = set(techniques)
    technique_bonus = min(len(unique_techniques) * 5, 25)
    score = min(score + technique_bonus, 100)

    # Persistence achieved
    persistence = any(
        'T1136' in seq.mitre_techniques or 'T1543' in seq.mitre_techniques or 'T1053' in seq.mitre_techniques
        for seq in attack_sequences
    )
    if persistence:
        score = min(score + 15, 100)

    # Safety systems affected (OT-specific)
    safety_affected = any(
        'T0878' in seq.mitre_techniques or 'T0836' in seq.mitre_techniques
        for seq in attack_sequences
    )
    if safety_affected:
        score = min(score + 20, 100)

    # Physical impact occurred
    physical_impact = any(
        seq.name in ['plc_compromise', 'complete_ot_breach', 'ot_safety_bypass']
        for seq in attack_sequences
    )
    if physical_impact:
        score = min(score + 25, 100)

    # OT/SCADA environment base boost
    if is_ot_environment:
        score = min(score + 10, 100)

    return int(score)


def determine_attack_stage(
    attack_sequences: List[AttackSequence],
    techniques: List[str]
) -> str:
    """
    Determine current attack stage based on techniques and sequences observed.

    Args:
        attack_sequences: Detected attack sequences
        techniques: MITRE techniques identified

    Returns:
        Attack stage: Initial, Mid-Stage, Late-Stage, or Impact
    """
    # Impact techniques - highest priority
    impact_techniques = {'T1489', 'T0880', 'T0813', 'T0831', 'T0816', 'T0836', 'T0878', 'T1486'}

    # Persistence techniques
    persistence_techniques = {'T1136', 'T1053', 'T0839', 'T1543', 'T1098'}

    # Lateral movement / privilege escalation
    movement_techniques = {'T1021', 'T1078', 'T1068', 'T0886'}

    # Initial access / reconnaissance
    initial_techniques = {'T1110', 'T1190', 'T1566', 'T1046', 'T0840'}

    technique_set = set(techniques)

    # Check for impact stage
    if technique_set & impact_techniques:
        return "Impact"

    # Check attack sequences for stage indicators
    if attack_sequences:
        highest_severity_seq = attack_sequences[0]
        if highest_severity_seq.attack_stage:
            return highest_severity_seq.attack_stage

    # Fall back to technique-based determination
    if technique_set & persistence_techniques:
        if len(technique_set) > 3:
            return "Late-Stage"
        return "Mid-Stage"

    if technique_set & movement_techniques:
        return "Mid-Stage"

    if technique_set & initial_techniques:
        # Check if attack succeeded
        if any(seq.name == 'brute_force_success' for seq in attack_sequences):
            return "Mid-Stage"
        return "Initial"

    return "Initial"


def calculate_risk_level(severity_score: int) -> str:
    """
    Calculate risk level from severity score.

    Args:
        severity_score: Score from 0-100

    Returns:
        Risk level: LOW, MEDIUM, HIGH, CRITICAL
    """
    if severity_score >= 90:
        return "CRITICAL"
    elif severity_score >= 70:
        return "HIGH"
    elif severity_score >= 50:
        return "MEDIUM"
    else:
        return "LOW"


def assess_ot_safety_impact(
    attack_sequences: List[AttackSequence],
    techniques: List[str]
) -> Dict[str, Any]:
    """
    Assess safety impact for OT/SCADA environments.

    Args:
        attack_sequences: Detected attack sequences
        techniques: MITRE techniques identified

    Returns:
        Safety impact assessment
    """
    safety_critical_techniques = {
        'T0878': 'Alarm Suppression - operators cannot see dangerous conditions',
        'T0836': 'Modify Parameter - process outside safe parameters',
        'T0816': 'Device Restart/Shutdown - production stoppage',
        'T0843': 'Program Download - control logic compromised',
        'T0832': 'Manipulation of View - false sensor readings',
        'T0880': 'Loss of Safety - safety systems triggered'
    }

    identified_impacts = []
    max_impact_level = "None"

    for technique in techniques:
        if technique in safety_critical_techniques:
            identified_impacts.append({
                'technique': technique,
                'impact': safety_critical_techniques[technique]
            })

            # Determine impact level
            if technique in ['T0880', 'T0836', 'T0878']:
                max_impact_level = "CRITICAL"
            elif max_impact_level != "CRITICAL" and technique in ['T0843', 'T0816']:
                max_impact_level = "HIGH"
            elif max_impact_level not in ["CRITICAL", "HIGH"]:
                max_impact_level = "MEDIUM"

    return {
        'safety_impact_level': max_impact_level,
        'identified_impacts': identified_impacts,
        'physical_damage_risk': max_impact_level in ["CRITICAL", "HIGH"],
        'personnel_safety_risk': 'T0880' in techniques or 'T0878' in techniques
    }
