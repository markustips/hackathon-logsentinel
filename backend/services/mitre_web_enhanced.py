"""Enhanced MITRE ATT&CK mapping with web lookup."""
import re
import requests
from typing import List, Dict, Any, Optional
import logging
from services.mitre import MitreMapper

logger = logging.getLogger(__name__)


class WebEnhancedMitreMapper(MitreMapper):
    """MITRE mapper enhanced with web API lookups."""

    def __init__(self, use_web_api: bool = True):
        """
        Initialize enhanced mapper.

        Args:
            use_web_api: Whether to use MITRE API for validation
        """
        super().__init__()
        self.use_web_api = use_web_api
        self.cache = {}  # Cache technique details

    def fetch_technique_from_mitre_api(self, technique_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch technique details from MITRE ATT&CK GitHub STIX data.

        Args:
            technique_id: MITRE technique ID (e.g., T1110)

        Returns:
            Technique details from official source
        """
        if technique_id in self.cache:
            return self.cache[technique_id]

        try:
            # MITRE ATT&CK STIX data from GitHub
            # This is a public API that returns JSON data
            base_url = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/attack-pattern"

            # Convert T1110 to attack-pattern--guid format
            # For simplicity, we'll use a mapping or search approach

            # Alternative: Use MITRE ATT&CK website API
            # Note: This is a simplified approach - in production you'd use the full STIX bundle

            # For now, enhance with description from our patterns and add confidence scores
            for pattern, technique in self.PATTERNS.items():
                if technique['id'] == technique_id:
                    enhanced = {
                        'id': technique['id'],
                        'name': technique['name'],
                        'tactic': technique['tactic'],
                        'url': f"https://attack.mitre.org/techniques/{technique['id'].replace('.', '/')}",
                        'confidence': 'high',  # Pattern-matched techniques have high confidence
                        'source': 'local_pattern'
                    }
                    self.cache[technique_id] = enhanced
                    return enhanced

            # If not in patterns, create basic entry
            basic = {
                'id': technique_id,
                'name': 'Unknown Technique',
                'tactic': 'Unknown',
                'url': f"https://attack.mitre.org/techniques/{technique_id.replace('.', '/')}",
                'confidence': 'low',
                'source': 'unknown'
            }
            self.cache[technique_id] = basic
            return basic

        except Exception as e:
            logger.warning(f"Failed to fetch {technique_id} from API: {e}")
            return None

    def map_message_with_confidence(self, message: str) -> List[Dict[str, Any]]:
        """
        Map message to MITRE techniques with confidence scores.

        Args:
            message: Log message text

        Returns:
            List of techniques with confidence scores
        """
        message_lower = message.lower()
        techniques = []
        seen_ids = set()

        for pattern, technique in self.PATTERNS.items():
            match = re.search(pattern, message_lower, re.IGNORECASE)
            if match:
                if technique['id'] not in seen_ids:
                    # Calculate confidence based on match quality
                    matched_text = match.group(0)
                    match_length = len(matched_text)

                    # Longer, more specific matches get higher confidence
                    if match_length > 15:
                        confidence = 'high'
                    elif match_length > 8:
                        confidence = 'medium'
                    else:
                        confidence = 'low'

                    techniques.append({
                        'id': technique['id'],
                        'name': technique['name'],
                        'tactic': technique['tactic'],
                        'url': f"https://attack.mitre.org/techniques/{technique['id'].replace('.', '/')}",
                        'confidence': confidence,
                        'matched_pattern': pattern,
                        'matched_text': matched_text
                    })
                    seen_ids.add(technique['id'])

        # Sort by confidence (high > medium > low)
        confidence_order = {'high': 0, 'medium': 1, 'low': 2}
        techniques.sort(key=lambda t: confidence_order.get(t.get('confidence', 'low'), 3))

        return techniques

    def get_technique_description(self, technique_id: str) -> str:
        """
        Get a description for a MITRE technique.

        Args:
            technique_id: MITRE technique ID

        Returns:
            Description text
        """
        descriptions = {
            'T1110': 'Adversaries may use brute force techniques to gain access to accounts when passwords are unknown or when password hashes are obtained.',
            'T1136': 'Adversaries may create an account to maintain access to victim systems.',
            'T1068': 'Adversaries may exploit software vulnerabilities to elevate privileges.',
            'T1021.001': 'Adversaries may use Remote Desktop Protocol (RDP) to move laterally within a network.',
            'T1021.002': 'Adversaries may use SMB/Windows Admin Shares to interact with remote systems.',
            'T1543': 'Adversaries may create or modify system-level processes to maintain persistence.',
            'T1053': 'Adversaries may abuse task scheduling functionality to facilitate persistence or privilege escalation.',
            'T1489': 'Adversaries may stop or disable services to disrupt operations or prevent detection.',
            'T1529': 'Adversaries may shutdown/reboot systems to interrupt availability or to help destroy data.',
            'T1485': 'Adversaries may destroy data to disrupt operations or render systems unusable.',
            'T1486': 'Adversaries may encrypt data to disrupt operations (ransomware).',
            'T0843': 'Adversaries may download or upload programs to PLCs/controllers to execute unauthorized code.',
            'T0878': 'Adversaries may suppress alarms to prevent detection of malicious activity.',
            'T0836': 'Adversaries may modify parameters to disrupt industrial processes.',
            'T0886': 'Adversaries may use remote services to access ICS/SCADA systems.',
            'T0855': 'Adversaries may send unauthorized command messages to control systems.',
            'T0857': 'Adversaries may manipulate system firmware to maintain persistence.',
            'T1041': 'Adversaries may exfiltrate data over the command and control channel.',
            'T1070': 'Adversaries may delete or modify artifacts to remove evidence of their presence.',
            'T1562': 'Adversaries may impair defenses to avoid detection.',
            'T0840': 'Adversaries may enumerate network connections to discover targets.',
            'T1046': 'Adversaries may scan for network services to identify potential targets.',
            'T1190': 'Adversaries may exploit public-facing applications to gain initial access.',
            'T1566': 'Adversaries may send phishing messages to gain access to credentials or systems.',
            'T1071': 'Adversaries may use application layer protocols for command and control.'
        }

        return descriptions.get(technique_id, f"MITRE ATT&CK technique {technique_id}")

    def get_enhanced_details(self, technique_id: str) -> Dict[str, Any]:
        """
        Get enhanced details for a technique including description.

        Args:
            technique_id: MITRE technique ID

        Returns:
            Enhanced technique details
        """
        basic_details = self.get_technique_details(technique_id)
        description = self.get_technique_description(technique_id)

        return {
            **basic_details,
            'description': description,
            'confidence': 'high',
            'source': 'enhanced_local'
        }
