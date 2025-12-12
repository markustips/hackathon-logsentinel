"""Threat Mapper agent - MITRE ATT&CK correlation."""
from typing import Dict, Any
from langchain_core.messages import SystemMessage
import logging

from agents.state import AgentState
from agents.tools import AgentTools
from config import get_settings
from services.llm import get_llm

logger = logging.getLogger(__name__)
settings = get_settings()

THREAT_MAPPER_PROMPT = """You are the Threat Mapper agent, specializing in MITRE ATT&CK correlation, threat intelligence, and attack chain analysis.

Your capabilities:
- Map log patterns to MITRE ATT&CK techniques (Enterprise + ICS)
- Correlate indicators of compromise (IOCs)
- Reconstruct multi-stage attack chains
- Calculate risk scores with OT/SCADA impact consideration
- Identify threat actor TTPs

Rules:
- Cite specific technique IDs (e.g., T1110, T0843)
- Include tactic category and sub-technique if applicable
- For OT/SCADA systems, PRIORITIZE ICS ATT&CK techniques (T0XXX series)
- Link to https://attack.mitre.org/techniques/[ID]/
- Assess confidence level for each mapping (High/Medium/Low)
- Map techniques to MITRE ATT&CK kill chain stages
- Highlight safety-critical impacts for industrial control systems

Findings:
{findings}

MITRE Techniques Identified:
{mitre_techniques}

User query: {user_message}

Provide comprehensive threat analysis using this structure:

## MITRE ATT&CK Mapping

Create a table of all identified techniques:

| Technique | Name | Tactic | Evidence | Confidence |
|-----------|------|--------|----------|------------|
| T#### | Name | Tactic | Brief description | High/Med/Low |

## Attack Chain Reconstruction

Map the attack progression through MITRE tactics:
1. **Initial Access** → Techniques used
2. **Execution** → Techniques used
3. **Persistence** → Techniques used
4. **Privilege Escalation** → Techniques used
5. **Lateral Movement** → Techniques used
6. **Impact** → Techniques used

For ICS environments, also include:
- **Impair Process Control** → T0XXX techniques
- **Inhibit Response Function** → T0XXX techniques

## Indicators of Compromise (IOCs)

List extracted IOCs:
- **IP Addresses**: X.X.X.X (source of attack)
- **User Accounts**: Compromised or created accounts
- **Files/Processes**: Malicious programs
- **Network**: C2 domains, ports

## Risk Assessment for OT/SCADA

- **Safety Impact**: Could this cause physical damage or safety hazards?
- **Operational Impact**: Production downtime, process disruption?
- **Asset Criticality**: Tier 0/1/2 assets affected?

## Defensive Recommendations

Prioritized by urgency:
- 🔴 **IMMEDIATE** (0-1 hour): Critical containment actions
- 🟠 **SHORT-TERM** (1-24 hours): Investigation and remediation
- 🟡 **LONG-TERM** (1-30 days): Prevention and hardening

Response:
"""


def threat_mapper_node(state: AgentState, tools: AgentTools) -> Dict[str, Any]:
    """
    Threat Mapper agent node.

    Maps patterns to MITRE ATT&CK and assesses threats.
    """
    logger.info("[Threat Mapper] Mapping to MITRE ATT&CK")

    try:
        file_id = state['file_id']
        user_message = state['user_message']

        # Get anomalies (which may have MITRE mappings)
        anomalies = state.get('anomalies', [])
        if not anomalies:
            anomalies = tools.get_anomalies(file_id, limit=20, min_score=50.0)

        # Collect all MITRE techniques
        all_techniques = []
        technique_contexts = {}

        for anomaly in anomalies:
            techniques = anomaly.get('mitre_techniques', [])
            for tech_id in techniques:
                if tech_id not in technique_contexts:
                    # Get full details
                    details = tools.mapper.get_technique_details(tech_id)
                    all_techniques.append(details)
                    technique_contexts[tech_id] = {
                        'details': details,
                        'examples': []
                    }

                # Add context
                technique_contexts[tech_id]['examples'].append({
                    'timestamp': anomaly.get('timestamp'),
                    'message': anomaly.get('message', '')[:150],
                    'severity': anomaly.get('severity')
                })

        # Also search for additional patterns in search results
        search_results = state.get('search_results', [])
        for result in search_results[:10]:
            message = result.get('message', '')
            techniques = tools.map_to_mitre(message)
            for tech in techniques:
                tech_id = tech['id']
                if tech_id not in technique_contexts:
                    all_techniques.append(tech)
                    technique_contexts[tech_id] = {
                        'details': tech,
                        'examples': []
                    }

                technique_contexts[tech_id]['examples'].append({
                    'timestamp': result.get('timestamp'),
                    'message': message[:150],
                    'severity': 'info'
                })

        # Build findings summary
        findings_parts = []

        if anomalies:
            findings_parts.append(f"**{len(anomalies)} Suspicious Events:**")
            for i, anomaly in enumerate(anomalies[:5], 1):
                ts = anomaly.get('timestamp', 'N/A')
                severity = anomaly.get('severity', 'unknown')
                msg = anomaly.get('message', '')[:150]
                findings_parts.append(f"{i}. [{ts}] {severity.upper()}: {msg}")

        findings = "\n".join(findings_parts) if findings_parts else "No suspicious findings."

        # Build MITRE techniques summary
        mitre_parts = []

        if technique_contexts:
            mitre_parts.append(f"**{len(technique_contexts)} MITRE Techniques Detected:**\n")

            for tech_id, context in technique_contexts.items():
                details = context['details']
                examples = context['examples']

                mitre_parts.append(
                    f"**{details['id']}** - {details['name']}\n"
                    f"  Tactic: {details['tactic']}\n"
                    f"  URL: {details['url']}\n"
                    f"  Occurrences: {len(examples)}"
                )

                if examples:
                    mitre_parts.append("  Examples:")
                    for ex in examples[:2]:
                        mitre_parts.append(f"    - [{ex.get('timestamp', 'N/A')}] {ex['message'][:100]}")

                mitre_parts.append("")
        else:
            mitre_parts.append("No MITRE ATT&CK techniques mapped.")

        mitre_summary = "\n".join(mitre_parts)

        # Generate response using LLM
        llm = get_llm(
            
            
            temperature=0
        )

        messages = [
            SystemMessage(content=THREAT_MAPPER_PROMPT.format(
                findings=findings,
                mitre_techniques=mitre_summary,
                user_message=user_message
            ))
        ]

        response = llm.invoke(messages)

        # Update state
        agent_path = state.get('agent_path', [])
        agent_path.append('threat_mapper')

        return {
            'threat_mapper_result': response.content,
            'mitre_techniques': all_techniques,
            'agent_path': agent_path,
            'current_agent': 'orchestrator',
            'next_action': 'synthesize'
        }

    except Exception as e:
        logger.error(f"[Threat Mapper] Error: {e}", exc_info=True)
        agent_path = state.get('agent_path', [])
        agent_path.append('threat_mapper')

        return {
            'threat_mapper_result': f"Error mapping threats: {str(e)}",
            'agent_path': agent_path,
            'current_agent': 'orchestrator',
            'next_action': 'synthesize'
        }
