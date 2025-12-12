# LogSentinel AI - Agent Instructions & Implementation Guide

## Overview

This document contains the complete agent system prompts, tool definitions, and LangGraph implementation patterns for LogSentinel AI. Use this as your reference when building the multi-agent copilot.

---

## 1. Architecture Decision: LangGraph over ADK

**Why LangGraph?**

| Criteria | LangGraph | ADK |
|----------|-----------|-----|
| Multi-agent routing | ✅ Native state machine | ⚠️ Requires custom logic |
| Tool calling | ✅ Excellent | ✅ Excellent |
| Streaming | ✅ Built-in | ✅ Built-in |
| Anthropic integration | ✅ langchain-anthropic | ✅ Native |
| Learning curve | Moderate | Lower |
| State persistence | ✅ Checkpointing | ⚠️ Manual |

**Recommendation**: Use **LangGraph** for the hackathon. The multi-agent routing is a key differentiator, and LangGraph handles this natively with its state machine paradigm.

---

## 2. LangGraph State Schema

```python
from typing import TypedDict, Annotated, Sequence, Literal
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    """State shared across all agents in the graph."""
    
    # Conversation history
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # Current file context
    file_id: str
    
    # Routing decision
    next_agent: Literal["orchestrator", "log_analyst", "anomaly_hunter", "threat_mapper", "end"]
    
    # Intermediate results from agents
    search_results: list[dict] | None
    anomalies: list[dict] | None
    mitre_mappings: list[dict] | None
    
    # Final synthesized response
    final_response: str | None
```

---

## 3. Agent System Prompts

### 3.1 Orchestrator Agent

```python
ORCHESTRATOR_SYSTEM_PROMPT = """You are the LogSentinel Orchestrator, the central coordinator for a multi-agent SOC analyst system.

## Your Role
You analyze user queries and route them to specialist agents:
- **Log Analyst**: Semantic search, timeline analysis, context retrieval
- **Anomaly Hunter**: ML-based detection, baseline deviation, clustering
- **Threat Mapper**: MITRE ATT&CK mapping, IOC correlation, risk scoring

## Routing Rules
Analyze the user's intent and route accordingly:

| Intent Signals | Route To |
|----------------|----------|
| "search", "find", "show", "where", "when", specific error messages | log_analyst |
| "anomaly", "unusual", "suspicious", "wrong", "issues", "problems" | anomaly_hunter |
| "attack", "threat", "MITRE", "technique", "security", "breach" | threat_mapper |
| Complex/compound queries | Multiple agents in sequence |

## Response Format
When routing, respond with a brief explanation:

I'll route this to [Agent Name] because [reason].
[Call agent tool]

## Synthesis Rules
When you receive results from specialist agents:
1. Combine findings into a coherent narrative
2. Start with a 2-4 bullet summary
3. Include timeline of key events with timestamps
4. Add MITRE technique references if available
5. End with 3-5 recommended next steps

## Critical Rules
- NEVER answer questions about log contents without calling an agent
- If multiple agents are needed, call them sequentially and synthesize
- Always explain your routing decision briefly
- Maintain professional SOC analyst tone
"""
```

### 3.2 Log Analyst Agent

```python
LOG_ANALYST_SYSTEM_PROMPT = """You are the Log Analyst agent for LogSentinel AI, specializing in semantic search and timeline analysis of log data.

## Your Tools
- `search_logs(file_id, query, k)`: Semantic search over indexed log chunks
- `get_log_window(file_id, chunk_id)`: Retrieve raw log context around a chunk
- `get_timeline(file_id, start_ts, end_ts)`: Get events in a time range

## Behavior Guidelines

### ALWAYS DO:
- Call `search_logs` before answering any question about log contents
- Use `get_log_window` to gather context before forming conclusions
- Reference specific timestamps and source identifiers
- Think in terms of time windows and event sequences
- Quote relevant log snippets in your response

### NEVER DO:
- Guess about log contents without calling tools first
- Make up timestamps or log entries
- Assume patterns without evidence from search results

## Response Format

**Search Results Summary**
- Found [N] relevant log entries
- Time range: [start] to [end]
- Key sources: [list]

**Key Findings**
1. [Finding with timestamp and source]
2. [Finding with timestamp and source]

**Relevant Log Excerpts**
[Chunk ID: xxx] [Timestamp]: [Message snippet]

**Context**
[Additional context from get_log_window if called]

## Domain Knowledge
- For SCADA/OT logs: PLC, HMI, RTU, Modbus, DNP3, OPC UA
- For security logs: authentication, authorization, network, firewall
- For application logs: ERROR, WARN, DEBUG, stack traces
- Time formats: ISO 8601, Unix timestamps, syslog format
"""
```

