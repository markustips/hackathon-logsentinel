"""Log Analyst agent - semantic search and timeline analysis with ACTIVE attack chain tracing."""
from typing import Dict, Any
from langchain_core.messages import SystemMessage
import logging
import re

from agents.state import AgentState
from agents.tools import AgentTools
from config import get_settings
from services.llm import get_llm

logger = logging.getLogger(__name__)
settings = get_settings()

LOG_ANALYST_PROMPT = """You are the Log Analyst agent, specializing in semantic search, timeline analysis, and attack chain reconstruction.

Your capabilities:
- Semantic search over indexed log chunks
- Timeline analysis of events
- Context retrieval around specific events
- Attack progression tracking (before → during → after)

Rules:
- ALWAYS search logs before answering about log contents
- Reference specific timestamps and sources
- Quote relevant log snippets verbatim
- NEVER guess or make up log entries
- For authentication failures, ALWAYS check if the attack eventually succeeded
- Track full attack chains from initial access to impact
- Identify temporal clusters and patterns
- Be precise and factual

Available information:
{context}

User query: {user_message}

Provide a comprehensive analysis addressing the user's query. Include:

1. **Direct Answer** - What was found
2. **Attack Timeline** - Chronological progression with timestamps:
   - BEFORE: Baseline or normal state
   - DURING: Attack/anomaly events
   - AFTER: Consequences or follow-up actions
3. **Log Evidence** - Exact excerpts with timestamps
4. **Follow-up Findings** - Automatically investigate:
   - If auth failures detected → Check for successful logins afterward
   - If compromise detected → Check for privilege escalation, account creation, or lateral movement
   - If OT/SCADA event detected → Check for safety system impacts

Response:
"""


