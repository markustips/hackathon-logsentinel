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

SYNTHESIS_PROMPT = """You are the LogSentinel Orchestrator synthesizing results from specialist agents.

User query: {user_message}

Agent Results:
{agent_results}

Provide a comprehensive answer following this structure:
1. **Summary** (2-4 bullet points of key findings)
2. **Timeline** (if available, list chronological events with timestamps)
3. **MITRE Techniques** (if available, list technique IDs with names)
4. **Recommendations** (3-5 specific next steps)

CRITICAL: Reference specific log records by timestamp when available.
Format MITRE techniques as: T#### - Name (Tactic)

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
    """Synthesize results from multiple agents."""
    logger.info("[Orchestrator] Synthesizing results")

    try:
        llm = get_llm(temperature=0)

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
                agent_results=agent_results
            ))
        ]

        response = llm.invoke(messages)

        return {
            'final_answer': response.content,
            'next_action': 'finish',
            'metadata': {
                'agents_consulted': state.get('agent_path', []),
                'techniques_found': len(state.get('mitre_techniques', [])),
                'anomalies_found': len(state.get('anomalies', []))
            }
        }

    except Exception as e:
        logger.error(f"[Orchestrator] Synthesis error: {e}", exc_info=True)
        return {
            'final_answer': f"Error synthesizing results: {str(e)}",
            'next_action': 'finish'
        }
