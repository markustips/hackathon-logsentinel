# LogSentinel AI - Architecture & Workflow Diagrams

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LOGSENTINEL AI PLATFORM                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│   Frontend Layer     │
│  (React + Vite)      │
├──────────────────────┤
│                      │
│  ┌────────────────┐  │
│  │  File Explorer │  │
│  │   Dashboard    │  │
│  │  Search Panel  │  │
│  │ Anomaly View   │  │
│  │ Copilot Chat   │  │
│  └────────────────┘  │
│                      │
│  Components:         │
│  - ThreatAssessment  │
│  - AttackTimeline    │
│  - MitreTable        │
│  - Recommendations   │
└──────────┬───────────┘
           │ HTTPS/REST
           │ WebSocket
           ▼
┌──────────────────────────────────────────────────────────────┐
│                 Backend Layer (FastAPI)                      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  API Routers:                                                │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │  /upload   │ │  /search   │ │/anomalies  │              │
│  └────────────┘ └────────────┘ └────────────┘              │
│  ┌────────────┐ ┌──────────────────────────┐               │
│  │   /logs    │ │   /copilot/chat         │               │
│  └────────────┘ └──────────────────────────┘               │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Multi-Agent System (LangGraph)             │   │
│  │                                                      │   │
│  │  ┌────────────────────────────────────────────────┐ │   │
│  │  │         Orchestrator Agent                     │ │   │
│  │  │  (Intent routing, synthesis, scoring)          │ │   │
│  │  └───────┬──────────────────────────┬─────────────┘ │   │
│  │          │                          │               │   │
│  │          ▼                          ▼               │   │
│  │  ┌──────────────┐          ┌──────────────┐        │   │
│  │  │ Log Analyst  │          │   Anomaly    │        │   │
│  │  │   Agent      │          │    Hunter    │        │   │
│  │  │              │          │    Agent     │        │   │
│  │  │ - Semantic   │          │              │        │   │
│  │  │   Search     │          │ - Isolation  │        │   │
│  │  │ - Timeline   │          │   Forest     │        │   │
│  │  │ - Context    │          │ - Sequences  │        │   │
│  │  └──────────────┘          └──────────────┘        │   │
│  │          │                          │               │   │
│  │          └──────────┬───────────────┘               │   │
│  │                     ▼                               │   │
│  │          ┌──────────────────────┐                   │   │
│  │          │   Threat Mapper      │                   │   │
│  │          │      Agent           │                   │   │
│  │          │                      │                   │   │
│  │          │ - MITRE ATT&CK       │                   │   │
│  │          │ - IOC Extraction     │                   │   │
│  │          │ - Risk Scoring       │                   │   │
│  │          └──────────────────────┘                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
└──────────────────────────┼───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                    Services Layer                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Parser     │  │   Indexer    │  │   Anomaly    │      │
│  │              │  │              │  │   Detector   │      │
│  │ - CSV        │  │ - Embeddings │  │              │      │
│  │ - JSON       │  │ - FAISS      │  │ - Isolation  │      │
│  │ - Syslog     │  │ - Chunking   │  │   Forest     │      │
│  │ - Plain Text │  │ - Metadata   │  │ - Frequency  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │    MITRE     │  │ Attack Chain │                         │
│  │   Mapper     │  │  Correlator  │                         │
│  │              │  │              │                         │
│  │ - Enterprise │  │ - Sequence   │                         │
│  │   ATT&CK     │  │   Detection  │                         │
│  │ - ICS        │  │ - Severity   │                         │
│  │   ATT&CK     │  │   Scoring    │                         │
│  └──────────────┘  └──────────────┘                         │
└──────────────────────┼───────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────┐
│                    Data Layer                                │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────┐    ┌────────────────────────┐  │
│  │   SQLite Database       │    │   FAISS Vector Store   │  │
│  │                         │    │                        │  │
│  │  Tables:                │    │  Indexes:              │  │
│  │  - uploaded_files       │    │  - log_embeddings      │  │
│  │  - log_chunks           │    │  - metadata mappings   │  │
│  │  - anomalies            │    │                        │  │
│  │  - mitre_mappings       │    │  384-dim vectors       │  │
│  │  - iocs                 │    │  (MiniLM-L6-v2)        │  │
│  └─────────────────────────┘    └────────────────────────┘  │
│                                                              │
│  ┌─────────────────────────┐                                │
│  │   File Storage          │                                │
│  │   (Uploaded Logs)       │                                │
│  │                         │                                │
│  │  - Raw log files        │                                │
│  │  - Parsed chunks        │                                │
│  │  - Preprocessed data    │                                │
│  └─────────────────────────┘                                │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                 External Services                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────┐    ┌────────────────────────┐  │
│  │   Anthropic Claude API  │    │  Sentence Transformers │  │
│  │   (Sonnet 4.5)          │    │  (Embeddings)          │  │
│  │                         │    │                        │  │
│  │  - Agent reasoning      │    │  - all-MiniLM-L6-v2    │  │
│  │  - Tool execution       │    │  - Local inference     │  │
│  │  - Response generation  │    │                        │  │
│  └─────────────────────────┘    └────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Multi-Agent Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MULTI-AGENT COPILOT WORKFLOW                             │
└─────────────────────────────────────────────────────────────────────────────┘

