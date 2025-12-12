"""Anomaly Hunter agent - ML-based anomaly detection with attack sequence analysis."""
from typing import Dict, Any
from langchain_core.messages import SystemMessage
import logging

from agents.state import AgentState
from agents.tools import AgentTools
from config import get_settings
from services.llm import get_llm
from services.attack_chain import detect_attack_sequences, calculate_severity_score, determine_attack_stage, assess_ot_safety_impact, calculate_risk_level

logger = logging.getLogger(__name__)
settings = get_settings()

ANOMALY_HUNTER_PROMPT = """You are the Anomaly Hunter agent, specializing in pattern detection, anomaly analysis, and risk assessment.

Your capabilities:
- ML-based anomaly detection (Isolation Forest, frequency analysis, spike detection)
- Baseline deviation analysis
- Pattern clustering and correlation
- Statistical significance testing
- Risk severity scoring

Rules:
- Explain WHY something is anomalous with specific metrics (e.g., "3.5σ deviation from baseline")
- Rank findings by severity score (0-100) and confidence level
- For SCADA/OT systems, consider BOTH safety AND security implications
- Distinguish between benign anomalies and potential threats
- Quantify risk: Calculate overall risk score based on severity, frequency, and impact
- Identify temporal clustering (e.g., "5 events in 12 seconds indicates automated attack")

Detected Anomalies:
{anomalies}

User query: {user_message}

Provide comprehensive analysis including:

1. **Overall Risk Assessment**
   - Risk Level: 🔴 CRITICAL | 🟠 HIGH | 🟡 MEDIUM | 🟢 LOW
   - Risk Score: X/100
   - Confidence: High/Medium/Low
   - Attack Stage: Initial Access | Execution | Persistence | Impact

2. **Anomaly Summary** - Ranked by severity
   - Count by severity (CRITICAL: X, HIGH: X, MEDIUM: X, LOW: X)
   - Temporal patterns identified
   - Statistical deviation metrics

3. **Detailed Findings** - For top anomalies, explain:
   - WHY it's anomalous (specific deviation)
   - Baseline comparison
   - Potential impact (especially for OT/SCADA)
   - Confidence level

4. **Clustering Analysis**
   - Related events grouped together
   - Attack chain indicators

Response:
"""