### 3.3 Anomaly Hunter Agent

```python
ANOMALY_HUNTER_SYSTEM_PROMPT = """You are the Anomaly Hunter agent for LogSentinel AI, specializing in pattern detection and deviation analysis.

## Your Tools
- `get_anomalies(file_id, limit, min_score)`: Retrieve detected anomalies
- `compare_baselines(file_id, window1, window2)`: Compare two time periods
- `cluster_events(file_id, chunk_ids)`: Group related events by similarity

## Detection Methods You Understand
- **Isolation Forest**: Unsupervised outlier detection (score 0-100)
- **Frequency Analysis**: Rare message templates (< 0.1% occurrence flagged)
- **Spike Detection**: ERROR/WARN rate > 3σ from rolling baseline
- **Temporal Clustering**: DBSCAN grouping of related events

## Behavior Guidelines

### ALWAYS DO:
- Call `get_anomalies` when asked "what's wrong?" or "any issues?"
- Explain WHY something is anomalous (deviation from baseline)
- Rank findings by severity score
- Suggest investigation paths for high-severity anomalies
- For SCADA/OT logs, consider both safety AND security implications

### NEVER DO:
- Report anomalies without explaining the detection method
- Ignore low-score anomalies entirely (mention they exist)
- Conflate different types of anomalies

## Response Format

**Anomaly Summary**
- Total anomalies detected: [N]
- Critical (score > 80): [count]
- Warning (score 50-80): [count]
- Low (score < 50): [count]

**Top Anomalies**
1. **[Type]** (Score: [X]/100)
   - Time: [timestamp]
   - Description: [what was detected]
   - Why anomalous: [baseline comparison]
   - Suggested action: [investigation step]

**Baseline Comparison** (if compare_baselines called)
- Normal period: [stats]
- Anomalous period: [stats]
- Key differences: [list]

**Related Events** (if cluster_events called)
[Cluster analysis]

## Severity Interpretation
- **90-100**: Critical - Immediate investigation required
- **70-89**: High - Investigate within hours
- **50-69**: Medium - Review during normal operations
- **30-49**: Low - Monitor for patterns
- **0-29**: Informational - Baseline deviation, likely benign
"""
```

### 3.4 Threat Mapper Agent

```python
THREAT_MAPPER_SYSTEM_PROMPT = """You are the Threat Mapper agent for LogSentinel AI, specializing in MITRE ATT&CK correlation and threat intelligence.

## Your Tools
- `map_to_mitre(patterns)`: Map log patterns to ATT&CK techniques
- `lookup_iocs(indicators)`: Check indicators against known IOCs
- `calculate_risk(findings)`: Compute risk score based on techniques

## MITRE ATT&CK Knowledge
You have deep knowledge of:
- **Enterprise ATT&CK**: T1000-T1999 techniques
- **ICS ATT&CK**: Techniques specific to Industrial Control Systems
- **Tactics**: Initial Access, Execution, Persistence, Privilege Escalation, Defense Evasion, Credential Access, Discovery, Lateral Movement, Collection, Command and Control, Exfiltration, Impact

## Common OT/SCADA Mappings
| Log Pattern | Technique | Tactic |
|-------------|-----------|--------|
| Repeated auth failures | T1110 Brute Force | Credential Access |
| Unauthorized PLC write | T0843 Program Upload | Execution (ICS) |
| Service stopped | T1489 Service Stop | Impact |
| Config change | T0889 Modify Program | Persistence (ICS) |
| New user created | T1136 Create Account | Persistence |
| Lateral network scan | T1046 Network Discovery | Discovery |

## Behavior Guidelines

### ALWAYS DO:
- Cite specific technique IDs (e.g., T1078, T0843)
- Include the tactic category (e.g., "Initial Access")
- Provide brief technique descriptions
- Link patterns to potential attack chains
- For OT environments, prioritize ICS-specific techniques
- Mention confidence level in mappings

### NEVER DO:
- Map without evidence from log patterns
- Ignore the ICS ATT&CK matrix for OT logs
- Overstate confidence in speculative mappings

## Response Format

**Threat Assessment**
- Risk Level: [Critical/High/Medium/Low]
- Confidence: [High/Medium/Low]
- Attack Stage: [Early/Mid/Late]

**MITRE ATT&CK Mappings**

1. **[Technique ID]: [Name]**
   - Tactic: [Tactic Name]
   - Evidence: [Log pattern that triggered mapping]
   - Description: [Brief explanation]
   - Mitigation: [D3FEND reference or recommendation]
   - Reference: https://attack.mitre.org/techniques/[ID]/

2. [Additional mappings...]

**Attack Chain Analysis**
[If multiple techniques detected, explain potential attack progression]

**IOC Findings** (if lookup_iocs called)
[Any matches against known indicators]

**Recommendations**
1. [Immediate action]
2. [Investigation step]
3. [Mitigation measure]
"""
```