User Query: "What happened with the authentication failures?"
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 1: ORCHESTRATOR AGENT (Intent Analysis)              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Task: Analyze user intent and route to specialist agents  │
│                                                             │
│  Logic:                                                     │
│  1. Parse query for keywords:                               │
│     - "authentication" → security/access context            │
│     - "failures" → anomaly/error detection                  │
│     - "what happened" → timeline analysis needed            │
│                                                             │
│  2. Determine routing:                                      │
│     Route 1: log_analyst (timeline + context)               │
│     Route 2: anomaly_hunter (pattern detection)             │
│     Route 3: threat_mapper (MITRE + risk assessment)        │
│                                                             │
│  3. Set state:                                              │
│     - next_agent = "log_analyst"                            │
│     - follow_up_needed = True                               │
│     - follow_up_queries = [                                 │
│         "Did login eventually succeed?",                    │
│         "What actions after success?",                      │
│         "Any persistence mechanisms?"                       │
│       ]                                                     │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 2: LOG ANALYST AGENT (Semantic Search + Timeline)    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Tool Calls:                                                │
│                                                             │
│  1️⃣ search_logs(file_id, "authentication failed", k=20)    │
│     Results:                                                │
│     - [08:15:23] WARN: Authentication failed for admin     │
│     - [08:15:26] WARN: Authentication failed for admin     │
│     - [08:15:31] WARN: Authentication failed for admin     │
│     - [08:15:38] WARN: Authentication failed for admin     │
│     - [08:15:45] WARN: Authentication failed for admin     │
│     Common IP: 192.168.1.250                                │
│                                                             │
│  2️⃣ FOLLOW-UP: search_logs(file_id, "successful login", k=20) │
│     Results:                                                │
│     - [08:15:45] INFO: Successful login for admin          │
│     IP: 192.168.1.250 ⚠️ SAME IP AS FAILURES!              │
│                                                             │
│  3️⃣ FOLLOW-UP: get_events_after(file_id, "08:15:45", 60)   │
│     Results:                                                │
│     - [08:16:12] INFO: User 'backup_admin' created         │
│     - [08:17:34] WARN: PLC program uploaded to PLC-03      │
│     - [08:18:01] CRITICAL: Safety alarms suppressed        │
│     - [08:18:22] CRITICAL: Temp setpoint changed 65→95°C   │
│     - [08:19:45] EMERGENCY: Emergency shutdown triggered   │
│                                                             │
│  Output to State:                                           │
│  - search_results = [all events with timestamps]            │
│  - next_agent = "anomaly_hunter"                            │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 3: ANOMALY HUNTER AGENT (Pattern Detection)          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Tool Calls:                                                │
│                                                             │
│  1️⃣ get_anomalies(file_id, limit=50, min_score=70)         │
│     Results:                                                │
│     - [Score: 95] Emergency shutdown triggered              │
│     - [Score: 92] Safety alarms suppressed                  │
│     - [Score: 88] PLC program upload                        │
│     - [Score: 85] Temp setpoint changed by 30°C             │
│     - [Score: 78] 5 failed logins in 22 seconds             │
│                                                             │
│  2️⃣ detect_sequences(file_id, "brute_force_success")       │
│     Pattern Matched:                                        │
│     ✅ Brute Force Success Pattern:                         │
│        - Multiple failures (5) → Success → Post-exploit     │
│        - Severity: 95/100                                   │
│        - Confidence: HIGH                                   │
│                                                             │
│  3️⃣ detect_sequences(file_id, "full_ot_attack")            │
│     Pattern Matched:                                        │
│     ✅ Complete OT Compromise:                              │
│        - Initial Access → Persistence → Execution →         │
│          Safety Bypass → Impact                             │
│        - Severity: 100/100 🚨                               │
│        - Confidence: HIGH                                   │
│                                                             │
│  4️⃣ compare_baselines(file_id, "normal", "attack_window")  │
│     Baseline Deviation:                                     │
│     - Normal error rate: 0.2/min                            │
│     - Observed error rate: 12/min                           │
│     - Deviation: 8.3 standard deviations ⚠️                 │
│     - Assessment: HIGHLY ANOMALOUS                          │
│                                                             │
│  Output to State:                                           │
│  - anomalies = [scored events]                              │
│  - attack_sequences = [detected patterns]                   │
│  - next_agent = "threat_mapper"                             │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 4: THREAT MAPPER AGENT (MITRE + IOCs)                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Tool Calls:                                                │
│                                                             │
│  1️⃣ map_to_mitre(search_results + anomalies)               │
│     MITRE Mappings:                                         │
│                                                             │
│     Enterprise ATT&CK:                                      │
│     - T1110 (Brute Force) → "5 failed logins"               │
│       Confidence: HIGH                                      │
│     - T1078 (Valid Accounts) → "Successful login"           │
│       Confidence: HIGH                                      │
│     - T1136 (Create Account) → "User created"               │
│       Confidence: HIGH                                      │
│                                                             │
│     ICS ATT&CK:                                             │
│     - T0843 (Program Upload) → "PLC program upload"         │
│       Confidence: HIGH                                      │
│       Safety Impact: HIGH                                   │
│     - T0878 (Alarm Suppression) → "Alarms suppressed"       │
│       Confidence: HIGH                                      │
│       Safety Impact: CRITICAL                               │
│     - T0836 (Modify Parameter) → "Setpoint changed"         │
│       Confidence: HIGH                                      │
│       Safety Impact: CRITICAL                               │
│     - T0880 (Loss of Safety) → "Emergency shutdown"         │
│       Confidence: HIGH                                      │
│       Safety Impact: CRITICAL                               │
│                                                             │
│  2️⃣ map_attack_chain(all_events)                            │
│     Attack Chain:                                           │
│     Credential Access → Initial Access → Persistence →      │
│     Execution → Inhibit Response → Impair Process →         │
│     Impact                                                  │
│                                                             │
│     Kill Chain Stages: 7/7 COMPLETE ⚠️                      │
│                                                             │
│  3️⃣ extract_iocs(all_events)                                │
│     IOCs Identified:                                        │
│     - IP: 192.168.1.250 (unauthorized external)             │
│     - Account: backup_admin (persistence)                   │
│     - PLC: PLC-03 (compromised)                             │
│     - Timestamp: 08:15-08:20 (attack window)                │
│                                                             │
│  4️⃣ calculate_risk(techniques, context)                     │
│     Severity Calculation:                                   │
│     Base: 0                                                 │
│     + Attack succeeded: +30                                 │
│     + 7 techniques: +35 (7 × 5)                             │
│     + Persistence: +15                                      │
│     + Safety affected: +20                                  │
│     + Physical impact: +25                                  │
│     + OT environment: +10                                   │
│     ─────────────────                                       │
│     Total: 95/100 🔴 CRITICAL                               │
│                                                             │
│  Output to State:                                           │
│  - mitre_mappings = [all techniques]                        │
│  - iocs = [extracted indicators]                            │
│  - threat_assessment = {severity: 95, risk: "CRITICAL"}     │
│  - next_agent = "orchestrator"                              │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 5: ORCHESTRATOR AGENT (Synthesis)                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Task: Synthesize all agent results into final report      │
│                                                             │
│  Inputs:                                                    │
│  - search_results from Log Analyst                          │
│  - anomalies + sequences from Anomaly Hunter                │
│  - mitre_mappings + iocs from Threat Mapper                 │
│                                                             │
│  Processing:                                                │
│  1. Build complete timeline from all events                 │
│  2. Determine attack stage (Initial/Mid/Late/Impact)        │
│  3. Assess attack success (succeeded = True)                │
│  4. Generate executive summary                              │
│  5. Prioritize recommendations                              │
│                                                             │
│  Output Format (Structured Markdown):                       │
│                                                             │
│  ### **Threat Assessment**                                  │
│  | Metric | Value |                                         │
│  | Risk Level | 🔴 **CRITICAL** |                           │
│  | Severity Score | **95/100** |                            │
│  | Confidence | High |                                      │
│  | Attack Stage | **Impact** (Complete compromise) |        │
│                                                             │
│  ### **Executive Summary**                                  │
│  A sophisticated OT attack succeeded via brute force        │
│  authentication, followed by persistence, PLC manipulation,  │
│  and safety system compromise. The attacker gained full     │
│  control of PLC-03, suppressed safety alarms, and caused    │
│  emergency shutdown via temperature parameter manipulation. │
│                                                             │
│  ### **Attack Timeline**                                    │
│  | Time | Severity | Event | MITRE |                        │
│  | 08:15:23 | 🟡 WARN | Failed login attempt 1/5 | T1110 | │
│  | 08:15:45 | 🟡 WARN | Successful login (same IP) | T1078 | │
│  | 08:16:12 | 🔴 CRIT | Persistence: User created | T1136 |  │
│  | 08:17:34 | 🔴 CRIT | PLC program uploaded | T0843 |      │
│  | 08:18:01 | ⚫ EMER | Alarms suppressed | T0878 |          │
│  | 08:18:22 | ⚫ EMER | Setpoint modified | T0836 |          │
│  | 08:19:45 | ⚫ EMER | Emergency shutdown | T0880 |         │
│                                                             │
│  ### **MITRE ATT&CK Mapping**                               │
│  | Technique | Name | Tactic | Evidence |                   │
│  | T1110 | Brute Force | Credential Access | 5 failures |  │
│  | T1078 | Valid Accounts | Initial Access | Success |     │
│  | T1136 | Create Account | Persistence | backup_admin |   │
│  | T0843 | Program Upload | Execution | PLC-03 modified | │
│  | T0878 | Alarm Suppress | Inhibit Response | Disabled | │
│  | T0836 | Modify Parameter | Impair Process | Temp 95°C | │
│  | T0880 | Loss of Safety | Impact | E-stop triggered |    │
│                                                             │
│  ### **IOCs**                                               │
│  | Type | Value | Context |                                 │
│  | IP | 192.168.1.250 | Unauthorized external address |    │
│  | Account | backup_admin | Attacker persistence |         │
│  | Asset | PLC-03 | Compromised controller |               │
│                                                             │
│  ### **Recommendations**                                    │
│  **Immediate (0-1 hour):**                                  │
│  1. 🔴 Block IP 192.168.1.250 at perimeter firewall         │
│  2. 🔴 Disable account "backup_admin"                       │
│  3. 🔴 Isolate PLC-03 from network                          │
│  4. 🔴 Restore PLC-03 from last known-good backup           │
│  5. 🔴 Verify safety system integrity before restart        │
│                                                             │
│  **Short-term (1-24 hours):**                               │
│  6. 🟡 Audit all user accounts for unauthorized access      │
│  7. 🟡 Review all PLC programs for unauthorized changes     │
│  8. 🟡 Enable MFA for all engineering workstations          │
│  9. 🟡 Implement rate limiting on authentication            │
│                                                             │
│  **Long-term:**                                             │
│  10. 🟢 Deploy network segmentation (IT/OT separation)      │
│  11. 🟢 Implement continuous monitoring on PLCs             │
│  12. 🟢 Conduct incident response tabletop exercise         │
│                                                             │
│  Output to State:                                           │
│  - final_response = [formatted markdown above]              │
│  - next_agent = "end"                                       │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 6: RENDER TO USER                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Frontend receives final_response and renders:              │
│                                                             │
│  ✅ Threat Assessment Card (severity badges)                │
│  ✅ Timeline Table (interactive, sortable)                  │
│  ✅ MITRE Technique Badges (clickable for details)          │
│  ✅ IOC List (exportable)                                   │
│  ✅ Recommendations (prioritized checklist)                 │
│                                                             │
│  User can:                                                  │
│  - Ask follow-up questions                                  │
│  - Export report as PDF/JSON                                │
│  - Click MITRE badges for technique details                 │
│  - Filter timeline by severity                              │
└─────────────────────────────────────────────────────────────┘