def log_analyst_node(state: AgentState, tools: AgentTools) -> Dict[str, Any]:
    """
    Log Analyst agent node with ACTIVE attack chain tracing.

    Performs semantic search, timeline analysis, AND automatically follows up on suspicious findings.
    """
    logger.info("[Log Analyst] Analyzing logs with active attack chain tracing")

    try:
        file_id = state['file_id']
        user_message = state['user_message']

        # Initial search
        search_results = tools.search_logs(file_id, user_message, k=15)

        # Get timeline
        timeline = tools.get_timeline(file_id)

        # CRITICAL: ACTIVE ATTACK CHAIN TRACING
        # Automatically investigate attack progression
        follow_up_results = {}

        if search_results:
            # Check for failed authentication attempts
            failed_logins = [r for r in search_results
                           if re.search(r'(failed|unsuccessful|invalid).*login|authentication.*fail',
                                      r.get('message', '').lower())]

            if failed_logins:
                logger.info("[Log Analyst] Detected failed logins - ACTIVELY tracing attack chain")

                # AUTOMATICALLY search for successful logins
                success_results = tools.search_logs(file_id, "successful login OR authentication success", k=20)
                follow_up_results['successful_logins'] = success_results

                # Extract IPs from failed logins and search for their activity
                ips_found = []
                for result in failed_logins:
                    ip_matches = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', result.get('message', ''))
                    ips_found.extend(ip_matches)

                # Search for activity from those IPs
                if ips_found:
                    unique_ips = list(set(ips_found))[:3]  # Top 3 IPs
                    for ip in unique_ips:
                        ip_activity = tools.search_by_ip(file_id, ip, limit=30)
                        follow_up_results[f'activity_from_{ip}'] = ip_activity

                # AUTOMATICALLY search for account creation
                account_results = tools.search_logs(file_id, "user created OR account created OR account added", k=20)
                follow_up_results['account_creation'] = account_results

                # AUTOMATICALLY search for privilege escalation
                priv_results = tools.search_logs(file_id, "privilege granted OR admin added OR sudo", k=20)
                follow_up_results['privilege_escalation'] = priv_results

            # Check for OT/SCADA-specific events
            ot_events = [r for r in search_results
                        if re.search(r'(plc|hmi|scada|alarm|setpoint|parameter|safety)',
                                   r.get('message', '').lower())]

            if ot_events:
                logger.info("[Log Analyst] Detected OT/SCADA events - tracing safety impact")

                # Search for safety-critical events
                safety_results = tools.search_logs(file_id, "alarm suppress OR safety override OR interlock bypass", k=20)
                follow_up_results['safety_events'] = safety_results

                # Search for parameter/setpoint changes
                param_results = tools.search_logs(file_id, "setpoint change OR parameter modify OR limit exceed", k=20)
                follow_up_results['parameter_changes'] = param_results

            # Check for compromise indicators and trace what happened AFTER
            compromise_events = [r for r in search_results
                               if re.search(r'(successful.*login|access.*granted)',
                                          r.get('message', '').lower())]

            if compromise_events and compromise_events[0].get('timestamp'):
                # Get events AFTER the first compromise
                first_timestamp = compromise_events[0]['timestamp']
                after_compromise = tools.get_events_after(file_id, first_timestamp, minutes=60)
                follow_up_results['post_compromise_activity'] = after_compromise

        # Build comprehensive context
        context_parts = []

        if search_results:
            context_parts.append("**Initial Search Results:**")
            for i, result in enumerate(search_results[:5], 1):
                ts = result.get('timestamp', 'N/A')
                level = result.get('log_level', 'INFO')
                msg = result['message'][:200]
                context_parts.append(f"{i}. [{ts}] [{level}] {msg}")

        # Add follow-up investigation results
        if follow_up_results:
            context_parts.append("\n**ACTIVE INVESTIGATION - Attack Chain Tracing:**")

            if 'successful_logins' in follow_up_results and follow_up_results['successful_logins']:
                context_parts.append(f"\n✓ Found {len(follow_up_results['successful_logins'])} successful logins AFTER failed attempts")
                for result in follow_up_results['successful_logins'][:3]:
                    ts = result.get('timestamp', 'N/A')
                    msg = result['message'][:150]
                    context_parts.append(f"  - [{ts}] {msg}")

            if 'account_creation' in follow_up_results and follow_up_results['account_creation']:
                context_parts.append(f"\n✓ Found {len(follow_up_results['account_creation'])} account creation events")
                for result in follow_up_results['account_creation'][:3]:
                    ts = result.get('timestamp', 'N/A')
                    msg = result['message'][:150]
                    context_parts.append(f"  - [{ts}] {msg}")

            if 'privilege_escalation' in follow_up_results and follow_up_results['privilege_escalation']:
                context_parts.append(f"\n✓ Found {len(follow_up_results['privilege_escalation'])} privilege escalation events")

            # IP-specific activity
            ip_keys = [k for k in follow_up_results.keys() if k.startswith('activity_from_')]
            for ip_key in ip_keys:
                ip = ip_key.replace('activity_from_', '')
                activity = follow_up_results[ip_key]
                if activity:
                    context_parts.append(f"\n✓ Activity from IP {ip}: {len(activity)} events")

            if 'post_compromise_activity' in follow_up_results and follow_up_results['post_compromise_activity']:
                context_parts.append(f"\n✓ Post-compromise: {len(follow_up_results['post_compromise_activity'])} events in following hour")

            if 'safety_events' in follow_up_results and follow_up_results['safety_events']:
                context_parts.append(f"\n⚠️ SAFETY CRITICAL: {len(follow_up_results['safety_events'])} safety system events detected")

            if 'parameter_changes' in follow_up_results and follow_up_results['parameter_changes']:
                context_parts.append(f"\n⚠️ PROCESS CONTROL: {len(follow_up_results['parameter_changes'])} parameter/setpoint modifications")

        if timeline:
            context_parts.append("\n**Timeline Overview:**")
            for event in timeline[:10]:
                ts = event.get('timestamp', 'N/A')
                total = event.get('total_events', 0)
                errors = event.get('error_count', 0)
                context_parts.append(f"- {ts}: {total} events ({errors} errors)")

        context = "\n".join(context_parts) if context_parts else "No relevant logs found."

        # Generate response using LLM
        llm = get_llm(temperature=0)

        messages = [
            SystemMessage(content=LOG_ANALYST_PROMPT.format(
                context=context,
                user_message=user_message
            ))
        ]

        response = llm.invoke(messages)

        # Extract referenced records
        referenced_records = [r['record_id'] for r in search_results[:5]]

        # Update state
        agent_path = state.get('agent_path', [])
        agent_path.append('log_analyst')

        return {
            'log_analyst_result': response.content,
            'search_results': search_results,
            'referenced_records': referenced_records,
            'agent_path': agent_path,
            'current_agent': 'orchestrator',
            'next_action': 'synthesize'
        }

    except Exception as e:
        logger.error(f"[Log Analyst] Error: {e}", exc_info=True)
        agent_path = state.get('agent_path', [])
        agent_path.append('log_analyst')

        return {
            'log_analyst_result': f"Error analyzing logs: {str(e)}",
            'agent_path': agent_path,
            'current_agent': 'orchestrator',
            'next_action': 'synthesize'
        }
