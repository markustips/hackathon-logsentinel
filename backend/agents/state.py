"""LangGraph state schema for multi-agent system."""
from typing import List, Dict, Any, Optional, Annotated
from typing_extensions import TypedDict
import operator


class AgentState(TypedDict):
    """State shared across all agents in the workflow."""

    # User input
    file_id: str
    user_message: str
    conversation_history: List[Dict[str, str]]

    # Agent routing
    current_agent: Optional[str]
    agent_path: List[str]  # Track which agents have been invoked

    # Agent outputs
    log_analyst_result: Optional[str]
    anomaly_hunter_result: Optional[str]
    threat_mapper_result: Optional[str]

    # Data retrieved
    search_results: List[Dict[str, Any]]
    anomalies: List[Dict[str, Any]]
    mitre_techniques: List[Dict[str, str]]
    referenced_records: List[str]

    # Attack chain analysis (NEW - the winning feature!)
    attack_sequences: List[Dict[str, Any]]  # Detected attack patterns
    severity_score: Optional[int]  # 0-100 calculated severity
    risk_level: Optional[str]  # LOW, MEDIUM, HIGH, CRITICAL
    attack_stage: Optional[str]  # Initial, Mid-Stage, Late-Stage, Impact
    attack_succeeded: Optional[bool]  # Did the attack succeed?
    safety_impact: Optional[Dict[str, Any]]  # OT/SCADA safety assessment

    # Final output
    final_answer: Optional[str]
    metadata: Dict[str, Any]

    # Control
    next_action: Optional[str]  # continue, finish, error

    # Progress tracking (for streaming updates)
    progress_callback: Optional[Any]  # Callable to emit progress updates