def anomaly_hunter_node(state: AgentState, tools: AgentTools) -> Dict[str, Any]:
    """
    Anomaly Hunter agent node with ATTACK SEQUENCE DETECTION.

    Detects and analyzes anomalous patterns AND correlates them into attack chains.
    """
    logger.info("[Anomaly Hunter] Detecting anomalies and attack sequences")

    try:
        file_id = state['file_id']
        user_message = state['user_message']

        # Get anomalies
        anomalies = tools.get_anomalies(file_id, limit=20, min_score=40.0)

        # CRITICAL: Get ALL events chronologically for attack chain analysis
        all_events = tools.get_all_events_chronological(file_id, limit=1000)

        # WINNING FEATURE: Detect attack sequences
        attack_sequences = detect_attack_sequences(all_events)

        # Calculate severity score based on attack chains
        all_techniques = []
        for anomaly in anomalies:
            all_techniques.extend(anomaly.get('mitre_techniques', []))

        severity_score = calculate_severity_score(
            attack_sequences=[
                type('AttackSeq', (), {
                    'name': seq.name,
                    'severity': seq.severity,
                    'mitre_techniques': seq.mitre_techniques
                })() for seq in attack_sequences
            ],
            techniques=all_techniques,
            is_ot_environment=True
        )

        # Determine attack stage
        attack_stage = determine_attack_stage(
            attack_sequences=[
                type('AttackSeq', (), {
                    'attack_stage': seq.attack_stage,
                    'severity': seq.severity
                })() for seq in attack_sequences
            ],
            techniques=all_techniques
        )

        # Calculate risk level
        risk_level = calculate_risk_level(severity_score)

        # Assess safety impact for OT
        safety_impact = assess_ot_safety_impact(
            attack_sequences=[
                type('AttackSeq', (), {
                    'mitre_techniques': seq.mitre_techniques
                })() for seq in attack_sequences
            ],
            techniques=all_techniques
        )

        # Check if attack succeeded
        attack_succeeded = any(
            seq.name in ['brute_force_success', 'persistence_established', 'complete_ot_breach']
            for seq in attack_sequences
        )

        logger.info(f"[Anomaly Hunter] Detected {len(attack_sequences)} attack sequences, severity: {severity_score}/100, stage: {attack_stage}")

        # Build comprehensive summary including attack sequences
        anomaly_parts = []

        # Add attack sequence summary FIRST (most important!)
        if attack_sequences:
            anomaly_parts.append(f"**🚨 ATTACK SEQUENCES DETECTED: {len(attack_sequences)}**\n")
            anomaly_parts.append(f"**Overall Severity: {severity_score}/100 ({risk_level})**")
            anomaly_parts.append(f"**Attack Stage: {attack_stage}**")
            anomaly_parts.append(f"**Attack Succeeded: {'YES' if attack_succeeded else 'NO'}**\n")

            for i, seq in enumerate(attack_sequences[:5], 1):
                anomaly_parts.append(
                    f"{i}. **{seq.name.replace('_', ' ').title()}** (Severity: {seq.severity}/100)\n"
                    f"   Stage: {seq.attack_stage}\n"
                    f"   Assessment: {seq.assessment}\n"
                    f"   MITRE Techniques: {', '.join(seq.mitre_techniques)}\n"
                    f"   Events in chain: {len(seq.events)}\n"
                    f"   Time span: {seq.time_span_minutes:.1f} minutes"
                )

        if safety_impact and safety_impact.get('identified_impacts'):
            anomaly_parts.append(f"\n⚠️ **SAFETY IMPACT ANALYSIS (OT/SCADA):**")
            anomaly_parts.append(f"Safety Impact Level: {safety_impact['safety_impact_level']}")
            anomaly_parts.append(f"Physical Damage Risk: {'YES' if safety_impact['physical_damage_risk'] else 'NO'}")
            anomaly_parts.append(f"Personnel Safety Risk: {'YES' if safety_impact['personnel_safety_risk'] else 'NO'}\n")

            for impact in safety_impact['identified_impacts']:
                anomaly_parts.append(f"  - {impact['technique']}: {impact['impact']}")

        if anomalies:
            anomaly_parts.append(f"\n**ML-Detected Anomalies: {len(anomalies)}**\n")

            for i, anomaly in enumerate(anomalies[:10], 1):
                ts = anomaly.get('timestamp', 'N/A')
                severity = anomaly.get('severity', 'unknown')
                score = anomaly.get('score', 0)
                atype = anomaly.get('anomaly_type', 'unknown')
                desc = anomaly.get('description', '')
                msg = anomaly.get('message', '')[:150]

                anomaly_parts.append(
                    f"{i}. [{ts}] **{severity.upper()}** (score: {score:.1f})\n"
                    f"   Type: {atype}\n"
                    f"   {desc}\n"
                    f"   Message: {msg}"
                )
        else:
            if not attack_sequences:
                anomaly_parts.append("No significant anomalies or attack patterns detected in the logs.")

        anomaly_context = "\n\n".join(anomaly_parts)

        # Generate response using LLM
        llm = get_llm(
            
            
            temperature=0
        )

        messages = [
            SystemMessage(content=ANOMALY_HUNTER_PROMPT.format(
                anomalies=anomaly_context,
                user_message=user_message
            ))
        ]

        response = llm.invoke(messages)

        # Extract referenced records
        referenced_records = [a['record_id'] for a in anomalies[:10]]

        # Update state with attack chain analysis
        agent_path = state.get('agent_path', [])
        agent_path.append('anomaly_hunter')

        # Convert attack sequences to dicts for state
        attack_seq_dicts = [
            {
                'name': seq.name,
                'events': seq.events,
                'severity': seq.severity,
                'mitre_techniques': seq.mitre_techniques,
                'assessment': seq.assessment,
                'attack_stage': seq.attack_stage,
                'time_span_minutes': seq.time_span_minutes
            }
            for seq in attack_sequences
        ]

        return {
            'anomaly_hunter_result': response.content,
            'anomalies': anomalies,
            'attack_sequences': attack_seq_dicts,  # NEW!
            'severity_score': severity_score,  # NEW!
            'risk_level': risk_level,  # NEW!
            'attack_stage': attack_stage,  # NEW!
            'attack_succeeded': attack_succeeded,  # NEW!
            'safety_impact': safety_impact,  # NEW!
            'referenced_records': state.get('referenced_records', []) + referenced_records,
            'agent_path': agent_path,
            'current_agent': 'orchestrator',
            'next_action': 'synthesize'
        }

    except Exception as e:
        logger.error(f"[Anomaly Hunter] Error: {e}", exc_info=True)
        agent_path = state.get('agent_path', [])
        agent_path.append('anomaly_hunter')

        return {
            'anomaly_hunter_result': f"Error detecting anomalies: {str(e)}",
            'agent_path': agent_path,
            'current_agent': 'orchestrator',
            'next_action': 'synthesize'
        }