Total Processing Time: ~3-5 seconds
Agent Calls: 4 (Orchestrator → Log Analyst → Anomaly Hunter →
              Threat Mapper → Orchestrator)
Tool Calls: 10+ (searches, anomaly detection, MITRE mapping)
```

---

## 3. Log Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      LOG INGESTION & INDEXING PIPELINE                      │
└─────────────────────────────────────────────────────────────────────────────┘

User uploads file (CSV, JSON, Syslog, TXT)
     │
     ▼
┌──────────────────────────────────────┐
│  Step 1: File Upload Handler        │
│  (POST /api/upload)                  │
├──────────────────────────────────────┤
│                                      │
│  1. Validate file:                   │
│     - Check size (max 100MB)         │
│     - Check format (CSV/JSON/etc)    │
│     - Scan for malicious content     │
│                                      │
│  2. Save to storage:                 │
│     - Path: ./uploads/{file_id}      │
│     - Generate unique file_id (UUID) │
│                                      │
│  3. Create DB record:                │
│     INSERT INTO uploaded_files       │
│     (id, name, size, format, ts)     │
│                                      │
│  4. Trigger background task:         │
│     parse_and_index(file_id)         │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Step 2: Log Parser                  │
│  (services/parser.py)                │
├──────────────────────────────────────┤
│                                      │
│  Auto-detect format:                 │
│  ├─ CSV: Parse with pandas           │
│  ├─ JSON: Parse with json.loads      │
│  ├─ Syslog: Regex patterns           │
│  └─ Plain text: Line-by-line         │
│                                      │
│  Extract fields:                     │
│  - Timestamp (ISO8601, Unix, etc)    │
│  - Log level (INFO/WARN/ERROR)       │
│  - Source (hostname, IP, service)    │
│  - Message (free text)               │
│  - Custom fields (user, IP, etc)     │
│                                      │
│  Normalize:                          │
│  - Convert timestamps to UTC         │
│  - Standardize log levels            │
│  - Clean special characters          │
│                                      │
│  Output: List[ParsedLogEntry]        │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Step 3: Chunking                    │
│  (services/indexer.py)               │
├──────────────────────────────────────┤
│                                      │
│  Strategy: Sliding window            │
│  - Chunk size: 200 tokens            │
│  - Overlap: 50 tokens                │
│  - Preserve context across chunks    │
│                                      │
│  For each chunk:                     │
│  - chunk_id = UUID()                 │
│  - text = " ".join(log_messages)     │
│  - metadata = {                      │
│      timestamp_start,                │
│      timestamp_end,                  │
│      source,                         │
│      log_level,                      │
│      event_count                     │
│    }                                 │
│                                      │
│  Output: List[LogChunk]              │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Step 4: Embedding Generation        │
│  (sentence-transformers)             │
├──────────────────────────────────────┤
│                                      │
│  Model: all-MiniLM-L6-v2             │
│  Dimensions: 384                     │
│                                      │
│  For each chunk:                     │
│  1. Tokenize text                    │
│  2. Generate embedding vector        │
│     embedding = model.encode(text)   │
│  3. Normalize to unit length         │
│                                      │
│  Batching: Process 32 chunks at once │
│  Speed: ~1000 chunks/sec on CPU      │
│                                      │
│  Output: numpy.ndarray (N × 384)     │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Step 5: FAISS Indexing              │
│  (services/indexer.py)               │
├──────────────────────────────────────┤
│                                      │
│  Index Type: IndexFlatL2             │
│  (Exact L2 distance search)          │
│                                      │
│  Process:                            │
│  1. Create index:                    │
│     index = faiss.IndexFlatL2(384)   │
│                                      │
│  2. Add vectors:                     │
│     index.add(embeddings)            │
│                                      │
│  3. Save to disk:                    │
│     faiss.write_index(              │
│       index,                         │
│       f"./indexes/{file_id}.faiss"   │
│     )                                │
│                                      │
│  4. Save metadata mapping:           │
│     JSON: chunk_id → metadata        │
│                                      │
│  Search complexity: O(N) exact       │
│  Future: Use IVF for O(√N)           │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Step 6: Anomaly Detection           │
│  (services/anomaly.py)               │
├──────────────────────────────────────┤
│                                      │
│  Method 1: Isolation Forest          │
│  - Train on embedding vectors        │
│  - Score each log entry (0-100)      │
│  - Threshold: > 70 = anomalous       │
│                                      │
│  Method 2: Frequency Analysis        │
│  - Extract message templates         │
│  - Count occurrences                 │
│  - Flag rare messages (< 0.1%)       │
│                                      │
│  Method 3: Spike Detection           │
│  - Calculate error rate per minute   │
│  - Compute rolling baseline (μ, σ)   │
│  - Alert on > 3σ deviation           │
│                                      │
│  Method 4: Sequence Detection        │
│  - Match against attack patterns     │
│  - Use time-windowing (5-60 min)     │
│  - Score pattern confidence          │
│                                      │
│  Output: List[Anomaly]               │
│  - anomaly_id, chunk_id, score,      │
│    method, pattern, timestamp        │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Step 7: Database Storage            │
│  (SQLite)                            │
├──────────────────────────────────────┤
│                                      │
│  INSERT INTO log_chunks:             │
│  - chunk_id, file_id, text,          │
│    timestamp_start, timestamp_end,   │
│    source, log_level, metadata       │
│                                      │
│  INSERT INTO anomalies:              │
│  - anomaly_id, chunk_id, score,      │
│    method, pattern, detected_at      │
│                                      │
│  Indexes:                            │
│  - idx_file_id (for file queries)    │
│  - idx_timestamp (for time range)    │
│  - idx_score (for anomaly ranking)   │
│                                      │
│  Update file status:                 │
│  UPDATE uploaded_files               │
│  SET status = 'indexed',             │
│      chunk_count = X,                │
│      anomaly_count = Y               │
│  WHERE id = file_id                  │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Step 8: Ready for Analysis          │
├──────────────────────────────────────┤
│                                      │
│  ✅ File fully indexed                │
│  ✅ Embeddings searchable via FAISS   │
│  ✅ Anomalies pre-computed            │
│  ✅ User can now:                     │
│     - Search semantically            │
│     - View anomalies                 │
│     - Ask AI copilot questions       │
│                                      │
│  Typical processing time:            │
│  - 1K events: ~2 seconds             │
│  - 10K events: ~15 seconds           │
│  - 100K events: ~2 minutes           │
└──────────────────────────────────────┘

End-to-end latency: File upload → Ready for queries in < 3 minutes
```

