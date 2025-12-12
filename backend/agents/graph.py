"""LangGraph workflow for multi-agent system."""
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from sqlmodel import Session
import logging

from agents.state import AgentState
from agents.orchestrator import orchestrator_node
from agents.log_analyst import log_analyst_node
from agents.anomaly_hunter import anomaly_hunter_node
from agents.threat_mapper import threat_mapper_node
from agents.tools import AgentTools

logger = logging.getLogger(__name__)


def create_workflow(session: Session) -> StateGraph:
    """
    Create the multi-agent workflow graph.

    Args:
        session: Database session for tools

    Returns:
        Compiled LangGraph workflow
    """
    # Create tools
    tools = AgentTools(session)

    # Create workflow graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("log_analyst", lambda state: log_analyst_node(state, tools))
    workflow.add_node("anomaly_hunter", lambda state: anomaly_hunter_node(state, tools))
    workflow.add_node("threat_mapper", lambda state: threat_mapper_node(state, tools))

    # Define routing function
    def route_agent(state: AgentState) -> str:
        """Route to next agent based on current_agent."""
        current = state.get('current_agent', 'orchestrator')
        next_action = state.get('next_action', 'continue')

        logger.info(f"[Router] current_agent={current}, next_action={next_action}")

        if next_action == 'finish':
            return END

        if current == 'orchestrator':
            return END  # Orchestrator always returns final answer

        # After specialist agents, return to orchestrator
        if current in ['log_analyst', 'anomaly_hunter', 'threat_mapper']:
            return 'orchestrator'

        # For synthesize or error
        if current == 'synthesize':
            return END

        return END

    # Set entry point
    workflow.set_entry_point("orchestrator")

    # Add conditional edges from orchestrator
    def orchestrator_route(state: AgentState) -> Literal["log_analyst", "anomaly_hunter", "threat_mapper", "__end__"]:
        """Route from orchestrator to specialist agents."""
        current = state.get('current_agent', 'end')
        next_action = state.get('next_action', 'finish')

        logger.info(f"[Orchestrator Router] current={current}, action={next_action}")

        if next_action == 'finish' or current == 'error' or current == 'synthesize':
            return "__end__"

        if current in ['log_analyst', 'anomaly_hunter', 'threat_mapper']:
            return current

        return "__end__"

    workflow.add_conditional_edges(
        "orchestrator",
        orchestrator_route,
        {
            "log_analyst": "log_analyst",
            "anomaly_hunter": "anomaly_hunter",
            "threat_mapper": "threat_mapper",
            "__end__": END
        }
    )

    # Add edges back from specialist agents to orchestrator
    workflow.add_edge("log_analyst", "orchestrator")
    workflow.add_edge("anomaly_hunter", "orchestrator")
    workflow.add_edge("threat_mapper", "orchestrator")

    # Compile
    return workflow.compile()


async def run_copilot(
    file_id: str,
    user_message: str,
    conversation_history: list,
    session: Session
) -> Dict[str, Any]:
    """
    Run the copilot workflow.

    Args:
        file_id: File identifier
        user_message: User's question
        conversation_history: Previous conversation
        session: Database session

    Returns:
        Final response with metadata
    """
    logger.info(f"[Copilot] Starting workflow for query: {user_message[:100]}")

    try:
        # Create workflow
        app = create_workflow(session)

        # Initialize state
        initial_state: AgentState = {
            'file_id': file_id,
            'user_message': user_message,
            'conversation_history': conversation_history,
            'current_agent': None,
            'agent_path': [],
            'log_analyst_result': None,
            'anomaly_hunter_result': None,
            'threat_mapper_result': None,
            'search_results': [],
            'anomalies': [],
            'mitre_techniques': [],
            'referenced_records': [],
            # NEW: Attack chain analysis fields
            'attack_sequences': [],
            'severity_score': None,
            'risk_level': None,
            'attack_stage': None,
            'attack_succeeded': None,
            'safety_impact': None,
            # End state
            'final_answer': None,
            'metadata': {},
            'next_action': 'continue',
            'progress_callback': None
        }

        # Run workflow
        final_state = app.invoke(initial_state)

        # Extract final answer
        final_answer = final_state.get('final_answer', '')
        if not final_answer:
            # If no final answer, check agent results
            if final_state.get('log_analyst_result'):
                final_answer = final_state['log_analyst_result']
            elif final_state.get('anomaly_hunter_result'):
                final_answer = final_state['anomaly_hunter_result']
            elif final_state.get('threat_mapper_result'):
                final_answer = final_state['threat_mapper_result']
            else:
                final_answer = "I wasn't able to analyze the logs. Please try rephrasing your question."

        return {
            'message': final_answer,
            'agent': ', '.join(final_state.get('agent_path', [])),
            'references': final_state.get('referenced_records', [])[:10],
            'mitre_techniques': final_state.get('mitre_techniques', []),
            'metadata': final_state.get('metadata', {})
        }

    except Exception as e:
        logger.error(f"[Copilot] Workflow error: {e}", exc_info=True)
        return {
            'message': f"I encountered an error analyzing your query: {str(e)}",
            'agent': 'error',
            'references': [],
            'mitre_techniques': [],
            'metadata': {'error': str(e)}
        }