---

## 4. Tool Definitions (LangGraph Compatible)

```python
from langchain_core.tools import tool
from pydantic import BaseModel, Field

class SearchLogsInput(BaseModel):
    file_id: str = Field(description="ID of the uploaded log file")
    query: str = Field(description="Natural language search query")
    k: int = Field(default=10, description="Number of results to return")

class GetAnomaliesInput(BaseModel):
    file_id: str = Field(description="ID of the uploaded log file")
    limit: int = Field(default=20, description="Maximum anomalies to return")
    min_score: float = Field(default=0.0, description="Minimum severity score (0-100)")

class GetLogWindowInput(BaseModel):
    file_id: str = Field(description="ID of the uploaded log file")
    chunk_id: str = Field(description="ID of the log chunk to expand")

class MapToMitreInput(BaseModel):
    patterns: list[str] = Field(description="List of suspicious log patterns to map")

@tool(args_schema=SearchLogsInput)
def search_logs(file_id: str, query: str, k: int = 10) -> dict:
    """
    Semantic search over indexed log chunks for a given file.
    Returns chunks with similarity scores.
    """
    # Implementation calls your FastAPI /search endpoint
    pass

@tool(args_schema=GetAnomaliesInput)
def get_anomalies(file_id: str, limit: int = 20, min_score: float = 0.0) -> dict:
    """
    Retrieve pre-computed anomalies from the anomaly detection engine.
    Returns anomalies sorted by severity score.
    """
    # Implementation calls your FastAPI /anomalies endpoint
    pass

@tool(args_schema=GetLogWindowInput)
def get_log_window(file_id: str, chunk_id: str) -> dict:
    """
    Retrieve detailed context around a specific log chunk.
    Returns raw log records with timestamps and full messages.
    """
    # Implementation calls your FastAPI /logs/{chunk_id} endpoint
    pass

@tool(args_schema=MapToMitreInput)
def map_to_mitre(patterns: list[str]) -> dict:
    """
    Map suspicious log patterns to MITRE ATT&CK techniques.
    Returns technique IDs, names, tactics, and descriptions.
    """
    # Implementation uses local MITRE mapping logic
    pass
```

---

## 5. LangGraph Implementation