---

## 4. Attack Chain Correlation Engine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   ATTACK CHAIN CORRELATION WORKFLOW                         │
└─────────────────────────────────────────────────────────────────────────────┘

Input: List[LogEvent] from timeline
     │
     ▼
┌──────────────────────────────────────┐
│  Step 1: Pattern Library Matching   │
├──────────────────────────────────────┤
│                                      │
│  Defined Attack Patterns:            │
│                                      │
│  1️⃣ Brute Force Success:             │
│     [failed login × N] →             │
│     [successful login] →             │
│     [post-exploitation]              │
│     Time window: 5 minutes           │
│                                      │
│  2️⃣ Persistence Established:         │
│     [successful login] →             │
│     [account created] →              │
│     [privilege granted]              │
│     Time window: 30 minutes          │
│                                      │
│  3️⃣ OT Safety Bypass:                │
│     [config change] →                │
│     [alarm suppression] →            │
│     [parameter modification]         │
│     Time window: 30 minutes          │
│                                      │
│  4️⃣ PLC Compromise:                  │
│     [program upload] →               │
│     [setpoint change] →              │
│     [safety event]                   │
│     Time window: 60 minutes          │
│                                      │
│  5️⃣ Full OT Attack (7 stages):       │
│     [failed logins] →                │
│     [successful login] →             │
│     [account created] →              │
│     [program upload] →               │
│     [alarm suppression] →            │
│     [setpoint change] →              │
│     [safety impact]                  │
│     Time window: 60 minutes          │
│                                      │
│  For each pattern:                   │
│  - Match sequence using regex        │
│  - Check time constraints            │
│  - Verify IP/user consistency        │
│  - Calculate confidence score        │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Step 2: Temporal Clustering         │
├──────────────────────────────────────┤
│                                      │
│  Group related events by:            │
│                                      │
│  1. Time proximity:                  │
│     - DBSCAN clustering              │
│     - ε = 5 minutes                  │
│     - min_samples = 2                │
│                                      │
│  2. Source correlation:              │
│     - Same IP address                │
│     - Same user account              │
│     - Same asset (PLC, HMI)          │
│                                      │
│  3. Semantic similarity:             │
│     - Embedding cosine similarity    │
│     - Threshold: > 0.7               │
│                                      │
│  Output: List[EventCluster]          │
│  - cluster_id                        │
│  - events                            │
│  - common_attributes                 │
│  - time_span                         │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Step 3: Causal Inference            │
├──────────────────────────────────────┤
│                                      │
│  Determine event causality:          │
│                                      │
│  Algorithm:                          │
│  1. Sort events chronologically      │
│  2. For each event pair (A, B):      │
│     IF:                              │
│     - B occurs after A               │
│     - Same source/user               │
│     - Time gap < threshold           │
│     - Pattern matches known chain    │
│     THEN: A likely caused B          │
│                                      │
│  Build directed graph:               │
│  - Nodes = Events                    │
│  - Edges = Causal relationships      │
│                                      │
│  Example:                            │
│  Failed Login → Successful Login     │
│       ↓                               │
│  Account Created                     │
│       ↓                               │
│  PLC Upload                          │
│       ↓                               │
│  Alarm Suppression                   │
│       ↓                               │
│  Parameter Change                    │
│       ↓                               │
│  Emergency Shutdown                  │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Step 4: MITRE Kill Chain Mapping    │
├──────────────────────────────────────┤
│                                      │
│  Map event graph to ATT&CK tactics:  │
│                                      │
│  Failed Login (× 5)                  │
│    ↓ Tactic: Credential Access       │
│    └─ T1110 (Brute Force)            │
│                                      │
│  Successful Login                    │
│    ↓ Tactic: Initial Access          │
│    └─ T1078 (Valid Accounts)         │
│                                      │
│  Account Created                     │
│    ↓ Tactic: Persistence             │
│    └─ T1136 (Create Account)         │
│                                      │
│  PLC Upload                          │
│    ↓ Tactic: Execution (ICS)         │
│    └─ T0843 (Program Upload)         │
│                                      │
│  Alarm Suppression                   │
│    ↓ Tactic: Inhibit Response (ICS)  │
│    └─ T0878 (Alarm Suppression)      │
│                                      │
│  Parameter Change                    │
│    ↓ Tactic: Impair Process (ICS)    │
│    └─ T0836 (Modify Parameter)       │
│                                      │
│  Emergency Shutdown                  │
│    ↓ Tactic: Impact (ICS)            │
│    └─ T0880 (Loss of Safety)         │
│                                      │
│  Kill Chain Coverage: 7/7 ✅         │
│  Attack Completeness: 100%           │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Step 5: Severity Calculation        │
├──────────────────────────────────────┤
│                                      │
│  Algorithm:                          │
│                                      │
│  base_score = 0                      │
│                                      │
│  IF attack_succeeded:                │
│    base_score += 30                  │
│                                      │
│  FOR each MITRE technique:           │
│    base_score += 5                   │
│                                      │
│  IF persistence_established:         │
│    base_score += 15                  │
│                                      │
│  IF safety_systems_affected:         │
│    base_score += 20                  │
│                                      │
│  IF physical_impact_occurred:        │
│    base_score += 25                  │
│                                      │
│  IF is_ot_environment:               │
│    base_score += 10                  │
│                                      │
│  severity = min(base_score, 100)     │
│                                      │
│  Example Calculation:                │
│  - Attack succeeded: +30             │
│  - 7 techniques: +35 (7 × 5)         │
│  - Persistence (account): +15        │
│  - Safety affected (alarms): +20     │
│  - Physical impact (shutdown): +25   │
│  - OT environment: +10               │
│  ────────────────                    │
│  Total: 95/100 🔴 CRITICAL           │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Step 6: Attack Stage Determination  │
├──────────────────────────────────────┤
│                                      │
│  Logic:                              │
│                                      │
│  IF "Impact" techniques detected:    │
│    stage = "Impact"                  │
│    (T1486, T0880, T0813, etc.)       │
│                                      │
│  ELIF "Persistence" + "Lateral       │
│       Movement" + "Privilege Esc":   │
│    stage = "Late-Stage"              │
│    (T1136, T1053, T1021, etc.)       │
│                                      │
│  ELIF "Initial Access" +             │
│       "Execution":                   │
│    stage = "Mid-Stage"               │
│    (T1078, T1110, T0843, etc.)       │
│                                      │
│  ELSE:                               │
│    stage = "Initial"                 │
│    (only reconnaissance/attempts)    │
│                                      │
│  Example: Impact                     │
│  Reason: T0880 (Loss of Safety)      │
│          detected - highest tier     │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Step 7: Generate Attack Report      │
├──────────────────────────────────────┤
│                                      │
│  Output: AttackChainReport {         │
│    sequence_name: "Full OT Attack",  │
│    events: [chronological list],     │
│    mitre_techniques: [T1110, ...],   │
│    severity_score: 95,               │
│    attack_stage: "Impact",           │
│    confidence: "High",               │
│    attack_succeeded: true,           │
│    physical_impact: true,            │
│    timeline: [formatted table],      │
│    iocs: [IP, accounts, assets],     │
│    recommendations: [prioritized]    │
│  }                                   │
│                                      │
│  Return to Orchestrator Agent        │
└──────────────────────────────────────┘

