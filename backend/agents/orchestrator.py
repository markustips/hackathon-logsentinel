"""Orchestrator agent - routes queries to specialist agents."""
from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
import logging

from agents.state import AgentState
from config import get_settings
from services.llm import get_llm

logger = logging.getLogger(__name__)
settings = get_settings()

ORCHESTRATOR_PROMPT = """You are the LogSentinel Orchestrator, the central coordinator for a multi-agent SOC analyst system.

Your role: Analyze user queries and route them to specialist agents:
- **log_analyst**: Semantic search, timeline analysis, context retrieval. Use for: "search", "find", "show", "where", "when", "what happened"
- **anomaly_hunter**: ML-based detection, baseline deviation, clustering. Use for: "anomaly", "unusual", "suspicious", "wrong", "strange", "outlier"
- **threat_mapper**: MITRE ATT&CK mapping, IOC correlation, risk scoring. Use for: "attack", "threat", "MITRE", "technique", "malicious"

Routing rules:
| Intent Signals | Route To |
|----------------|----------|
| "search", "find", "show", "where", "when", "what" | log_analyst |
| "anomaly", "unusual", "suspicious", "wrong", "strange" | anomaly_hunter |
| "attack", "threat", "MITRE", "technique", "tactic" | threat_mapper |
| Complex queries (multiple intents) | Multiple agents in sequence |

Response format:
1. Determine which agent(s) to call based on the user query
2. Return ONLY ONE of: "log_analyst", "anomaly_hunter", "threat_mapper", or "synthesize"
3. Use "synthesize" if agents have already run and you need to combine their results

Current conversation:
{conversation_history}

User query: {user_message}

Agents already consulted: {agent_path}

Which agent should handle this query next? Respond with ONLY the agent name or "synthesize".
"""

SYNTHESIS_PROMPT = """You are the LogSentinel Orchestrator synthesizing results from specialist SOC analysts into a comprehensive security report.

User query: {user_message}

Attack Chain Analysis:
{attack_chain_summary}

Agent Results:
{agent_results}

Provide a professional, comprehensive SOC analyst report using this EXACT structure:

# 🔍 Executive Summary

Provide 2-4 concise bullet points answering:
- What happened?
- What was the impact or risk?
- What stage is the attack at?
- What's the recommended immediate action?

---

# ⚠️ Threat Assessment

| Metric | Value |
|--------|-------|
| **Risk Level** | 🔴 CRITICAL / 🟠 HIGH / 🟡 MEDIUM / 🟢 LOW |
| **Severity Score** | X/100 |
| **Confidence** | High / Medium / Low |
| **Attack Stage** | [Initial Access / Execution / Persistence / Lateral Movement / Impact] |
| **Environment Type** | [IT / OT/SCADA / Hybrid] |

---

# 📅 Attack Timeline

Present ALL significant events in a chronological table (use EXACT format):

| Time | Severity | Event | MITRE |
|------|----------|-------|-------|
| HH:MM:SS | 🟡 WARN / 🔴 CRITICAL / ⚫ EMERGENCY | Event description | T#### |
| HH:MM:SS | 🟡 WARN / 🔴 CRITICAL / ⚫ EMERGENCY | Event description | T#### |

**Attack Duration**: X minutes from first to last event
**Attack Outcome**: {attack_succeeded_text}

---

# 🎯 MITRE ATT&CK Techniques

| Technique | Name | Tactic | Evidence Count | Severity |
|-----------|------|--------|----------------|----------|
| T#### | Technique Name | Tactic Category | X occurrences | CRITICAL/HIGH/MEDIUM |

**For ICS/OT environments**, highlight ICS-specific techniques (T0XXX):
- T0843 - Program Download
- T0836 - Modify Parameter
- T0878 - Alarm Suppression

---

# 🚨 Indicators of Compromise (IOCs)

**Network Indicators:**
- Source IP: X.X.X.X
- Destination Ports: XXXX
- Protocols: XXX

**Host Indicators:**
- Compromised Accounts: username1, username2
- Created Accounts: backdoor_user
- Suspicious Processes: process.exe

**Behavioral Indicators:**
- Failed login attempts: X
- Privilege escalation events: X
- Configuration changes: X

---

# 💡 Recommended Actions

## 🔴 IMMEDIATE (0-1 hour)
1. **Contain**: Specific containment steps
2. **Isolate**: Network segmentation actions
3. **Disable**: Account lockouts

## 🟠 SHORT-TERM (1-24 hours)
4. **Investigate**: Forensic analysis tasks
5. **Remediate**: System restoration steps
6. **Verify**: Integrity checks

## 🟡 LONG-TERM (1-30 days)
7. **Harden**: Security improvements
8. **Monitor**: Enhanced detection rules
9. **Train**: User awareness updates

---

# 📊 Impact Analysis

**For OT/SCADA systems**, assess:
- **Safety Impact**: Physical damage risk, personnel safety
- **Operational Impact**: Production downtime, process disruption
- **Compliance Impact**: Regulatory violations, reporting requirements
- **Financial Impact**: Estimated costs, business interruption

---

**CRITICAL FORMATTING RULES:**
- Use markdown tables for structured data
- Include specific timestamps (HH:MM:SS format)
- Reference exact log record IDs when available
- Use severity emojis (🔴 🟠 🟡 🟢)
- For MITRE techniques, format as: **T####** - Name (Tactic)
- Always include clickable URLs: https://attack.mitre.org/techniques/T####/

Synthesized response:
"""