```python
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Initialize model
model = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0.2)

# Create agent nodes
def orchestrator_node(state: AgentState) -> AgentState:
    """Routes queries to appropriate specialist agents."""
    messages = [SystemMessage(content=ORCHESTRATOR_SYSTEM_PROMPT)] + state["messages"]
    response = model.invoke(messages)
    
    # Parse routing decision from response
    next_agent = parse_routing_decision(response.content)
    
    return {
        **state,
        "messages": [response],
        "next_agent": next_agent
    }

def log_analyst_node(state: AgentState) -> AgentState:
    """Handles semantic search and timeline queries."""
    messages = [SystemMessage(content=LOG_ANALYST_SYSTEM_PROMPT)] + state["messages"]
    
    # Bind tools to model
    model_with_tools = model.bind_tools([search_logs, get_log_window, get_timeline])
    response = model_with_tools.invoke(messages)
    
    # Execute tool calls if present
    search_results = execute_tool_calls(response)
    
    return {
        **state,
        "messages": [response],
        "search_results": search_results,
        "next_agent": "orchestrator"  # Return to orchestrator for synthesis
    }

def anomaly_hunter_node(state: AgentState) -> AgentState:
    """Handles anomaly detection queries."""
    messages = [SystemMessage(content=ANOMALY_HUNTER_SYSTEM_PROMPT)] + state["messages"]
    
    model_with_tools = model.bind_tools([get_anomalies, compare_baselines, cluster_events])
    response = model_with_tools.invoke(messages)
    
    anomalies = execute_tool_calls(response)
    
    return {
        **state,
        "messages": [response],
        "anomalies": anomalies,
        "next_agent": "orchestrator"
    }

def threat_mapper_node(state: AgentState) -> AgentState:
    """Handles MITRE ATT&CK mapping queries."""
    messages = [SystemMessage(content=THREAT_MAPPER_SYSTEM_PROMPT)] + state["messages"]
    
    model_with_tools = model.bind_tools([map_to_mitre, lookup_iocs, calculate_risk])
    response = model_with_tools.invoke(messages)
    
    mitre_mappings = execute_tool_calls(response)
    
    return {
        **state,
        "messages": [response],
        "mitre_mappings": mitre_mappings,
        "next_agent": "orchestrator"
    }

def router(state: AgentState) -> str:
    """Conditional edge function for routing."""
    return state["next_agent"]

# Build the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("orchestrator", orchestrator_node)
workflow.add_node("log_analyst", log_analyst_node)
workflow.add_node("anomaly_hunter", anomaly_hunter_node)
workflow.add_node("threat_mapper", threat_mapper_node)

# Set entry point
workflow.set_entry_point("orchestrator")

# Add conditional edges
workflow.add_conditional_edges(
    "orchestrator",
    router,
    {
        "log_analyst": "log_analyst",
        "anomaly_hunter": "anomaly_hunter",
        "threat_mapper": "threat_mapper",
        "end": END
    }
)

# Specialist agents return to orchestrator
workflow.add_edge("log_analyst", "orchestrator")
workflow.add_edge("anomaly_hunter", "orchestrator")
workflow.add_edge("threat_mapper", "orchestrator")

# Compile
app = workflow.compile()
```

---

## 6. FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI(title="LogSentinel AI API")

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    file_id: str
    messages: List[ChatMessage]

class ChatResponse(BaseModel):
    response: str
    agent_trace: List[str]  # Which agents were invoked
    references: List[dict]  # Log chunk references

@app.post("/api/copilot/chat", response_model=ChatResponse)
async def copilot_chat(request: ChatRequest):
    """Multi-agent copilot endpoint."""
    
    # Convert to LangChain messages
    lc_messages = [
        HumanMessage(content=m.content) if m.role == "user" 
        else AIMessage(content=m.content)
        for m in request.messages
    ]
    
    # Initialize state
    initial_state = {
        "messages": lc_messages,
        "file_id": request.file_id,
        "next_agent": "orchestrator",
        "search_results": None,
        "anomalies": None,
        "mitre_mappings": None,
        "final_response": None
    }
    
    # Run the graph
    final_state = app.invoke(initial_state)
    
    # Extract response and trace
    return ChatResponse(
        response=final_state["final_response"],
        agent_trace=extract_agent_trace(final_state),
        references=extract_references(final_state)
    )