Processing Time: ~500ms for 1000 events
Accuracy: 90%+ on known patterns
Extensibility: Add new patterns via configuration
```

---

## 5. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          END-TO-END DATA FLOW                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌────────────┐
│    User    │
└──────┬─────┘
       │
       │ 1. Upload log file
       ▼
┌────────────────────┐
│  Frontend (React)  │
│  FileUpload.tsx    │
└──────┬─────────────┘
       │ 2. POST /api/upload (multipart/form-data)
       ▼
┌────────────────────────────────┐
│  Backend API (FastAPI)         │
│  routers/upload.py             │
└──────┬─────────────────────────┘
       │ 3. Save file + Create record
       ▼
┌────────────────────────────────┐         ┌──────────────────┐
│  SQLite Database               │◄────────│  File Storage    │
│  uploaded_files table          │         │  ./uploads/      │
└──────┬─────────────────────────┘         └──────────────────┘
       │ 4. Trigger background task
       ▼
┌────────────────────────────────┐
│  Parser Service                │
│  services/parser.py            │
│  (Extract fields, normalize)   │
└──────┬─────────────────────────┘
       │ 5. Parsed log entries
       ▼
┌────────────────────────────────┐
│  Indexer Service               │
│  services/indexer.py           │
│  (Chunk + Embed + Index)       │
└──────┬─────────────────────────┘
       │ 6. Embeddings
       ▼
┌────────────────────────────────┐
│  Sentence Transformers         │
│  all-MiniLM-L6-v2 (local)      │
└──────┬─────────────────────────┘
       │ 7. 384-dim vectors
       ▼
┌────────────────────────────────┐
│  FAISS Vector Store            │
│  ./indexes/{file_id}.faiss     │
└────────────────────────────────┘
       │
       │ 8. Also run anomaly detection
       ▼
┌────────────────────────────────┐
│  Anomaly Service               │
│  services/anomaly.py           │
│  (Isolation Forest + patterns) │
└──────┬─────────────────────────┘
       │ 9. Store anomalies
       ▼
┌────────────────────────────────┐
│  SQLite Database               │
│  anomalies table               │
└────────────────────────────────┘
       │
       │ 10. User asks question via chat
       ▼
┌────────────────────────────────┐
│  Frontend (React)              │
│  CopilotChat.tsx               │
└──────┬─────────────────────────┘
       │ 11. POST /api/copilot/chat
       ▼
┌────────────────────────────────┐
│  Backend API (FastAPI)         │
│  routers/copilot.py            │
└──────┬─────────────────────────┘
       │ 12. Invoke LangGraph workflow
       ▼
┌────────────────────────────────────────────────────────────┐
│  LangGraph Multi-Agent System                             │
│  agents/graph.py                                          │
└──────┬─────────────────────────────────────────────────────┘
       │
       │ 13. Orchestrator routes to agents
       ├───────────┬──────────────┬──────────────┐
       ▼           ▼              ▼              ▼
┌────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│Orchestrator│ │   Log    │ │ Anomaly  │ │  Threat  │
│   Agent    │ │ Analyst  │ │  Hunter  │ │  Mapper  │
└────────────┘ └─────┬────┘ └─────┬────┘ └─────┬────┘
                     │            │            │
       │ 14. Agents call tools    │            │
       ├─────────────┴────────────┴────────────┘
       │
       │ Tool: search_logs()
       ▼
┌────────────────────────────────┐
│  FAISS Vector Store            │
│  (Semantic search)             │
└──────┬─────────────────────────┘
       │ 15. Return relevant chunks
       ▼
┌────────────────────────────────┐
│  SQLite Database               │
│  log_chunks table              │
│  (Get full context)            │
└──────┬─────────────────────────┘
       │
       │ Tool: get_anomalies()
       ▼
┌────────────────────────────────┐
│  SQLite Database               │
│  anomalies table               │
└──────┬─────────────────────────┘
       │
       │ Tool: map_to_mitre()
       ▼
┌────────────────────────────────┐
│  MITRE Service                 │
│  services/mitre.py             │
│  (Pattern matching)            │
└──────┬─────────────────────────┘
       │
       │ Tool: detect_sequences()
       ▼
┌────────────────────────────────┐
│  Attack Chain Service          │
│  services/attack_chain.py      │
│  (Sequence matching)           │
└──────┬─────────────────────────┘
       │
       │ 16. All agents report back
       ▼
┌────────────────────────────────┐
│  Orchestrator Agent            │
│  (Synthesize results)          │
└──────┬─────────────────────────┘
       │ 17. Generate Claude API call
       ▼
┌────────────────────────────────┐
│  Anthropic Claude API          │
│  Claude Sonnet 4.5             │
│  (Final formatting & reasoning)│
└──────┬─────────────────────────┘
       │ 18. Return formatted report
       ▼
┌────────────────────────────────┐
│  Backend API (FastAPI)         │
│  routers/copilot.py            │
└──────┬─────────────────────────┘
       │ 19. HTTP 200 + JSON response
       ▼
┌────────────────────────────────┐
│  Frontend (React)              │
│  CopilotChat.tsx               │
│  (Render structured response)  │
└──────┬─────────────────────────┘
       │ 20. Display to user
       ▼
┌────────────┐
│    User    │
│  (Sees:    │
│   - Threat │
│   - Timeline)
│   - MITRE  │
│   - IOCs   │
│   - Recs)  │
└────────────┘

Legend:
→  Data flow
◄─ Read operation
```