def orchestrator_node(state: AgentState) -> Dict[str, Any]:
    """
    Orchestrator agent node.

    Analyzes query and routes to appropriate specialist agent.
    """
    logger.info("[Orchestrator] Routing user query")

    try:
        # Check if we need to synthesize results
        agent_path = state.get('agent_path', [])

        # If multiple agents have run, synthesize
        if len(agent_path) >= 2 or state.get('next_action') == 'synthesize':
            return synthesize_results(state)

        # Determine next agent
        llm = get_llm(temperature=0)

        # Build conversation history string
        history_str = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in state.get('conversation_history', [])[-5:]  # Last 5 messages
        ])

        # Get routing decision
        messages = [
            SystemMessage(content=ORCHESTRATOR_PROMPT.format(
                conversation_history=history_str,
                user_message=state['user_message'],
                agent_path=", ".join(agent_path) if agent_path else "None"
            ))
        ]

        response = llm.invoke(messages)
        next_agent = response.content.strip().lower()

        logger.info(f"[Orchestrator] Routing to: {next_agent}")

        # Validate routing
        valid_agents = ['log_analyst', 'anomaly_hunter', 'threat_mapper', 'synthesize']
        if next_agent not in valid_agents:
            # Default to log_analyst for unclear queries
            next_agent = 'log_analyst'

        return {
            'current_agent': next_agent,
            'next_action': 'continue'
        }

    except Exception as e:
        logger.error(f"[Orchestrator] Error: {e}", exc_info=True)
        return {
            'current_agent': 'error',
            'final_answer': f"I encountered an error routing your query: {str(e)}",
            'next_action': 'finish'
        }


def synthesize_results(state: AgentState) -> Dict[str, Any]:
    """Synthesize results from multiple agents with attack chain analysis."""
    logger.info("[Orchestrator] Synthesizing results with attack chain data")

    try:
        llm = get_llm(temperature=0)

        # Build attack chain summary (THE WINNING FEATURE!)
        attack_chain_parts = []

        attack_sequences = state.get('attack_sequences', [])
        severity_score = state.get('severity_score', 0)
        risk_level = state.get('risk_level', 'UNKNOWN')
        attack_stage = state.get('attack_stage', 'Unknown')
        attack_succeeded = state.get('attack_succeeded', False)
        safety_impact = state.get('safety_impact', {})

        if attack_sequences:
            attack_chain_parts.append(f"**🚨 CRITICAL: {len(attack_sequences)} Attack Sequences Detected!**\n")
            attack_chain_parts.append(f"Overall Severity Score: **{severity_score}/100**")
            attack_chain_parts.append(f"Risk Level: **{risk_level}**")
            attack_chain_parts.append(f"Attack Stage: **{attack_stage}**")
            attack_chain_parts.append(f"Attack Succeeded: **{'YES - BREACH CONFIRMED' if attack_succeeded else 'NO - Attack blocked/failed'}**\n")

            for i, seq in enumerate(attack_sequences[:3], 1):
                attack_chain_parts.append(
                    f"{i}. **{seq['name'].replace('_', ' ').title()}**\n"
                    f"   - Severity: {seq['severity']}/100\n"
                    f"   - Stage: {seq['attack_stage']}\n"
                    f"   - Assessment: {seq['assessment']}\n"
                    f"   - MITRE Techniques: {', '.join(seq['mitre_techniques'])}\n"
                    f"   - Time Span: {seq['time_span_minutes']:.1f} minutes\n"
                    f"   - Events: {len(seq['events'])}"
                )

        if safety_impact and safety_impact.get('identified_impacts'):
            attack_chain_parts.append(f"\n⚠️ **OT/SCADA SAFETY IMPACT:**")
            attack_chain_parts.append(f"- Safety Impact Level: {safety_impact['safety_impact_level']}")
            attack_chain_parts.append(f"- Physical Damage Risk: {'YES' if safety_impact.get('physical_damage_risk') else 'NO'}")
            attack_chain_parts.append(f"- Personnel Safety Risk: {'YES' if safety_impact.get('personnel_safety_risk') else 'NO'}")

        attack_chain_summary = "\n".join(attack_chain_parts) if attack_chain_parts else "No attack chains detected."

        # Build agent results summary
        results_parts = []

        if state.get('log_analyst_result'):
            results_parts.append(f"**Log Analyst:**\n{state['log_analyst_result']}")

        if state.get('anomaly_hunter_result'):
            results_parts.append(f"**Anomaly Hunter:**\n{state['anomaly_hunter_result']}")

        if state.get('threat_mapper_result'):
            results_parts.append(f"**Threat Mapper:**\n{state['threat_mapper_result']}")

        agent_results = "\n\n".join(results_parts) if results_parts else "No results from agents."

        # Synthesize
        messages = [
            SystemMessage(content=SYNTHESIS_PROMPT.format(
                user_message=state['user_message'],
                attack_chain_summary=attack_chain_summary,
                agent_results=agent_results,
                attack_succeeded_text="Attack SUCCEEDED - Breach confirmed" if attack_succeeded else "Attack BLOCKED or FAILED"
            ))
        ]

        response = llm.invoke(messages)

        return {
            'final_answer': response.content,
            'next_action': 'finish',
            'severity_score': severity_score,
            'risk_level': risk_level,
            'attack_stage': attack_stage,
            'attack_succeeded': attack_succeeded,
            'metadata': {
                'agents_consulted': state.get('agent_path', []),
                'techniques_found': len(state.get('mitre_techniques', [])),
                'anomalies_found': len(state.get('anomalies', [])),
                'attack_sequences_detected': len(attack_sequences),
                'severity_score': severity_score,
                'risk_level': risk_level,
                'attack_stage': attack_stage
            }
        }

    except Exception as e:
        logger.error(f"[Orchestrator] Synthesis error: {e}", exc_info=True)
        return {
            'final_answer': f"Error synthesizing results: {str(e)}",
            'next_action': 'finish'
        }