async def run_copilot_streaming(
    file_id: str,
    user_message: str,
    conversation_history: list,
    session: Session
):
    """
    Run the copilot workflow with streaming progress updates.

    Args:
        file_id: File identifier
        user_message: User's question
        conversation_history: Previous conversation
        session: Database session

    Yields:
        Progress events and final response
    """
    logger.info(f"[Copilot Streaming] Starting workflow for query: {user_message[:100]}")

    try:
        # Create workflow
        app = create_workflow(session)

        # Track progress events
        events = []

        def progress_callback(event: Dict[str, Any]):
            """Callback to capture progress events."""
            events.append(event)

        # Initialize state with progress callback
        initial_state: AgentState = {
            'file_id': file_id,
            'user_message': user_message,
            'conversation_history': conversation_history,
            'current_agent': None,
            'agent_path': [],
            'log_analyst_result': None,
            'anomaly_hunter_result': None,
            'threat_mapper_result': None,
            'search_results': [],
            'anomalies': [],
            'mitre_techniques': [],
            'referenced_records': [],
            # NEW: Attack chain analysis fields
            'attack_sequences': [],
            'severity_score': None,
            'risk_level': None,
            'attack_stage': None,
            'attack_succeeded': None,
            'safety_impact': None,
            # End state
            'final_answer': None,
            'metadata': {},
            'next_action': 'continue',
            'progress_callback': progress_callback
        }

        # Emit orchestrator routing step
        yield {
            'type': 'status',
            'step': 'orchestrator_routing',
            'agent': 'orchestrator',
            'message': 'Analyzing query intent and routing to specialist agents'
        }

        # Run workflow with streaming
        for step_output in app.stream(initial_state):
            logger.info(f"[Streaming] Step output: {list(step_output.keys())}")

            # Extract the node name and state
            for node_name, node_state in step_output.items():
                current_agent = node_state.get('current_agent')

                if current_agent and current_agent != 'error':
                    # Map agent names to progress steps
                    step_map = {
                        'log_analyst': 'log_analyst',
                        'anomaly_hunter': 'anomaly_hunter',
                        'threat_mapper': 'threat_mapper',
                        'synthesize': 'synthesizing_results'
                    }

                    # Detailed status messages showing what each agent does
                    message_map = {
                        'log_analyst': 'Loading semantic search model and searching log entries',
                        'anomaly_hunter': 'Running ML-based anomaly detection (Isolation Forest)',
                        'threat_mapper': 'Correlating patterns with MITRE ATT&CK framework',
                        'synthesize': 'Combining findings from all consulted agents'
                    }

                    step_name = step_map.get(current_agent, current_agent)
                    message = message_map.get(current_agent, f'{current_agent.replace("_", " ").title()} analyzing logs')

                    # Emit agent progress with detailed status
                    yield {
                        'type': 'status',
                        'step': step_name,
                        'agent': current_agent,
                        'message': message
                    }

        # Get final state
        final_state = list(app.stream(initial_state))[-1]
        final_node_state = list(final_state.values())[0]

        # Extract final answer
        final_answer = final_node_state.get('final_answer', '')
        if not final_answer:
            if final_node_state.get('log_analyst_result'):
                final_answer = final_node_state['log_analyst_result']
            elif final_node_state.get('anomaly_hunter_result'):
                final_answer = final_node_state['anomaly_hunter_result']
            elif final_node_state.get('threat_mapper_result'):
                final_answer = final_node_state['threat_mapper_result']
            else:
                final_answer = "I wasn't able to analyze the logs. Please try rephrasing your question."

        # Emit synthesizing step before final result
        yield {
            'type': 'status',
            'step': 'synthesizing_results',
            'agent': 'orchestrator',
            'message': 'Synthesizing findings from all agents'
        }

        # Emit final result
        yield {
            'type': 'result',
            'message': final_answer,
            'agent': ', '.join(final_node_state.get('agent_path', [])),
            'references': final_node_state.get('referenced_records', [])[:10],
            'mitre_techniques': final_node_state.get('mitre_techniques', []),
            'metadata': final_node_state.get('metadata', {})
        }

    except Exception as e:
        logger.error(f"[Copilot Streaming] Workflow error: {e}", exc_info=True)
        yield {
            'type': 'error',
            'message': f"I encountered an error analyzing your query: {str(e)}",
            'agent': 'error',
            'references': [],
            'mitre_techniques': [],
            'metadata': {'error': str(e)}
        }
