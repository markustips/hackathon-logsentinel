"""MITRE ATT&CK mapping service."""
import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class MitreMapper:
    """Map log patterns to MITRE ATT&CK techniques."""

    # Pattern mappings for enterprise and ICS techniques
    PATTERNS = {
        # Authentication & Access
        r"(failed|unsuccessful|invalid).*login": {
            "id": "T1110",
            "name": "Brute Force",
            "tactic": "Credential Access"
        },
        r"authentication.*fail": {
            "id": "T1110",
            "name": "Brute Force",
            "tactic": "Credential Access"
        },
        r"(successful|accepted).*login": {
            "id": "T1078",
            "name": "Valid Accounts",
            "tactic": "Initial Access"
        },
        r"(user|account).*(created|added|new)": {
            "id": "T1136",
            "name": "Create Account",
            "tactic": "Persistence"
        },
        r"backdoor.*(account|user)": {
            "id": "T1136",
            "name": "Create Account",
            "tactic": "Persistence"
        },
        r"privilege.*escalat": {
            "id": "T1068",
            "name": "Exploitation for Privilege Escalation",
            "tactic": "Privilege Escalation"
        },

        # Lateral Movement
        r"(rdp|remote desktop).*connect": {
            "id": "T1021.001",
            "name": "Remote Desktop Protocol",
            "tactic": "Lateral Movement"
        },
        r"(smb|cifs|samba).*access": {
            "id": "T1021.002",
            "name": "SMB/Windows Admin Shares",
            "tactic": "Lateral Movement"
        },

        # Persistence
        r"(service|daemon).*(created|installed|added)": {
            "id": "T1543",
            "name": "Create or Modify System Process",
            "tactic": "Persistence"
        },
        r"scheduled.*task.*created": {
            "id": "T1053",
            "name": "Scheduled Task/Job",
            "tactic": "Persistence"
        },

        # Impact
        r"(service|process).*(stop|kill|terminate)": {
            "id": "T1489",
            "name": "Service Stop",
            "tactic": "Impact"
        },
        r"(shutdown|reboot|restart)": {
            "id": "T1529",
            "name": "System Shutdown/Reboot",
            "tactic": "Impact"
        },
        r"(delete|remove|wipe).*file": {
            "id": "T1485",
            "name": "Data Destruction",
            "tactic": "Impact"
        },
        r"encrypt.*file": {
            "id": "T1486",
            "name": "Data Encrypted for Impact",
            "tactic": "Impact"
        },

        # ICS/OT Specific Techniques
        r"plc.*(write|program|upload|download)": {
            "id": "T0843",
            "name": "Program Download",
            "tactic": "Execution (ICS)"
        },
        r"(ladder|logic).*modif": {
            "id": "T0843",
            "name": "Program Download",
            "tactic": "Execution (ICS)"
        },
        r"(alarm|alert).*(disable|suppress|silence|mute)": {
            "id": "T0878",
            "name": "Alarm Suppression",
            "tactic": "Inhibit Response Function (ICS)"
        },
        r"(setpoint|parameter).*(change|modif|alter|force)": {
            "id": "T0836",
            "name": "Modify Parameter",
            "tactic": "Impair Process Control (ICS)"
        },
        r"(safety|interlock).*(bypass|override|disable)": {
            "id": "T0878",
            "name": "Alarm Suppression",
            "tactic": "Inhibit Response Function (ICS)"
        },
        r"(scada|hmi|dcs).*(access|login|connect)": {
            "id": "T0886",
            "name": "Remote Services",
            "tactic": "Lateral Movement (ICS)"
        },
        r"(controller|plc|rtu).*(command|control)": {
            "id": "T0855",
            "name": "Unauthorized Command Message",
            "tactic": "Impair Process Control (ICS)"
        },
        r"firmware.*(upload|download|modif|flash)": {
            "id": "T0857",
            "name": "System Firmware",
            "tactic": "Inhibit Response Function (ICS)"
        },
        # Additional ICS Attack Patterns
        r"(pressure|temperature|flow|level).*(exceed|critical|dangerous|overflow|limit)": {
            "id": "T0836",
            "name": "Modify Parameter",
            "tactic": "Impair Process Control (ICS)"
        },
        r"(reactor|turbine|generator|pump|valve).*(shutdown|stop|fail|trip)": {
            "id": "T0816",
            "name": "Device Restart/Shutdown",
            "tactic": "Impact (ICS)"
        },
        r"(manual|auto).*(mode|control).*switch": {
            "id": "T0838",
            "name": "Modify Control Logic",
            "tactic": "Impair Process Control (ICS)"
        },
        r"(historian|data.*log).*(modif|tamper|delete)": {
            "id": "T0870",
            "name": "Detect Program State",
            "tactic": "Discovery (ICS)"
        },
        r"(engineering.*station|workstation).*(access|compromise)": {
            "id": "T0883",
            "name": "Internet Accessible Device",
            "tactic": "Initial Access (ICS)"
        },
        r"(default.*credential|default.*password)": {
            "id": "T0812",
            "name": "Default Credentials",
            "tactic": "Initial Access (ICS)"
        },
        r"(modbus|dnp3|iec.*104|profinet|opcua).*(inject|manipulate|spoof)": {
            "id": "T0855",
            "name": "Unauthorized Command Message",
            "tactic": "Impair Process Control (ICS)"
        },
        r"(emergency.*shutdown|e-?stop|scram).*(fail|block|disable)": {
            "id": "T0816",
            "name": "Device Restart/Shutdown",
            "tactic": "Impact (ICS)"
        },
        r"(sensor|transducer|transmitter).*(spoof|manipulate|false)": {
            "id": "T0832",
            "name": "Manipulation of View",
            "tactic": "Impact (ICS)"
        },
        r"(hmi.*screen|operator.*display).*(modify|manipulate|fake)": {
            "id": "T0832",
            "name": "Manipulation of View",
            "tactic": "Impact (ICS)"
        },

        # Exfiltration
        r"(data|file|document).*(transfer|exfil|upload|send)": {
            "id": "T1041",
            "name": "Exfiltration Over C2 Channel",
            "tactic": "Exfiltration"
        },

        # Defense Evasion
        r"(log|audit).*(clear|delete|wipe|disable)": {
            "id": "T1070",
            "name": "Indicator Removal",
            "tactic": "Defense Evasion"
        },
        r"(antivirus|firewall|security).*(disable|stop|bypass)": {
            "id": "T1562",
            "name": "Impair Defenses",
            "tactic": "Defense Evasion"
        },

        # Discovery
        r"(scan|enumerate|discover|reconnaissance)": {
            "id": "T0840",
            "name": "Network Connection Enumeration",
            "tactic": "Discovery (ICS)"
        },
        r"(network|port).*scan": {
            "id": "T1046",
            "name": "Network Service Scanning",
            "tactic": "Discovery"
        },

        # Initial Access
        r"(exploit|vulnerability|cve-)": {
            "id": "T1190",
            "name": "Exploit Public-Facing Application",
            "tactic": "Initial Access"
        },
        r"phish.*email": {
            "id": "T1566",
            "name": "Phishing",
            "tactic": "Initial Access"
        },

        # Command and Control
        r"(c2|command.*control|beacon|callback)": {
            "id": "T1071",
            "name": "Application Layer Protocol",
            "tactic": "Command and Control"
        },
    }

    def map_message(self, message: str) -> List[Dict[str, str]]:
        """
        Map a log message to MITRE ATT&CK techniques.

        Args:
            message: Log message text

        Returns:
            List of matched MITRE techniques
        """
        message_lower = message.lower()
        techniques = []
        seen_ids = set()

        for pattern, technique in self.PATTERNS.items():
            if re.search(pattern, message_lower, re.IGNORECASE):
                if technique['id'] not in seen_ids:
                    techniques.append({
                        'id': technique['id'],
                        'name': technique['name'],
                        'tactic': technique['tactic'],
                        'url': f"https://attack.mitre.org/techniques/{technique['id'].replace('.', '/')}/"
                    })
                    seen_ids.add(technique['id'])

        return techniques

    def map_anomalies(self, anomalies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Map anomaly descriptions to MITRE techniques.

        Args:
            anomalies: List of anomaly detections

        Returns:
            Anomalies enriched with MITRE techniques
        """
        enriched = []

        for anomaly in anomalies:
            # Try to map based on message or description
            message = anomaly.get('message', '') + ' ' + anomaly.get('description', '')
            techniques = self.map_message(message)

            enriched_anomaly = anomaly.copy()
            enriched_anomaly['mitre_techniques'] = [t['id'] for t in techniques]
            enriched_anomaly['mitre_details'] = techniques

            enriched.append(enriched_anomaly)

        return enriched

    def get_technique_details(self, technique_id: str) -> Dict[str, str]:
        """
        Get details for a specific MITRE technique.

        Args:
            technique_id: MITRE technique ID (e.g., T1110)

        Returns:
            Technique details
        """
        for pattern, technique in self.PATTERNS.items():
            if technique['id'] == technique_id:
                return {
                    'id': technique['id'],
                    'name': technique['name'],
                    'tactic': technique['tactic'],
                    'url': f"https://attack.mitre.org/techniques/{technique['id'].replace('.', '/')}/"
                }

        return {
            'id': technique_id,
            'name': 'Unknown',
            'tactic': 'Unknown',
            'url': f"https://attack.mitre.org/techniques/{technique_id.replace('.', '/')}/"
        }