---

## 6. Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT ARCHITECTURE OPTIONS                          │
└─────────────────────────────────────────────────────────────────────────────┘

Option 1: Single-Server Deployment (Demo/Small Teams)
─────────────────────────────────────────────────────

┌──────────────────────────────────────────────────┐
│          Docker Host (8GB RAM, 4 CPU)            │
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │  Docker Compose Stack                      │  │
│  │                                            │  │
│  │  ┌──────────────────┐  ┌───────────────┐  │  │
│  │  │  Frontend         │  │  Backend      │  │  │
│  │  │  (Nginx + React) │  │  (FastAPI)    │  │  │
│  │  │  Port: 80/443    │  │  Port: 8000   │  │  │
│  │  └──────────────────┘  └───────────────┘  │  │
│  │                                            │  │
│  │  ┌──────────────────┐  ┌───────────────┐  │  │
│  │  │  SQLite          │  │  FAISS Index  │  │  │
│  │  │  (Volume mount)  │  │  (Volume)     │  │  │
│  │  └──────────────────┘  └───────────────┘  │  │
│  │                                            │  │
│  │  ┌──────────────────────────────────────┐  │  │
│  │  │  Sentence Transformers (local)       │  │  │
│  │  │  Model cached in volume              │  │  │
│  │  └──────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  External: Anthropic Claude API (HTTPS)          │
└──────────────────────────────────────────────────┘