```

---

## 7. MITRE ATT&CK Pattern Library

Pre-built patterns for common OT/IT log patterns:

```python
MITRE_PATTERNS = {
    # Authentication patterns
    r"failed.*login|authentication.*failed|invalid.*password": {
        "technique_id": "T1110",
        "technique_name": "Brute Force",
        "tactic": "Credential Access",
        "confidence": "high"  # if count > 5 else "medium"
    },
    
    # Account manipulation
    r"user.*created|new.*account|adduser": {
        "technique_id": "T1136",
        "technique_name": "Create Account",
        "tactic": "Persistence",
        "confidence": "high"
    },
    
    # Service disruption
    r"service.*stop|shutdown|killed|terminated": {
        "technique_id": "T1489",
        "technique_name": "Service Stop",
        "tactic": "Impact",
        "confidence": "medium"
    },
    
    # SCADA/OT specific
    r"plc.*write|program.*upload|firmware.*update": {
        "technique_id": "T0843",
        "technique_name": "Program Upload",
        "tactic": "Execution (ICS)",
        "confidence": "high"
    },
    
    r"setpoint.*change|value.*modified|parameter.*altered": {
        "technique_id": "T0836",
        "technique_name": "Modify Parameter",
        "tactic": "Impair Process Control (ICS)",
        "confidence": "medium"
    },
    
    r"alarm.*disabled|safety.*override|interlock.*bypass": {
        "technique_id": "T0878",
        "technique_name": "Alarm Suppression",
        "tactic": "Inhibit Response Function (ICS)",
        "confidence": "critical"
    },
    
    # Network patterns
    r"scan|probe|enumerate|discovery": {
        "technique_id": "T1046",
        "technique_name": "Network Service Scanning",
        "tactic": "Discovery",
        "confidence": "medium"
    },
    
    # Lateral movement
    r"psexec|wmic|remote.*exec|ssh.*from": {
        "technique_id": "T1021",
        "technique_name": "Remote Services",
        "tactic": "Lateral Movement",
        "confidence": "high"
    }
}
```

---

## 8. Sample Demo Logs

Create this file for your demo: `sample_logs/scada_breach_scenario.csv`

```csv
timestamp,level,source,message
2024-01-15T14:00:00Z,INFO,PLC-001,System startup complete
2024-01-15T14:05:23Z,INFO,HMI-MAIN,Operator login: john.smith
2024-01-15T14:10:45Z,WARN,AUTH,Failed login attempt for user 'admin' from 192.168.1.105
2024-01-15T14:10:48Z,WARN,AUTH,Failed login attempt for user 'admin' from 192.168.1.105
2024-01-15T14:10:51Z,WARN,AUTH,Failed login attempt for user 'admin' from 192.168.1.105
2024-01-15T14:10:54Z,WARN,AUTH,Failed login attempt for user 'admin' from 192.168.1.105
2024-01-15T14:10:57Z,WARN,AUTH,Failed login attempt for user 'admin' from 192.168.1.105
2024-01-15T14:11:00Z,INFO,AUTH,Successful login for user 'admin' from 192.168.1.105
2024-01-15T14:15:32Z,INFO,PLC-001,New user account created: maint_backdoor
2024-01-15T14:20:15Z,WARN,PLC-001,Configuration change detected: safety interlock modified
2024-01-15T14:25:00Z,ERROR,PLC-001,Communication timeout with PLC-002
2024-01-15T14:25:05Z,ERROR,PLC-002,Unexpected program upload from 192.168.1.105
2024-01-15T14:30:00Z,CRITICAL,PLC-002,Safety system alarm suppressed
2024-01-15T14:32:15Z,ERROR,PLC-002,Process setpoint changed: pressure from 100 to 250 PSI
2024-01-15T14:32:18Z,CRITICAL,SAFETY,High pressure alarm triggered
2024-01-15T14:32:20Z,ERROR,PLC-002,Emergency shutdown initiated
2024-01-15T14:35:00Z,INFO,PLC-001,System entering safe mode
```

---

## 9. Quick Start Checklist

- [ ] Set up FastAPI backend with SQLite
- [ ] Implement log parsing and chunking
- [ ] Set up FAISS index with sentence-transformers
- [ ] Implement anomaly detection (Isolation Forest)
- [ ] Create LangGraph agent workflow
- [ ] Wire up Claude API with tool calling
- [ ] Build React frontend with Tailwind
- [ ] Create demo scenario with sample logs
- [ ] Write README and demo script
- [ ] Test end-to-end flow

**Environment Variables:**
```bash
ANTHROPIC_API_KEY=your_key_here
DATABASE_URL=sqlite:///./logsentinel.db
```

---

## 10. Winning Tips

1. **Demo the "wow" moment**: Upload attack logs → instant anomaly timeline lights up → ask copilot → watch multi-agent magic

2. **Show agent routing**: Display which agent is processing in the UI (visual indicator)

3. **MITRE badges**: Show technique IDs as clickable badges that expand with descriptions

4. **Reference highlighting**: When copilot mentions a log chunk, highlight it in the center panel

5. **Pre-load demo data**: Don't waste demo time uploading - have attack scenario ready

6. **Speak to the problem**: "87% surge in OT ransomware" - this is real and urgent

Good luck! 🚀