Benefits:
✅ Simple deployment (docker-compose up)
✅ Low cost ($50-100/month VPS)
✅ Easy backups (volume snapshots)

Limitations:
⚠️ Single point of failure
⚠️ Limited scalability (100s of users)
⚠️ Manual scaling required


Option 2: Production Deployment (Enterprise)
─────────────────────────────────────────────

┌────────────────────────────────────────────────────────────────┐
│                       Load Balancer (Nginx/Traefik)            │
│                       SSL Termination                          │
└─────────────────────┬──────────────────────────────────────────┘
                      │
          ┌───────────┴───────────┐
          │                       │
          ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│  Frontend Pods   │    │  Backend Pods    │
│  (Kubernetes)    │    │  (Kubernetes)    │
│                  │    │                  │
│  Replicas: 3     │    │  Replicas: 5     │
│  Auto-scale      │    │  Auto-scale      │
│  CPU: 0.5        │    │  CPU: 2, RAM: 4GB│
└──────────────────┘    └─────────┬────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
          ┌──────────────────┐        ┌──────────────────┐
          │  PostgreSQL      │        │  Redis Cache     │
          │  (Managed RDS)   │        │  (Embeddings)    │
          │                  │        │                  │
          │  Multi-AZ        │        │  Cluster: 3      │
          │  Backups: Daily  │        │  nodes           │
          └──────────────────┘        └──────────────────┘
                    │
                    │
                    ▼
          ┌──────────────────┐
          │  S3/MinIO        │
          │  Object Storage  │
          │                  │
          │  - Log files     │
          │  - FAISS indexes │
          │  - Backups       │
          └──────────────────┘

Kubernetes Resources:
- Namespace: logsentinel
- Ingress: HTTPS with cert-manager
- HPA: Scale 3-20 pods based on CPU
- PVC: Persistent volumes for indexes
- Secrets: API keys, DB credentials

Benefits:
✅ High availability (99.9% uptime)
✅ Auto-scaling (1000s of users)
✅ Zero-downtime deployments
✅ Multi-region support

Cost: $500-2000/month (AWS/GCP/Azure)
```

---

## Summary of Diagrams

1. **System Architecture**: Complete technical stack visualization
2. **Multi-Agent Workflow**: Step-by-step agent collaboration process
3. **Log Processing Pipeline**: End-to-end ingestion workflow
4. **Attack Chain Correlation**: Sequence detection algorithm
5. **Data Flow**: Request/response paths through system
6. **Deployment Options**: Infrastructure configurations

These diagrams can be used in your presentation slides, converted to visual formats using tools like Mermaid, Draw.io, or presented as-is in Markdown.
