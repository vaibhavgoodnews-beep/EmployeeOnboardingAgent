# Agentic AI Employee Onboarding - Complete Technical Documentation

**Date**: March 2, 2026  
**Version**: 1.0  
**Status**: As-Implemented

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [File-by-File Breakdown](#2-file-by-file-breakdown)
3. [Agent System](#3-agent-system)
4. [MCP Layer](#4-mcp-layer)
5. [UI Flow Documentation](#5-ui-flow-documentation)
6. [Database Schema](#6-database-schema)
7. [Skill Gap Assessment Lifecycle](#7-skill-gap-assessment-lifecycle)
8. [Gemini LLM Integration](#8-gemini-llm-integration)
9. [Audit & Logging System](#9-audit--logging-system)
10. [End-to-End Flow Summary](#10-end-to-end-flow-summary)

---

## 1. Architecture Overview

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  Streamlit Web Interface                    │
│  (Dashboard, Employees, Projects, Assignments, Assessment)  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              AgentOrchestrator (app.py)                     │
│  - Coordinates 4 specialized agents                         │
│  - Manages MCP registry                                     │
│  - Handles session state                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   ┌─────────┐    ┌─────────────┐   ┌──────────────┐
   │ HR Agent│    │ IT Agent    │   │ Training Ag. │
   └────┬────┘    └──────┬──────┘   └──────┬───────┘
        │                │                │
        │        ┌───────┴────────┐       │
        │        ▼                ▼       │
        └────────┬────────────────┘       │
        │ Skill Gap Agent                │
        └────────┬─────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              MCPRegistry (Tool Management)                   │
│  - Database operations (db_read, db_write)                  │
│  - Gemini integrations                                      │
│  - Email simulation                                         │
│  - Audit logging                                            │
└───────────────┬──────────────────────┬──────────────────────┘
                │                      │
        ┌───────▼────────┐      ┌──────▼──────────┐
        │   SQLite DB    │      │  Gemini API    │
        │  onboarding.db │      │ (gemini-1.5)   │
        └────────────────┘      └────────────────┘
```

### Core Principles

- **Agent-Oriented**: Four specialized agents handle distinct onboarding domains
- **Tool Registry Pattern**: MCP (Model Context Protocol) registry centralizes all external operations
- **Declarative DB Access**: All database operations wrap through MCP tools, never direct DB calls
- **Synchronous Orchestration**: Agents execute sequentially; results flow from one to next
- **Audit-First**: Every action is logged before UI confirmation

---

## 2. File-by-File Breakdown

### 2.1 `app.py` (834 lines)

**Purpose**: Main Streamlit web application and agent orchestration layer.

#### Classes

**1. `AgentOrchestrator`**
- **Purpose**: Orchestrates multi-agent workflows
- **Methods**:
  - `__init__(registry: MCPRegistry)` → Initializes 4 agents (HR, IT, Training, SkillGap)
  - `run_onboarding(employee_id: int)` → Executes end-to-end onboarding workflow
  - `assign_project_and_trigger_skill_gap(employee_id, project_id, role_on_project)` → Assigns employee to project and triggers assessment
  - `submit_assessment_answers(assessment_id, answers)` → Processes assessment submission and generates recommendations

#### Functions

**Bootstrap & Initialization**:
- `bootstrap()` → `@st.cache_resource` — Initializes database, seeds data, creates registry & agents
- `init_session_state()` → Sets up Streamlit session state defaults
- `register_mcp_tools(registry, gemini_client)` → Registers 8 MCP tools for agent execution

**Utility Functions**:
- `sanitize_text(value, max_len=2000)` → Strips/normalizes text
- `is_valid_email(email)` → Regex-based email validation
- `to_df(rows)` → Converts list of dicts to pandas DataFrame
- `load_css()` → Loads CSS from `static/styles.css`
- `parse_json_field(raw_value, default)` → Safely parses JSON or returns default
- `get_logo_data_uri()` → Encodes SVG logo to base64 data URI

**Auth Functions**:
- `render_auth_gate()` → Displays login form; checks against AUTH_USERS dict; manages logout
- `AUTH_USERS` = {"admin": "admin123", "hrlead": "hrlead123", "itops": "itops123"}

**UI Render Functions** (each fetches data and renders Streamlit components):
- `render_header()` → Displays branded header with logo
- `render_dashboard(registry)` → Displays 4 metric cards + recent agent activity table
- `render_employees(orchestrator, registry)` → Employee list + create form + onboarding control
- `render_projects(registry)` → Project list with assignment counts
- `render_assign_project(orchestrator, registry)` → Form to assign employee to project
- `render_skill_gap_assessment(orchestrator, registry)` → Assessment form (2 tabs: Form & History)
- `render_recommendation_block(recommendation)` → Displays strengths/gaps/certifications/courses
- `render_audit_logs(registry)` → Filterable audit log viewer
- `main()` → Entry point; sets page config, authenticates, renders sidebar navigation

#### Dependencies
- `streamlit` (UI framework)
- `pandas` (dataframe handling)
- `json`, `re`, `base64`, `pathlib` (utilities)
- Local: `agents/*`, `db/database`, `db/seed_data`, `mcp/registry`, `utils/*`

#### When Executed
- Runs continuously on Streamlit server
- Reruns on every user interaction
- Bootstrap happens once via `@st.cache_resource`

#### Data Flow
```
User Action → Form Submission → AgentOrchestrator → Agent.execute() 
→ MCP tool calls → DB/Gemini → Agent reflect() → Session State Update → UI Rerender
```

---

### 2.2 `agents/base_agent.py` (26 lines)

**Purpose**: Abstract base class defining agent interface.

#### Class: `BaseAgent` (ABC)

**Constructor**:
- `__init__(mcp_registry)` → Stores registry reference

**Abstract Methods** (must be implemented by subclasses):
- `plan(context: dict) → dict` → Validates and enriches context
- `use_tools(context: dict) → dict` → Executes MCP tools to accomplish action
- `reflect(result: dict) → dict` → Post-processes result, adds reflection, logs

**Concrete Method**:
- `execute(context: dict) → dict` → Template method orchestrating the three-phase flow:
  ```
  1. planned = self.plan(context)
  2. tool_result = self.use_tools(planned)
  3. return self.reflect(tool_result)
  ```

#### Design Pattern
- **Template Method**: Defines workflow; subclasses fill in details
- **No agency decision logic**: Agents are deterministic processors, not autonomous planners

---

### 2.3 `agents/hr_agent.py` (188 lines)

**Purpose**: Handles employee lifecycle and project assignments.

#### Class: `HRAgent(BaseAgent)`

**Name**: `"HR Agent"`

**Methods**:

**1. `plan(context: dict) → dict`**
- Validates `action` property is exactly one of: `"create_employee"`, `"update_onboarding"`, `"assign_project"`
- Raises `ValueError` if unsupported
- Returns context with action field isolated

**2. `use_tools(context: dict) → dict`**
- Dispatches to private method based on action:
  - `create_employee` → `_create_employee(context)`
  - `update_onboarding` → `_update_onboarding_status(context)`
  - `assign_project` → `_assign_project(context)`

**3. `reflect(result: dict) → dict`**
- Adds `"agent": "HR Agent"` to result
- Sets `"reflection"` to status message based on result["status"]
- Returns enhanced result

**Private Methods**:

**`_create_employee(context: dict) → dict`**
- **Input Required**: first_name, last_name, email, department, role, joining_date
- **Validation**: All fields must be non-empty
- **DB Write**: Inserts row into `Employees` table with status="Pending"
- **Logging**: Calls `log_action` MCP tool
- **Email**: Calls `send_email` MCP tool (simulated)
- **Returns**: `{"status": "created", "employee_id": lastrowid}`

**`_update_onboarding_status(context: dict) → dict`**
- **Input Required**: employee_id, status
- **Validation**: employee_id > 0, status non-empty
- **DB Write**: Updates `Employees.status` where employee_id matches
- **Logging**: Calls `log_action` MCP tool
- **Returns**: `{"status": "updated", "employee_id", "onboarding_status"}`

**`_assign_project(context: dict) → dict`**
- **Input Required**: employee_id, project_id, role_on_project
- **Validation**: All > 0, role non-empty; verifies employee and project exist
- **DB Operations**:
  1. Mark previous active assignments as "Completed"
  2. Insert new row into `EmployeeProjects` with status="Active"
- **Logging**: Calls `log_action` MCP tool
- **Email**: Sends notification to employee
- **Returns**: `{"status": "assigned", "assignment_id", "employee_id", "project_id"}`

#### MCP Tools Called
- `db_read` (2 calls in assign_project to verify employee/project exist)
- `db_write` (1, 1, or 3+ calls per method)
- `log_action` (1 per method)
- `send_email` (1-2 per method)

#### DB Tables Modified
- `Employees` (INSERT, UPDATE)
- `EmployeeProjects` (UPDATE, INSERT)
- `AuditLogs` (INSERT, via log_action)

---

### 2.4 `agents/it_agent.py` (96 lines)

**Purpose**: Provisions IT access and assets for employees.

#### Class: `ITAgent(BaseAgent)`

**Name**: `"IT Agent"`

**Methods**:

**1. `plan(context: dict) → dict`**
- Validates action is exactly `"provision_access"`
- Raises `ValueError` if not
- Returns context with action field isolated

**2. `use_tools(context: dict) → dict`**
- Extracts `employee_id` and optional `project_id`
- Validates `employee_id > 0`
- Queries `Employees` table to fetch name and email
- Raises `ValueError` if employee not found
- Generates deterministic asset tag: `f"LAP-{employee_id:04d}"`
- Builds account package dict with VPN, email group, SSO status
- Logs action with account_pack metadata
- **Sends email** with asset details
- **Returns**: Dict with status="provisioned", asset_tag, account_pack

**3. `reflect(result: dict) → dict`**
- Adds `"agent": "IT Agent"`
- Adds reflection comment about enterprise access controls
- Returns enhanced result

#### Account Badge Generation
```python
asset_tag = f"LAP-{employee_id:04d}"
# Example: Employee 1 → "LAP-0001"
# Example: Employee 42 → "LAP-0042"
```

#### MCP Tools Called
- `db_read` (1 call)
- `log_action` (1 call)
- `send_email` (1 call)

#### DB Tables Modified
- `AuditLogs` (INSERT, via log_action)

---

### 2.5 `agents/training_agent.py` (105 lines)

**Purpose**: Assigns role-based training modules to employees.

#### Class: `TrainingAgent(BaseAgent)`

**Name**: `"Training Agent"`

**Methods**:

**1. `plan(context: dict) → dict`**
- Validates action is exactly `"assign_training"`
- Raises `ValueError` if not
- Returns context with action field isolated

**2. `use_tools(context: dict) → dict`**
- Extracts `employee_id` and optional `project_id`
- Validates `employee_id > 0`
- Queries `Employees` table for first_name, email, role
- Raises `ValueError` if employee not found
- Calls `_build_modules(role, project_id)` to determine training plan
- Logs action with modules list
- **Sends email** with assigned modules
- **Returns**: Dict with status="training_assigned", modules list

**3. `reflect(result: dict) → dict`**
- Adds `"agent": "Training Agent"`
- Adds reflection comment about compliance + upskilling
- Returns enhanced result

**Private Method: `_build_modules(role: str, project_id: int | None) → list[str]`**
- Starts with 3 mandatory modules:
  - "Code of Conduct and Compliance"
  - "Information Security Awareness"
  - "Enterprise Data Protection"
- If role contains "engineer" (case-insensitive):
  - Adds "Secure SDLC Fundamentals"
  - Adds "Agile Delivery for Distributed Teams"
- If role contains "manager":
  - Adds "Delivery Governance and Risk Management"
- If project_id provided:
  - Adds "Project Context Briefing"
- Returns final modules list

#### Module Assignment Logic Example
```
An employee with role="Software Engineer" on project 1 receives:
  1. Code of Conduct and Compliance
  2. Information Security Awareness
  3. Enterprise Data Protection
  4. Secure SDLC Fundamentals
  5. Agile Delivery for Distributed Teams
  6. Project Context Briefing
```

#### MCP Tools Called
- `db_read` (1 call)
- `log_action` (1 call)
- `send_email` (1 call)

#### DB Tables Modified
- `AuditLogs` (INSERT, via log_action)

---

### 2.6 `agents/skill_gap_agent.py` (343 lines)

**Purpose**: Generates skill assessments, evaluates answers, generates recommendations.

#### Class: `SkillGapAgent(BaseAgent)`

**Name**: `"Skill Gap Agent"`

**Methods**:

**1. `plan(context: dict) → dict`**
- Validates action is `"generate_assessment"` or `"evaluate_assessment"`
- Raises `ValueError` if unsupported

**For generate_assessment**:
- Extracts employee_id, project_id, question_count (clamps 10-15)
- Fetches employee and project records via `_fetch_single()`
- Returns enriched context with employee, project objects

**For evaluate_assessment**:
- Extracts assessment_id
- Joins Assessments with Projects to fetch tech_stack
- Returns context with assessment object

**2. `use_tools(context: dict) → dict`**
- Dispatches based on action:
  - `"generate_assessment"` → `_generate_assessment(context)`
  - `"evaluate_assessment"` → `_evaluate_assessment(context)`

**3. `reflect(result: dict) → dict`**
- **For generation**: 
  - If question count < 10, appends filler questions to reach minimum
  - Filler questions are hardcoded generic resilience/debugging questions
  - Logs action in MCP
  - Sets reflection message about question validation
- **For evaluation**:
  - Calls `reflect_recommendation` MCP tool to refine recommendation
  - Handles reflection response or uses fallback notes
  - **Updates** Assessments table to mark "Completed"
  - **Inserts** new row into Recommendations table (with JSON-serialized certs/courses)
  - Logs action with identified skill gaps
  - Returns comprehensive result with analysis, certifications, courses

**Private Methods**:

**`_generate_assessment(context: dict) → dict`**
1. Calls `generate_assessment_questions` MCP tool
2. Inserts new Assessments record with status="Pending"
3. Bulk inserts questions into AssessmentQuestions table
4. Logs action
5. Returns dict with assessment_id, employee, project, questions list

**`_evaluate_assessment(context: dict) → dict`**
1. Fetches assessment with QA rows (joins AssessmentQuestions + AssessmentAnswers)
2. Constructs QA pairs list
3. Scores each answer using `_score_answer()` (word count-based)
4. Updates AssessmentAnswers rows with scores
5. Calls `analyze_skill_answers` MCP tool → gets strengths/gaps
6. Calls `recommend_courses` MCP tool → gets certifications/courses
7. Calls `_compose_recommendation_text()` to build report
8. Returns dict with all analysis data

**`_fetch_single(query: str, params: tuple) → dict`**
- Calls `db_read` MCP tool
- Raises `ValueError` if no rows
- Returns first row as dict

**`_score_answer(answer: str) → float`**
- Counts words in answer
- Returns 5.0 if ≥80 words
- Returns 4.0 if ≥50 words
- Returns 3.0 if ≥30 words
- Returns 2.0 if ≥15 words
- Returns 1.0 if >0 words
- Returns 0.0 if empty

**`_compose_recommendation_text(analysis, recommendations) → str`**
- Assembles multi-line recommendation summary
- Includes strengths, gaps, certifications, courses (limited to top N items)
- Returns formatted string

#### MCP Tools Called
- `generate_assessment_questions` (1 call)
- `db_read` (3+ calls)
- `db_write` (2+ calls)
- `analyze_skill_answers` (1 call)
- `recommend_courses` (1 call)
- `reflect_recommendation` (1 call)
- `log_action` (2 calls)

#### DB Tables Modified
- `Assessments` (INSERT, UPDATE)
- `AssessmentQuestions` (INSERT bulk)
- `AssessmentAnswers` (UPDATE)
- `Recommendations` (INSERT)
- `AuditLogs` (INSERT, via log_action)

---

### 2.7 `db/database.py` (133 lines)

**Purpose**: SQLite database layer and schema initialization.

#### Constants
- `DB_PATH` = `Path(__file__).resolve().parent.parent / "onboarding.db"`
- Location: `EmployeeOnboardingAgent/onboarding.db`

#### Functions

**`get_connection() → sqlite3.Connection`**
- Opens SQLite connection to onboarding.db
- Sets `row_factory = sqlite3.Row` (access columns by name)
- Enables foreign key constraints: `PRAGMA foreign_keys = ON`
- Connection not thread-bound (check_same_thread=False)

**`initialize_database() → None`**
- Executes schema creation if tables don't exist
- Creates 8 tables (see Section 6 for full schema)
- Called once on app startup

**`execute_read(query: str, params: Iterable) → list[dict]`**
- Opens connection
- Executes SELECT query with params
- Converts rows to dicts using sqlite3.Row
- Closes connection
- Returns list of dicts

**`execute_write(query: str, params: Iterable, many: bool) → int`**
- Opens connection
- If `many=True`: `executemany(query, params)` then `commit()`
- Else: `execute(query, params)` then `commit()`
- Returns `cursor.rowcount` (many=True) or `cursor.lastrowid` (many=False)
- Closes connection

#### JSON Configuration
- Foreign key constraints enforced
- Row factory enables named column access
- All writes auto-commit

---

### 2.8 `db/seed_data.py` (181 lines)

**Purpose**: Populates database with initial test data.

#### Function: `seed_data() → None`

**Guard Condition**:
- Checks if Employees table has rows
- If yes, returns immediately (idempotent)
- If no, proceeds to seed

**Data Inserted**:

**Employees** (10 rows):
- Names: Aarav Sharma, Ishita Nair, Rohan Mehta, Neha Kulkarni, Arjun Rao, Pooja Singh, Karan Patel, Divya Iyer, Manav Joshi, Sara Thomas
- Departments: Engineering, Cybersecurity, Delivery, QA, Support
- Roles: Software Engineer, Data Engineer, Security Analyst, Project Manager, Cloud Engineer, Automation Engineer, Backend Engineer, Frontend Engineer, DevOps Specialist, Machine Learning Engineer
- Status: Active or Pending
- Joining dates: Spread across 60 days before today

**Projects** (5 rows):
- Project names: Retail Banking Mobile Platform, Data Lake Modernization, CRM Rollout, Cloud Migration Factory, Cyber Defense Operations
- Tech stacks: Python/FastAPI/AWS, Spark/Databricks/Azure, Salesforce, Java/Kubernetes, SIEM/Python/Azure
- Description, dates, status fields

**EmployeeProjects** (5 rows):
- Assigns 5 employees to projects with status="Active"
- Examples: Employee 1 → Project 1 as "API Developer"

**Skills** (22 rows):
- Links employees to skills with proficiency ratings (1-5)
- Examples: Employee 1 = Python (4), FastAPI (3), AWS (3)

#### Execution Context
- Called once in `bootstrap()` function in app.py
- Guarded by check to prevent duplicate data on reruns

---

### 2.9 `mcp/registry.py` (40 lines)

**Purpose**: Simple MCP (Model Context Protocol) tool registry for safe agent-tool interactions.

#### Class: `MCPRegistry`

**Constructor**: `__init__()`
- Initializes empty dict `_tools`

**Methods**:

**`register_tool(name: str, function: Callable[..., Any]) → None`**
- Validates name is non-empty string
- Validates function is callable
- Raises `ValueError` if either invalid
- Stores mapping `_tools[name] = function`

**`execute_tool(name: str, args: dict | None) → Any`**
- Checks if tool name is registered
- Raises `KeyError` if not found
- Merges args dict (defaults to empty)
- Calls `_tools[name](**args)` with kwargs unpacking
- Returns result

**`list_tools() → list[str]`**
- Returns sorted list of registered tool names

#### Registered Tools (in app.py:register_mcp_tools)

1. **`db_read`** → `execute_read(query, params)` from db.database
2. **`db_write`** → `execute_write(query, params, many)` from db.database
3. **`log_action`** → Calls `log_action()` function from utils.logger
4. **`generate_assessment_questions`** → Calls gemini_client method
5. **`analyze_skill_answers`** → Calls gemini_client method
6. **`recommend_courses`** → Calls gemini_client method
7. **`reflect_recommendation`** → Calls gemini_client method
8. **`send_email`** → Simulates email sending (returns {"status": "sent"})

#### Design Philosophy
- Registry is dumb; it just looks up and calls
- No tool has dependencies on other tools
- All tool failures bubble up as exceptions
- No retry logic or error recovery

---

### 2.10 `utils/gemini_client.py` (372 lines)

**Purpose**: Wrapper around Google Generative AI (Gemini) API with deterministic fallbacks.

#### Class: `GeminiClient`

**Constructor**: `__init__(model_name: str | None = None)`
- Reads `GOOGLE_API_KEY` from environment
- Reads `GEMINI_MODEL` from environment (defaults to "gemini-1.5-flash")
- If both available and genai package loads: configures SDK, initializes model
- Else: sets `_model = None` (graceful degradation)

**Property**: `enabled: bool`
- Returns True if `_model` is not None
- False if API unavailable or offline

**Private Methods**:

**`_extract_json(text: str) → Any`**
- Attempts direct JSON parsing
- If fails, searches for `{...}` or `[...]` patterns with regex
- Tries parsing extracted patterns
- Returns None if no valid JSON found

**`_split_skills(tech_stack: str) → list[str]`**
- Splits tech_stack on commas
- Strips whitespace from each item
- Returns fallback list if empty: ["Software Engineering", "Cloud Fundamentals", "Data Fundamentals"]

**`generate_text(prompt: str, temperature=0.2, max_output_tokens=2048) → str`**
- If no model: returns ""
- Calls `_model.generate_content()` with config
- Catches exceptions, returns ""
- Returns generated text or ""

**Public Methods**:

**1. `generate_assessment_questions(tech_stack: str, question_count: int) → list[str]`**
- **Input**: tech_stack string, question_count (auto-clamped 10-15)
- **Prompt**: Asks for N technical assessment questions for the stack
- **Processing**: Calls `generate_text()`, tries to extract JSON array
- **Validation**: If valid list with ≥10 items, returns first 'count' items
- **Fallback**: If JSON parsing fails, calls `_fallback_questions()`
- **Returns**: List of question strings

**`_fallback_questions(tech_stack: str, count: int) → list[str]`**
- Creates 6 question templates (addressing production issues, resilience, performance, testing, security, optimization)
- Splits tech stack into skills
- Cycles through templates + skills to generate 'count' questions
- **Returns**: List of deterministic questions

**2. `analyze_skill_answers(tech_stack: str, qa_pairs: list[dict]) → dict`**
- **Input**: QA pairs with "question" and "answer" keys
- **Prompt**: Analyzes answers for strengths, skill_gaps, summary
- **Processing**: Expects JSON response with keys: strengths, skill_gaps, summary
- **Validation**: If valid dict with strengths or skill_gaps, returns it
- **Fallback**: Calls `_fallback_analysis()`
- **Returns**: {"strengths": [...], "skill_gaps": [...], "summary": "..."}

**`_fallback_analysis(tech_stack: str, qa_pairs) → dict`**
- Iterates QA pairs
- Grades answers by word count (≥35 words = strength)
- Identifies related skills from tech stack
- Compiles lists of strengths and weak skills
- Returns deterministic analysis dict

**3. `recommend_courses(skill_gaps: list[str], tech_stack: str) → dict`**
- **Input**: List of skill gaps, tech_stack
- **Prompt**: Asks for certifications and course recommendations
- **Processing**: Expects JSON with "certifications" array and "courses" array (with title, provider, platform, url fields)
- **Validation**: If valid, structures course objects
- **Fallback**: Calls `_fallback_courses()`
- **Returns**: {"certifications": [...], "courses": [...]}

**`_fallback_courses(skill_gaps, tech_stack) → dict`**
- Maintains hardcoded catalog mapping: {aws, azure, python, kubernetes, spark, salesforce, java} → {cert name, course object}
- Searches tech_stack + skill_gaps for keywords
- Returns matching catalog entries or generic fallbacks
- **Returns**: Dict with up to 5 certs and 6 courses

**4. `reflect_recommendation(initial_recommendation: str, tech_stack: str, qa_pairs) → dict`**
- **Input**: Draft recommendation text, tech_stack, QA pairs
- **Prompt**: Meta-prompt asking Gemini to review and refine recommendation
- **Processing**: Expects JSON with "reflection_notes" and "final_recommendation"
- **Validation**: If valid dict with non-empty final_recommendation, returns it
- **Fallback**: Returns deterministic reflection dict
- **Returns**: {"reflection_notes": "...", "final_recommendation": "..."}

#### Gemini Configuration
- **Model**: `gemini-1.5-flash` (default)
- **Temperature**: 0.2 (low variance for determinism)
- **Max Tokens**: 2048
- **Error Handling**: All Gemini calls wrapped in try/except; empty strings or fallbacks on failure
- **Graceful Degradation**: If API unavailable, all public methods return fallback data

#### Design Pattern
- **Fail-Soft**: System operates fully offline with deterministic fallbacks
- **No Streaming**: All responses are finalized before returning
- **Safe JSON Extraction**: Handles malformed AI responses

---

### 2.11 `utils/logger.py` (19 lines)

**Purpose**: Centralized audit logging function.

#### Function: `log_action(db_write, agent_name, action, employee_id=None, project_id=None, metadata=None) → int`

**Parameters**:
- `db_write`: Callable (the MCP tool function reference)
- `agent_name`: String (e.g., "HR Agent")
- `action`: String (e.g., "Employee created")
- `employee_id`: Optional int
- `project_id`: Optional int
- `metadata`: Optional dict

**Implementation**:
1. Serializes metadata to JSON string (ensure_ascii=True)
2. Gets current UTC timestamp in ISO format
3. Calls `db_write()` with INSERT query into AuditLogs
4. Returns lastrowid

**SQL Inserted**:
```sql
INSERT INTO AuditLogs (agent_name, action, timestamp, employee_id, project_id, metadata)
VALUES (?, ?, ?, ?, ?, ?)
```

**Audit Flow**:
- Called by all agents via MCP's `log_action` tool
- **Not** called directly; always through MCP registry
- Timestamp is always UTC
- Metadata is always JSON-serialized

---

### Summary: File Dependencies

```
app.py
├── agents/ (all agents imported and instantiated)
│   ├── base_agent.py (ABC, inherited by all agents)
│   ├── hr_agent.py
│   ├── it_agent.py
│   ├── skill_gap_agent.py
│   └── training_agent.py
├── db/
│   ├── database.py (execute_read, execute_write, initialize_database)
│   └── seed_data.py (called by bootstrap)
├── mcp/
│   └── registry.py (MCPRegistry class)
└── utils/
    ├── gemini_client.py (GeminiClient for LLM calls)
    └── logger.py (log_action function)
```

---

## 3. Agent System

### 3.1 Agent Hierarchy

All agents inherit from `BaseAgent(ABC)` and implement the same three-phase `execute()` workflow.

```
BaseAgent (abstract)
├── plan() → dict
├── use_tools() → dict
├── reflect() → dict
└── execute() → dict (template method)

Concrete Agents:
├── HRAgent → manages employees, projects, assignments
├── ITAgent → provisions IT access
├── TrainingAgent → assigns training modules
└── SkillGapAgent → generates assessments, evaluates, recommends
```

### 3.2 Agent Responsibilities Matrix

| Agent | plan() | use_tools() | reflect() | DB Write | MCP Tools | DB Read | Preconditions |
|-------|--------|------------|-----------|----------|-----------|---------|---------------|
| **HR** | Validate action (create/update/assign) | Execute private handler | Add agent name, reflection | Employees, EmployeeProjects | db_*, log, email | Employees, Projects | Action must be supported |
| **IT** | Validate action (provision_access) | Fetch employee, generate asset tag | Add agent name, reflection | None direct | db_read, log, email | Employees | employee_id must exist |
| **Training** | Validate action (assign_training) | Fetch employee, build modules | Add agent name, reflection | None direct | db_read, log, email | Employees | employee_id must exist |
| **SkillGap** | Validate action, fetch employee/project/assessment | Generate assessment OR evaluate assessment | Append filler questions OR create recommendation | Assessments, AssessmentQuestions, AssessmentAnswers, Recommendations | db_*, generate_questions, analyze, recommend, reflect, log | All assessment tables | Goal must be clear |

### 3.3 Agent Execution Flow

#### Example: Create Employee (HR Agent)
```
1. User clicks "Create Employee" in UI
2. orchestrator.hr_agent.execute(context)
3. plan(context)
   - Validates action == "create_employee"
   - Returns context
4. use_tools(context)
   - _create_employee():
     - INSERT into Employees
     - Call log_action
     - Call send_email
     - Return result dict
5. reflect(result)
   - Add "agent": "HR Agent"
   - Add "reflection": success/partial message
   - Return final result
6. UI displays success and reruns
```

#### Example: Assign Project & Trigger Assessment (Orchestrator)
```
1. User selects employee, project, role
2. orchestrator.assign_project_and_trigger_skill_gap(emp_id, proj_id, role)
3. Result1 = hr_agent.execute({"action": "assign_project", ...})
   - HR inserts EmployeeProjects
   - HR logs action
   - HR sends email
4. Result2 = skill_gap_agent.execute({"action": "generate_assessment", ...})
   - SkillGap inserts Assessment
   - SkillGap calls Gemini for questions
   - SkillGap inserts AssessmentQuestions
   - SkillGap logs action
5. Return combined result
6. UI navigates to assessment form
```

### 3.4 No Inter-Agent Communication

**Important**: Agents do NOT call other agents.

- HR Agent does NOT call SkillGap Agent
- IT Agent does NOT call Training Agent
- All coordination happens in `AgentOrchestrator.run_onboarding()` or UI code

Data flows between agents only through **database state**, not direct method calls.

### 3.5 Agent Error Handling

**Errors are not caught by BaseAgent**. They bubble up from use_tools():

```python
# In HRAgent._create_employee():
if not value:
    raise ValueError(f"Missing required employee field: {field}")

# In ITAgent.use_tools():
if employee_id <= 0:
    raise ValueError("employee_id is required for IT provisioning.")

# UI catches and displays error
```

---

## 4. MCP Layer

### 4.1 What is MCPRegistry?

MCPRegistry is a **simple callable registry** pattern (NOT a full MCP server implementation).

- **Purpose**: Decouples agents from implementation details of external services
- **Pattern**: Registry lookup + kwargs unpacking
- **Philosophy**: Agents call tools by name; registry routes to implementation

### 4.2 Tool Lifecycle

```
Agent code:
  self.mcp.execute_tool("db_read", {
    "query": "SELECT * FROM Employees WHERE id = ?",
    "params": (1,)
  })

MCPRegistry.execute_tool():
  1. Validate tool name "db_read" exists in _tools
  2. Unpack args dict to kwargs
  3. Call _tools["db_read"](**args)
  4. Return result

Actual execution:
  execute_read("SELECT * FROM Employees WHERE id = ?", (1,))
    → opens connection
    → executes query
    → returns [{"employee_id": 1, ...}]
```

### 4.3 All Registered Tools

Registered in `app.py:register_mcp_tools()`:

| Tool Name | Function Reference | Params | Returns |
|-----------|-------------------|--------|---------|
| `db_read` | `execute_read` | query, params | list[dict] |
| `db_write` | `execute_write` | query, params, many | int (rowid/count) |
| `log_action` | wrapper → `log_action` | agent_name, action, employee_id, project_id, metadata | int (log_id) |
| `generate_assessment_questions` | `gemini_client.generate_assessment_questions` | tech_stack, question_count | list[str] |
| `analyze_skill_answers` | `gemini_client.analyze_skill_answers` | tech_stack, qa_pairs | dict |
| `recommend_courses` | `gemini_client.recommend_courses` | skill_gaps, tech_stack | dict |
| `reflect_recommendation` | `gemini_client.reflect_recommendation` | initial_recommendation, tech_stack, qa_pairs | dict |
| `send_email` | stub function | recipient, subject, body | dict |

### 4.4 Tool Invocation Pattern

All agent tool calls follow this pattern:

```python
result = self.mcp.execute_tool(
    "tool_name",
    {
        "param1": value1,
        "param2": value2,
    }
)
```

**Key point**: All parameters are passed as dict keys; MCPRegistry unpacks to kwargs.

### 4.5 Error Behavior

If tool is not registered or execution fails:

```python
# Tool not found
try:
    result = registry.execute_tool("nonexistent_tool", {})
except KeyError:
    # "Tool 'nonexistent_tool' is not registered."

# Tool raises exception
try:
    result = registry.execute_tool("db_read", {"query": "INVALID SQL"})
except sqlite3.OperationalError:
    # SQLException bubbles up to caller
    # UI catches and displays error
```

### 4.6 No Middleware or Retry Logic

- MCPRegistry does NOT retry failed tools
- MCPRegistry does NOT log calls (that's done by log_action tool)
- MCPRegistry does NOT transform responses
- Errors surface immediately

---

## 5. UI Flow Documentation

### 5.1 Authentication Gate

**File**: `app.py:render_auth_gate()`

**Flow**:
```
1. Check st.session_state["authenticated"]
2. If False:
   - Display login form (username, password, submit)
   - User enters credentials
   - Form submitted → check AUTH_USERS dict
   - If match: Set session state to authenticated, store username, rerun
   - If no match: Show error message, stay on login
3. If True:
   - Display "Signed in: [username]"
   - Show "Logout" button
   - If clicked: Reset auth state, clear user, rerun
```

**Credentials** (hardcoded in AUTH_USERS):
- admin / admin123
- hrlead / hrlead123
- itops / itops123

**Session State Keys**:
- `authenticated: bool`
- `current_user: str`

---

### 5.2 Dashboard Tab

**File**: `app.py:render_dashboard(registry)`

**Flow**:
```
1. Fetch 4 metrics via MCP db_read:
   - COUNT(*) FROM Employees
   - COUNT(*) FROM Projects
   - COUNT(*) FROM EmployeeProjects WHERE status = 'Active'
   - COUNT(*) FROM Assessments WHERE status = 'Pending'

2. Render 4 metric cards with counts

3. Fetch recent audit logs:
   - SELECT timestamp, agent_name, action, employee_id, project_id
   - FROM AuditLogs
   - ORDER BY log_id DESC
   - LIMIT 8

4. Display as Streamlit dataframe (hide index)
```

**Data Fetched**: No create/update operations. Read-only.

**Session State**: None modified.

**User Actions**: None on this tab (it's informational).

---

### 5.3 Employees Tab

**File**: `app.py:render_employees(orchestrator, registry)`

**Section 1: Employee List**
```
1. Fetch all employees:
   - SELECT employee_id, first_name, last_name, email, department, role, joining_date, status
   - FROM Employees
   - ORDER BY employee_id

2. Display as dataframe
```

**Section 2: Add Employee Form**
```
1. Render form fields:
   - First Name (text)
   - Last Name (text)
   - Email (text, lowercase)
   - Department (text)
   - Role (text)
   - Joining Date (date picker)

2. User clicks "Create Employee"
   - Validate all fields non-empty
   - Validate email format regex
   - Call orchestrator.hr_agent.execute({
       "action": "create_employee",
       "first_name": sanitized,
       "last_name": sanitized,
       "email": sanitized,
       "department": sanitized,
       "role": sanitized,
       "joining_date": ISO string
     })

3. HR Agent executes:
   - INSERT into Employees
   - Call log_action
   - Call send_email
   - Return employee_id

4. Display success message with ID
5. Rerun to refresh employee list
6. Form cleared on submit
```

**Section 3: Multi-Agent Onboarding**
```
1. Display info if no employees

2. If employees exist:
   - Create selectbox of employee labels
   - Show "Run End-to-End Onboarding" button

3. User clicks button:
   - Call orchestrator.run_onboarding(selected_employee_id):
     a. HR Agent: update_onboarding to "In Progress"
     b. IT Agent: provision_access
     c. Training Agent: assign_training
     d. HR Agent: update_onboarding to "Active"
   - Return dict with IT + Training results

4. Display success message with results
5. Rerun
```

**Session State**: None modified in employees tab.

---

### 5.4 Projects Tab

**File**: `app.py:render_projects(registry)`

**Flow**:
```
1. Fetch all projects with assignment counts:
   - SELECT p.project_id, p.project_name, p.client, p.tech_stack, p.status,
            COUNT(ep.assignment_id) AS assigned_employees
   - FROM Projects p
   - LEFT JOIN EmployeeProjects ep ON ep.project_id = p.project_id AND ep.status = 'Active'
   - GROUP BY p.project_id
   - ORDER BY p.project_id

2. Display as dataframe
```

**Data Operations**: Read-only.

**User Actions**: None (informational only).

---

### 5.5 Assign Project Tab

**File**: `app.py:render_assign_project(orchestrator, registry)`

**Flow**:
```
1. Fetch employees and projects:
   - SELECT employee_id, first_name, last_name FROM Employees
   - SELECT project_id, project_name FROM Projects

2. If either empty: Show info message, return

3. Create maps for selectboxes

4. Render form:
   - Selectbox: Employee
   - Selectbox: Project
   - Text input: "Role on Project" (default "Engineer")
   - Submit button: "Assign Project and Trigger Skill Gap Assessment"

5. User submits:
   - Validate role non-empty
   - Call orchestrator.assign_project_and_trigger_skill_gap(employee_id, project_id, role):
     a. HR Agent: assign_project action
        - UPDATE EmployeeProjects previous assignments to "Completed"
        - INSERT new EmployeeProjects row with status="Active"
        - call log_action
        - call send_email
        - return assignment_id
     b. SkillGap Agent: generate_assessment action
        - INSERT into Assessments (status="Pending")
        - Call generate_assessment_questions
        - INSERT questions into AssessmentQuestions
        - call log_action
        - return assessment_id
   - Return dict with assignment + assessment data

6. On success:
   - Store assessment_id in st.session_state["pending_assessment_id"]
   - Set st.session_state["current_page"] = "Skill Gap Assessment"
   - Show success message
   - Rerun (navigates to assessment tab)

7. On error: Show error message, stay on tab
```

**Session State Modified**:
- `pending_assessment_id: int`
- `current_page: str` → "Skill Gap Assessment"

---

### 5.6 Skill Gap Assessment Tab

**File**: `app.py:render_skill_gap_assessment(orchestrator, registry)`

**Two tabs**: "Assessment Form" and "Recommendation History"

#### Tab 1: Assessment Form

**Section 1: Assessment Selection**
```
1. Fetch pending assessments:
   - SELECT a.assessment_id, a.employee_id, a.project_id, a.created_at,
            e.first_name || ' ' || e.last_name AS employee_name,
            p.project_name
   - FROM Assessments a
   - JOIN Employees e ON a.employee_id = e.employee_id
   - JOIN Projects p ON a.project_id = p.project_id
   - WHERE a.status = 'Pending'
   - ORDER BY a.assessment_id DESC

2. If none: Show info "No pending assessments"

3. Create selectbox with assessment options
   - Default to pending_assessment_id from session state (if exists)

4. Display selected assessment info
```

**Section 2: Assessment Form**
```
1. Fetch questions for selected assessment:
   - SELECT question_id, question_text
   - FROM AssessmentQuestions
   - WHERE assessment_id = ?
   - ORDER BY question_id

2. If no questions: Show warning

3. Render form:
   - For each question: text_area for answer
   - Submit button: "Submit Assessment and Generate Recommendations"

4. User submits:
   - Validate all answers non-empty
   - Call orchestrator.submit_assessment_answers(assessment_id, answers_dict):
     a. SkillGap Agent: evaluate_assessment action
        - Fetch QA rows (question + answer)
        - Score each answer via _score_answer()
        - UPDATE AssessmentAnswers with score + evaluated_at
        - Call analyze_skill_answers → gets strengths/gaps
        - Call recommend_courses → gets certs/courses
        - Compose recommendation text
        - Call reflect_recommendation → gets reflection notes + final recommendation
        - UPDATE Assessments to "Completed"
        - INSERT into Recommendations
        - call log_action
        - return recommendation dict
   - Store recommendation in st.session_state["last_recommendation"]
   - Clear pending_assessment_id
   - Show success message
   - Rerun

5. Display recommendation block (if exists in session):
   - Show final_recommendation text
   - Show reflection_notes
   - Column layout with strengths/improvement areas
   - Show certifications list
   - Show courses list (with links)
```

**Section 3: Recommendation History**

```
1. Fetch all recommendations:
   - SELECT r.recommendation_id, r.assessment_id, r.employee_id, r.project_id,
            r.recommendation_text, r.certifications, r.courses, r.created_at, r.reflection_notes,
            e.first_name || ' ' || e.last_name AS employee_name,
            p.project_name
   - FROM Recommendations r
   - JOIN Employees e ... JOIN Projects p ...
   - ORDER BY r.recommendation_id DESC

2. If none: Show caption

3. Display table of recommendations (id, assessment, employee, project, created_at)

4. Selectbox to choose recommendation to inspect

5. Display detail page:
   - recommendation_text
   - reflection_notes
   - Parse certifications JSON, display list
   - Parse courses JSON, display list with links
```

**Session State**:
- `pending_assessment_id: int | None`
- `last_recommendation: dict | None`

---

### 5.7 Audit Logs Tab

**File**: `app.py:render_audit_logs(registry)`

**Flow**:
```
1. Fetch all audit logs:
   - SELECT log_id, timestamp, agent_name, action, employee_id, project_id, metadata
   - FROM AuditLogs
   - ORDER BY log_id DESC

2. If none: Show info message

3. Extract unique agent names, sort

4. Render selectbox: "Filter by agent" (options: "All" + agent list)

5. Filter logs by selected agent

6. For each log:
   - Parse metadata JSON
   - Create display row with all fields + stringified metadata

7. Display as dataframe
```

**No user actions** on this tab (read-only).

---

### 5.8 Navigation Sidebar

**File**: `app.py:main()`

**Sidebar radio button**:
```
Pages = [
  "Dashboard",
  "Employees",
  "Projects",
  "Assign Project",
  "Skill Gap Assessment",
  "Audit Logs"
]

1. Render radio with current page (from session) as default
2. User selects page
3. Store selection in st.session_state["current_page"]
4. Main() dispatches to appropriate render_*() function
```

---

## 6. Database Schema

### 6.1 Tables Overview

```
Employees
  ├─ employee_id (PK, AI)
  ├─ first_name, last_name
  ├─ email (UNIQUE)
  ├─ department, role
  ├─ joining_date
  └─ status

Projects
  ├─ project_id (PK, AI)
  ├─ project_name
  ├─ client
  ├─ description
  ├─ tech_stack
  ├─ start_date, end_date
  └─ status

EmployeeProjects
  ├─ assignment_id (PK, AI)
  ├─ employee_id (FK → Employees)
  ├─ project_id (FK → Projects)
  ├─ assigned_on
  ├─ role_on_project
  └─ status

Skills
  ├─ skill_id (PK, AI)
  ├─ employee_id (FK → Employees)
  ├─ skill_name
  ├─ proficiency (1-5)
  └─ last_updated

Assessments
  ├─ assessment_id (PK, AI)
  ├─ employee_id (FK → Employees)
  ├─ project_id (FK → Projects)
  ├─ created_at
  ├─ status
  └─ summary

AssessmentQuestions
  ├─ question_id (PK, AI)
  ├─ assessment_id (FK → Assessments)
  ├─ question_text
  └─ expected_topics

AssessmentAnswers
  ├─ answer_id (PK, AI)
  ├─ question_id (FK → AssessmentQuestions)
  ├─ employee_id (FK → Employees)
  ├─ answer_text
  ├─ score
  └─ evaluated_at

Recommendations
  ├─ recommendation_id (PK, AI)
  ├─ assessment_id (FK → Assessments)
  ├─ employee_id (FK → Employees)
  ├─ project_id (FK → Projects)
  ├─ recommendation_text
  ├─ certifications (JSON)
  ├─ courses (JSON)
  ├─ created_at
  └─ reflection_notes

AuditLogs
  ├─ log_id (PK, AI)
  ├─ agent_name
  ├─ action
  ├─ timestamp
  ├─ employee_id
  ├─ project_id
  └─ metadata (JSON)
```

### 6.2 Detailed Table Documentation

#### **Employees**

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| employee_id | INTEGER | PK, AUTOINCREMENT | Unique identifier |
| first_name | TEXT | NOT NULL | Employee's first name |
| last_name | TEXT | NOT NULL | Employee's last name |
| email | TEXT | NOT NULL, UNIQUE | Unique email address |
| department | TEXT | NOT NULL | Dept (Engineering, Delivery, etc.) |
| role | TEXT | NOT NULL | Job role (Software Engineer, etc.) |
| joining_date | TEXT | NOT NULL | ISO format date |
| status | TEXT | NOT NULL, DEFAULT 'Pending' | Pending / In Progress / Active |

**Sample Row** (from seed data):
```
(1, "Aarav", "Sharma", "aarav.sharma@acme.com", "Engineering", "Software Engineer", "2026-01-21", "Active")
```

**Modified By**:
- `HRAgent._create_employee()` → INSERT
- `HRAgent._update_onboarding_status()` → UPDATE status
- `TrainingAgent.use_tools()` → READ only

**Read By**:
- Dashboard (COUNT query)
- Employees tab (list + filter)
- Various agents for validation

---

#### **Projects**

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| project_id | INTEGER | PK, AUTOINCREMENT | Unique project ID |
| project_name | TEXT | NOT NULL | Project name |
| client | TEXT | NOT NULL | Client name |
| description | TEXT | | Project description |
| tech_stack | TEXT | NOT NULL | Tech stack (comma-separated skills) |
| start_date | TEXT | NOT NULL | ISO date |
| end_date | TEXT | | ISO date (optional) |
| status | TEXT | NOT NULL, DEFAULT 'Active' | Active / Completed / On-Hold |

**Sample Row**:
```
(1, "Retail Banking Mobile Platform", "NorthBridge Bank", "Build a secure mobile platform", "Python, FastAPI, PostgreSQL, React, Docker, AWS", "2025-11-13", "2026-09-10", "Active")
```

**Modified By**:
- Seed data only (no direct agent writes)

**Read By**:
- Dashboard (COUNT query)
- Projects tab (display all)
- Assign Project tab (selectbox)
- AssignmentOrchestrator (fetch for assessment)
- Skill Gap Agent (fetch tech_stack)

---

#### **EmployeeProjects**

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| assignment_id | INTEGER | PK, AUTOINCREMENT | Assignment ID |
| employee_id | INTEGER | FK → Employees | Assigned employee |
| project_id | INTEGER | FK → Projects | Assigned project |
| assigned_on | TEXT | NOT NULL | ISO date assignment date |
| role_on_project | TEXT | NOT NULL | Role (e.g., "API Developer") |
| status | TEXT | NOT NULL, DEFAULT 'Active' | Active / Completed |

**Sample Rows**:
```
(1, 1, 1, "2026-02-11", "API Developer", "Active")
(2, 2, 2, "2026-02-13", "Data Engineer", "Active")
```

**Modified By**:
- `HRAgent._assign_project()` → UPDATE previous to "Completed", INSERT new as "Active"

**Read By**:
- Dashboard (COUNT WHERE status='Active')
- Projects tab (COUNT per project)

---

#### **Skills**

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| skill_id | INTEGER | PK, AUTOINCREMENT | Skill ID |
| employee_id | INTEGER | FK → Employees | Employee who has skill |
| skill_name | TEXT | NOT NULL | Skill name (Python, AWS, etc.) |
| proficiency | INTEGER | NOT NULL, CHECK 1-5 | Rating 1-5 |
| last_updated | TEXT | NOT NULL | ISO date |

**Sample Rows**:
```
(1, 1, "Python", 4, "2026-02-21")
(2, 1, "FastAPI", 3, "2026-02-21")
(3, 1, "AWS", 3, "2026-02-21")
```

**Modified By**:
- Seed data only (currently no agent logic to update skills)

**Read By**: 
- Not read in current codebase

**Note**: This table is seeded but not actively used in agent workflows.

---

#### **Assessments**

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| assessment_id | INTEGER | PK, AUTOINCREMENT | Assessment ID |
| employee_id | INTEGER | FK → Employees | Employee being assessed |
| project_id | INTEGER | FK → Projects | Project context |
| created_at | TEXT | NOT NULL | ISO timestamp |
| status | TEXT | NOT NULL, DEFAULT 'Pending' | Pending / Completed |
| summary | TEXT | | Brief summary text |

**Sample Row** (created by SkillGapAgent):
```
(1, 1, 1, "2026-02-21T14:30:00", "Pending", "Skill assessment generated")
```

**Lifecycle**:
1. INSERT by `SkillGapAgent._generate_assessment()` → status="Pending"
2. UPDATE by `SkillGapAgent.reflect()` → status="Completed", summary updated

**Read By**:
- Skill Gap Assessment tab (WHERE status='Pending')
- History tab (ORDER BY DESC)

---

#### **AssessmentQuestions**

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| question_id | INTEGER | PK, AUTOINCREMENT | Question ID |
| assessment_id | INTEGER | FK → Assessments | Parent assessment |
| question_text | TEXT | NOT NULL | The question |
| expected_topics | TEXT | | Comma-sep topics (e.g., tech_stack) |

**Sample Rows**:
```
(1, 1, "Describe a production issue you resolved using Python. What was your root-cause process?", "Python")
(2, 1, "How would you design a resilient module in FastAPI for high traffic?", "FastAPI")
```

**Creation**:
- `SkillGapAgent._generate_assessment()` → INSERT generated questions
- `SkillGapAgent.reflect()` → INSERT filler questions if < 10

**Read By**:
- Skill Gap Assessment form (JOIN with answers)

---

#### **AssessmentAnswers**

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| answer_id | INTEGER | PK, AUTOINCREMENT | Answer ID |
| question_id | INTEGER | FK → AssessmentQuestions | Question being answered |
| employee_id | INTEGER | FK → Employees | Employee providing answer |
| answer_text | TEXT | NOT NULL | The answer text |
| score | REAL | | Score (0-5) |
| evaluated_at | TEXT | | ISO timestamp of evaluation |

**Lifecycle**:
1. INSERT by `AgentOrchestrator.submit_assessment_answers()` via MCP via app.py form
   - Score initially NULL
   - evaluated_at initially NULL
2. UPDATE by `SkillGapAgent._evaluate_assessment()` → score + evaluated_at set

**Read By**:
- `SkillGapAgent._evaluate_assessment()` → JOIN with questions

---

#### **Recommendations**

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| recommendation_id | INTEGER | PK, AUTOINCREMENT | Recommendation ID |
| assessment_id | INTEGER | FK → Assessments | Parent assessment |
| employee_id | INTEGER | FK → Employees | Employee being recommended |
| project_id | INTEGER | FK → Projects | Project context |
| recommendation_text | TEXT | NOT NULL | Full recommendation summary |
| certifications | TEXT | | JSON array of cert names |
| courses | TEXT | | JSON array of course objects |
| created_at | TEXT | NOT NULL | ISO timestamp |
| reflection_notes | TEXT | | Reflection notes from Gemini |

**Sample Row**:
```json
{
  "recommendation_id": 1,
  "assessment_id": 1,
  "employee_id": 1,
  "project_id": 1,
  "recommendation_text": "Assessment Summary\nSkill profile indicates...",
  "certifications": "[\"AWS Certified Developer\", \"Azure Fundamentals\"]",
  "courses": "[{\"title\": \"AWS Developer Associate Prep\", ...}]",
  "created_at": "2026-02-21T14:35:00",
  "reflection_notes": "Recommendation validated against stack..."
}
```

**Creation**:
- INSERT by `SkillGapAgent.reflect()` after evaluation complete

**Read By**:
- Recommendation History tab

---

#### **AuditLogs**

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| log_id | INTEGER | PK, AUTOINCREMENT | Log entry ID |
| agent_name | TEXT | NOT NULL | Agent name (HR Agent, IT Agent, etc.) |
| action | TEXT | NOT NULL | Action description |
| timestamp | TEXT | NOT NULL | UTC ISO timestamp |
| employee_id | INTEGER | | Employee context (optional) |
| project_id | INTEGER | | Project context (optional) |
| metadata | TEXT | | JSON object with extra data |

**Sample Rows**:
```
(1, "HR Agent", "Employee created", "2026-02-21T10:00:00", 1, None, "{\"department\": \"Engineering\", \"role\": \"Software Engineer\"}")
(2, "IT Agent", "IT provisioning completed", "2026-02-21T10:01:00", 1, None, "{\"asset_tag\": \"LAP-0001\", ...}")
(3, "Skill Gap Agent", "Skill gap assessment generated", "2026-02-21T10:02:00", 1, 1, "{\"assessment_id\": 1, \"question_count\": 12}")
```

**Creation**:
- INSERT by `log_action()` function (called by all agents via MCP)

**Read By**:
- Dashboard (LIMIT 8)
- Audit Logs tab (all, filterable)

---

### 6.3 Data Lifecycle Example: Employee Onboarding

**Day 1 - Employee Creation**:
```
UI: User clicks "Create Employee" form, enters Aarav Sharma
├── HRAgent.execute({"action": "create_employee", ...})
│   └── INSERT Employees (employee_id=1, status="Pending")
│       INSERT AuditLogs ("Employee created", employee_id=1)
│       send_email(aarav.sharma@acme.com)

Initial State:
- Employees: [1, Aarav, Sharma, ..., "Pending"]
- AuditLogs: [1, HR Agent, "Employee created", ..., 1]
```

**Day 2 - Onboarding Workflow**:
```
UI: User clicks "Run End-to-End Onboarding", selects Employee 1
├── HRAgent.execute({"action": "update_onboarding", "status": "In Progress"})
│   └── UPDATE Employees SET status="In Progress" WHERE employee_id=1
│       INSERT AuditLogs
├── ITAgent.execute({"action": "provision_access", "employee_id": 1})
│   └── INSERT AuditLogs
│       send_email(asset_tag details)
├── TrainingAgent.execute({"action": "assign_training", "employee_id": 1})
│   └── INSERT AuditLogs
│       send_email(training modules)
└── HRAgent.execute({"action": "update_onboarding", "status": "Active"})
    └── UPDATE Employees SET status="Active" WHERE employee_id=1
        INSERT AuditLogs

Final State:
- Employees: [1, Aarav, Sharma, ..., "Active"]
- AuditLogs: [multiple entries from all agents]
```

**Day 5 - Project Assignment & Assessment**:
```
UI: User assigns Employee 1 → Project 1, role "API Developer"
├── HRAgent.execute({"action": "assign_project", ...})
│   ├── UPDATE EmployeeProjects SET status="Completed" WHERE ...(prior assignments)
│   ├── INSERT EmployeeProjects (assignment_id=1, employee_id=1, project_id=1, status="Active")
│   └── INSERT AuditLogs
├── SkillGapAgent.execute({"action": "generate_assessment", ...})
│   ├── INSERT Assessments (assessment_id=1, employee_id=1, project_id=1, status="Pending")
│   ├── [call Gemini for 12 questions]
│   ├── INSERT AssessmentQuestions (12+ rows)
│   └── INSERT AuditLogs

Current State:
- EmployeeProjects: [1, 1, 1, "2026-02-21", "API Developer", "Active"]
- Assessments: [1, 1, 1, "2026-02-21T14:30:00", "Pending", "..."]
- AssessmentQuestions: [12 question rows]
```

**Day 7 - Assessment Submission**:
```
UI: Employee answers assessment form, clicks "Submit"
└── SkillGapAgent.execute({"action": "evaluate_assessment", "assessment_id": 1})
    ├── [Fetch QA pairs]
    ├── [Score each answer]
    ├── INSERT/UPDATE AssessmentAnswers (12 rows with scores)
    ├── [Call analyze_skill_answers Gemini]
    ├── [Call recommend_courses Gemini]
    ├── [Call reflect_recommendation Gemini]
    ├── UPDATE Assessments SET status="Completed"
    ├── INSERT Recommendations (certifications + courses as JSON)
    └── INSERT AuditLogs

Final State:
- AssessmentAnswers: [12 rows with scores and evaluated_at]
- Assessments: [1, ..., "Completed", ...]
- Recommendations: [1, 1, 1, 1, ..., "Recommendation text", "...", "{...}", "{...}", ...]
- AuditLogs: [entry for skill gap recommendations finalized]
```

---

## 7. Skill Gap Assessment Lifecycle

This is the most complex workflow in the system.

### 7.1 Full Lifecycle Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ TRIGGER: Project Assignment                                     │
│ User selects employee + project on "Assign Project" tab          │
└─────────────────────────────────────┬───────────────────────────┘
                                      │
                        ┌─────────────▼──────────────┐
                        │ orchestrator.               │
                        │ assign_project_and_        │
                        │ trigger_skill_gap()        │
                        └─────────────┬──────────────┘
                                      │
                    ┌─────────────────┴────────────────┐
                    │                                  │
        ┌───────────▼─────────────┐   ┌──────────────▼────────┐
        │ HRAgent.execute()       │   │ SkillGapAgent.        │
        │ action: assign_project  │   │ execute()             │
        │                         │   │ action:               │
        │ Returns:                │   │ generate_assessment   │
        │ - assignment_id         │   │                       │
        │ - triggers project      │   │ Returns:              │
        │   assignment           │   │ - assessment_id       │
        └─────────────────────────┘   │ - questions generated │
                                      └──────────────┬────────┘
                                                     │
                                    ┌────────────────▼──────────────┐
                                    │ GEMINI QUESTION GENERATION     │
                                    │ (gemini_client)                │
                                    │                                │
                                    │ Input:                         │
                                    │ - tech_stack                   │
                                    │ - question_count (10-15)       │
                                    │                                │
                                    │ Output:                        │
                                    │ - List of assessment questions │
                                    │ - Or fallback questions        │
                                    └────────────────┬───────────────┘
                                                     │
                                   ┌─────────────────▼──────────────┐
                                   │ ASSESSMENT STORAGE             │
                                   │                                │
                                   │ INSERT Assessments table       │
                                   │ INSERT AssessmentQuestions     │
                                   │ INSERT AuditLogs               │
                                   │                                │
                                   │ Status: PENDING                │
                                   └─────────────────┬──────────────┘
                                                     │
                                ┌────────────────────▼────────────────┐
                                │ UI REDIRECTION                      │
                                │                                     │
                                │ Store assessment_id in session      │
                                │ Navigate to Skill Gap Assessment tab│
                                │ Display assessment form              │
                                └────────────────────┬────────────────┘
                                                     │
                        ┌────────────────────────────▼───────────────┐
                        │ PHASE 2: EMPLOYEE COMPLETES ASSESSMENT     │
                        │                                            │
                        │ Employee reads questions                   │
                        │ Employee writes answers for each question  │
                        │ Employee clicks "Submit Assessment"        │
                        └────────────────┬───────────────────────────┘
                                         │
                      ┌──────────────────▼──────────────────┐
                      │  SkillGapAgent.execute()            │
                      │  action: evaluate_assessment        │
                      │                                     │
                      │ 1. Fetch QA pairs from DB          │
                      │ 2. Score each answer (word count)  │
                      │ 3. UPDATE AssessmentAnswers        │
                      └──────────────┬──────────────────────┘
                                     │
                ┌────────────────────┴──────────────────┐
                │                                       │
    ┌───────────▼──────────────┐        ┌─────────────▼──────────┐
    │ GEMINI ANALYSIS          │        │ GEMINI RECOMMENDATIONS │
    │                          │        │                        │
    │ Input:                   │        │ Input:                 │
    │ - tech_stack             │        │ - skill_gaps list      │
    │ - QA pairs               │        │ - tech_stack           │
    │                          │        │                        │
    │ Output:                  │        │ Output:                │
    │ - strengths              │        │ - certifications       │
    │ - skill_gaps             │        │ - courses (with links) │
    │ - summary                │        │                        │
    │ (Or fallback analysis)  │        │ (Or fallback courses)  │
    └───────────┬──────────────┘        └─────────────┬──────────┘
                │                                     │
                └────────────────┬────────────────────┘
                                 │
                    ┌────────────▼──────────────┐
                    │ Compose Draft              │
                    │ Recommendation Text        │
                    │                           │
                    │ (Strengths + Gaps +       │
                    │  Certs + Courses)         │
                    └────────────┬───────────────┘
                                 │
                    ┌────────────▼──────────────┐
                    │ GEMINI REFLECTION         │
                    │                           │
                    │ Input:                    │
                    │ - draft_recommendation    │
                    │ - tech_stack              │
                    │ - QA pairs                │
                    │                           │
                    │ Output:                   │
                    │ - reflection_notes        │
                    │ - final_recommendation    │
                    └────────────┬───────────────┘
                                 │
                    ┌────────────▼──────────────┐
                    │ RECOMMENDATION STORAGE    │
                    │                           │
                    │ UPDATE Assessments        │
                    │ INSERT Recommendations    │
                    │ INSERT AuditLogs          │
                    │                           │
                    │ Status: COMPLETED         │
                    └────────────┬───────────────┘
                                 │
                    ┌────────────▼──────────────┐
                    │ UI DISPLAY                │
                    │                           │
                    │ Show recommendation block:│
                    │ - Final recommendation    │
                    │ - Reflection notes        │
                    │ - Strengths / Gaps        │
                    │ - Certifications          │
                    │ - Courses (clickable)     │
                    └───────────────────────────┘
```

### 7.2 Step-by-Step State Changes

#### Step 1: Generate Assessment

**Trigger**: User clicks "Assign Project and Trigger Skill Gap Assessment"

**Input**:
```python
{
  "action": "generate_assessment",
  "employee_id": 1,
  "project_id": 1,
  "question_count": 12  # default, clamped 10-15
}
```

**Execution** (SkillGapAgent):
```
plan(): Validate action, fetch employee + project
use_tools():
  1. Call MCP "generate_assessment_questions"
     with tech_stack="Python, FastAPI, PostgreSQL, React, Docker, AWS"
     with question_count=12
     ↓
     [Returns 12 questions or fallback questions]
  
  2. INSERT Assessments table:
     - employee_id = 1
     - project_id = 1  
     - created_at = now_utc()
     - status = "Pending"
     - summary = "Skill assessment generated"
     ↓ Returns assessment_id = 1
  
  3. INSERT AssessmentQuestions table (12 rows):
     - question_id = auto
     - assessment_id = 1
     - question_text = [each question]
     - expected_topics = "Python, FastAPI, ..."

reflect(): 
  - If questions < 10: append filler questions to reach 10
  - Call log_action
  - Return result with questions list
```

**DB State After**:
```sql
-- Assessments
INSERT INTO Assessments VALUES (1, 1, 1, "2026-02-21T14:30:00", "Pending", "Skill assessment generated");

-- AssessmentQuestions (12+ rows)
INSERT INTO AssessmentQuestions VALUES 
  (1, 1, "Describe a production issue..."), 
  (2, 1, "How would you design a resilient..."),
  ... (12 total)

-- AuditLogs
INSERT INTO AuditLogs VALUES (X, "Skill Gap Agent", "Skill gap assessment generated", "2026-02-21T14:30:00", 1, 1, {...});
```

**Session State Update**:
```python
st.session_state["pending_assessment_id"] = 1
st.session_state["current_page"] = "Skill Gap Assessment"
```

**UI Navigation**:
```
Success message shown
Tab automatically switches to "Skill Gap Assessment"
Assessment form displays all 12+ questions
```

---

#### Step 2: Evaluate Assessment

**Trigger**: Employee answers all questions and clicks "Submit Assessment and Generate Recommendations"

**Input**:
```python
{
  "assessment_id": 1,
  "answers": {
    1: "I once debugged a FastAPI timeout issue...",  # answer to Q1
    2: "For resilience, I'd implement circuit breakers...",  # answer to Q2
    ... (12 answers)
  }
}
```

**Execution Flow** (SkillGapAgent):

**Stage 1: Assessment Loading & Validation**
```
plan():
  Fetch assessment from Assessments table
  Join with Projects to get tech_stack
  Validate assessment exists and belongs to correct employee
  
  Context result: {
    "action": "evaluate_assessment",
    "assessment": {
      "assessment_id": 1,
      "employee_id": 1,
      "project_id": 1,
      "tech_stack": "Python, FastAPI, PostgreSQL, React, Docker, AWS"
    }
  }
```

**Stage 2: Answer Scoring**
```
use_tools():
  1. Fetch QA pairs via DB:
     SELECT q.question_id, q.question_text, COALESCE(a.answer_text, '') AS answer_text
     FROM AssessmentQuestions q
     LEFT JOIN AssessmentAnswers a ON ...
     WHERE q.assessment_id = 1
     ↓ Returns 12 rows with question text + answer text

  2. For each (question, answer):
     a. Score using _score_answer(answer):
        - Count words
        - If >= 80 words → 5.0
        - If >= 50 words → 4.0
        - If >= 30 words → 3.0
        - If >= 15 words → 2.0
        - If > 0 words → 1.0
        - Else → 0.0
     
     b. UPDATE AssessmentAnswers:
        SET score = [score], evaluated_at = [now]
        WHERE question_id = [qid] AND employee_id = 1

  3. Construct QA pairs list for Gemini:
     qa_pairs = [
       {"question": "Describe a production issue...", "answer": "I once debugged..."},
       ...
     ]
```

**Stage 3: Gemini Analysis Calls**
```
  4. Call MCP "analyze_skill_answers":
     Input: {
       "tech_stack": "Python, FastAPI, ...",
       "qa_pairs": [12 qa pairs]
     }
     Output (from Gemini or fallback):
     {
       "strengths": [
         "Demonstrates strong problem-solving skills",
         "Shows knowledge of distributed system design",
         ...
       ],
       "skill_gaps": [
         "Limited experience with cloud deployment",
         "Needs improvement in load testing practices",
         ...
       ],
       "summary": "Skill profile indicates readiness..."
     }

  5. Call MCP "recommend_courses":
     Input: {
       "skill_gaps": ["Limited experience with cloud deployment", ...],
       "tech_stack": "Python, FastAPI, ..."
     }
     Output (from Gemini or fallback):
     {
       "certifications": [
         "AWS Certified Developer - Associate",
         "Azure Administrator",
         ...
       ],
       "courses": [
         {
           "title": "AWS Developer Associate Prep",
           "provider": "Udemy",
           "platform": "Udemy",
           "url": "https://www.udemy.com/..."
         },
         ...
       ]
     }

  6. Compose draft recommendation text using:
     _compose_recommendation_text(analysis, recommendations)
     ↓ Returns multi-line string with summary
```

**Stage 4: Gemini Reflection & Refinement**
```
reflect():
  1. Call MCP "reflect_recommendation":
     Input: {
       "initial_recommendation": [draft text],
       "tech_stack": "Python, FastAPI, ...",
       "qa_pairs": [12 qa pairs]
     }
     Output (from Gemini or fallback):
     {
       "reflection_notes": "Recommendation validated against stack...",
       "final_recommendation": "[Refined recommendation text]"
     }

  2. UPDATE Assessments:
     SET status = "Completed", summary = [final_recommendation[:600]]
     WHERE assessment_id = 1

  3. INSERT Recommendations:
     assessment_id = 1
     employee_id = 1
     project_id = 1
     recommendation_text = [final_recommendation]
     certifications = JSON.stringify(certs)
     courses = JSON.stringify(courses)
     created_at = now()
     reflection_notes = [notes]

  4. Call log_action:
     agent_name = "Skill Gap Agent"
     action = "Skill gap recommendations finalized"
     employee_id = 1
     project_id = 1
     metadata = {"assessment_id": 1, "identified_gaps": [...]}

  5. Return result dict with all data
```

**DB State After**:
```sql
-- AssessmentAnswers (12 rows updated with scores)
UPDATE AssessmentAnswers SET score = 5.0, evaluated_at = "2026-02-21T14:35:00" WHERE question_id = 1 AND employee_id = 1;
...

-- Assessments (1 row updated)
UPDATE Assessments SET status = "Completed", summary = "Assessment Summary..." WHERE assessment_id = 1;

-- Recommendations (1 row inserted)
INSERT INTO Recommendations VALUES 
(1, 1, 1, 1, "Assessment Summary...", "[\"AWS...\", ...]", "[{\"title\": \"AWS...\"}]", "2026-02-21T14:35:00", "Recommendation validated...");

-- AuditLogs (1 row inserted)
INSERT INTO AuditLogs VALUES (..., "Skill Gap Agent", "Skill gap recommendations finalized", ..., {...});
```

**Session State Update**:
```python
st.session_state["last_recommendation"] = {
  "agent": "Skill Gap Agent",
  "assessment_id": 1,
  "employee_id": 1,
  "project_id": 1,
  "analysis": {...},
  "certifications": [...],
  "courses": [...],
  "reflection_notes": "...",
  "final_recommendation": "..."
}
st.session_state["pending_assessment_id"] = None
```

**UI Display**:
```
Success message: "Assessment submitted and recommendation generated"
Recommendation block displayed below form showing:
- Final recommendation text
- Reflection notes
- Strengths list (2-column layout)
- Improvement areas list (2-column layout)
- Certifications list
- Courses list with clickable links
```

---

#### Step 3: View History

**Trigger**: User clicks on "Recommendation History" tab or selects existing recommendation

**Query Flow**:
```sql
SELECT r.recommendation_id, r.assessment_id, r.employee_id, r.project_id,
       r.recommendation_text, r.certifications, r.courses, r.created_at, r.reflection_notes,
       e.first_name || ' ' || e.last_name AS employee_name,
       p.project_name
FROM Recommendations r
JOIN Employees e ON r.employee_id = e.employee_id
JOIN Projects p ON r.project_id = p.project_id
ORDER BY r.recommendation_id DESC
```

**UI Display**:
```
1. Table of all recommendations
2. Selectbox to choose a recommendation
3. Detail view:
   - recommendation_text (full)
   - reflection_notes
   - Parse certifications JSON
   - Parse courses JSON (with links)
```

---

### 7.3 Filler Question Logic

**Condition**: If generated questions < 10, filler questions are appended.

**Filler Questions** (hardcoded in SkillGapAgent.reflect()):
```python
filler_questions = [
  "Explain your readiness to deliver production outcomes in {tech_stack}.",
  "Describe the last defect triage you handled and your resolution strategy.",
  "How do you prioritize reliability, security, and delivery speed for enterprise systems?"
]
```

**Application**:
```
If questions = 8:
  - Need 2 more to reach 10
  - Add filler_questions[0 % 3] → Q9
  - Add filler_questions[1 % 3] → Q10
```

**Stored**: Filler questions inserted into AssessmentQuestions table with INSERT bulk operation (many=True).

---

### 7.4 Scoring Algorithm

**Formula** (in SkillGapAgent._score_answer()):
```python
words = len(answer.split())
if words >= 80:     return 5.0
elif words >= 50:   return 4.0
elif words >= 30:   return 3.0
elif words >= 15:   return 2.0
elif words > 0:     return 1.0
else:               return 0.0
```

**Rationale**: Encourages thoughtful, detailed answers.

**Score Range**: 0.0 - 5.0 (continuous, not discrete).

**Storage**: Persisted in AssessmentAnswers.score column (REAL type).

---

## 8. Gemini LLM Integration

### 8.1 Configuration

**API Key Source**:
- Environment variable: `GOOGLE_API_KEY`
- Must be set before app starts
- Read in `GeminiClient.__init__()`

**Model**:
- Environment variable: `GEMINI_MODEL`
- Default: `"gemini-1.5-flash"`

**Initialization** (app.py:bootstrap()):
```python
gemini_client = GeminiClient()
register_mcp_tools(registry, gemini_client)
```

**Failure Handling**:
```python
if genai is None or self.api_key is None:
    self._model = None
    # All methods return fallbacks
```

---

### 8.2 Gemini Prompts & Calls

#### Call 1: generate_assessment_questions

**When**: During skill gap assessment generation

**MCP Tool**: `generate_assessment_questions(tech_stack, question_count)`

**Prompt Template**:
```
Generate {count} technical skill assessment questions for this project tech stack:
{tech_stack}

Requirements:
- Questions must evaluate practical experience, debugging approach, architecture, and production readiness.
- Keep each question concise and interview-grade.
- Return valid JSON array only.
```

**Generation Config**:
```python
{
  "temperature": 0.2,
  "max_output_tokens": 2048
}
```

**Expected Response Format**:
```json
[
  "Describe a production issue you resolved using Python. What was root-cause process?",
  "How would you design a resilient module in FastAPI for high traffic?",
  ...
]
```

**Parsing**:
1. Extract JSON array from response
2. If successful and ≥10 items: return first count items
3. If fail: fallback to deterministic questions

---

#### Call 2: analyze_skill_answers

**When**: During assessment evaluation, after answer scoring

**MCP Tool**: `analyze_skill_answers(tech_stack, qa_pairs)`

**Prompt Template**:
```
Analyze this employee assessment response set for project stack: {tech_stack}

Questions and Answers:
{json.dumps(qa_pairs)}

Return valid JSON object with these keys only:
- strengths: list of short points
- skill_gaps: list of short points
- summary: concise paragraph
```

**Expected Response Format**:
```json
{
  "strengths": [
    "Demonstrates strong problem-solving skills",
    "Shows knowledge of distributed system design"
  ],
  "skill_gaps": [
    "Limited experience with cloud deployment",
    "Needs improvement in load testing"
  ],
  "summary": "Skill profile indicates readiness for guided onboarding with focused upskilling..."
}
```

**Parsing**:
1. Extract JSON object
2. Validate keys are present
3. If valid: return dict
4. If fail: fallback analysis

---

#### Call 3: recommend_courses

**When**: After skill analysis complete

**MCP Tool**: `recommend_courses(skill_gaps, tech_stack)`

**Prompt Template**:
```
Recommend enterprise-relevant learning paths for these skill gaps:
{json.dumps(skill_gaps)}

Project stack: {tech_stack}

Return valid JSON object with:
- certifications: list of certifications
- courses: list of objects with keys title, provider, platform, url
```

**Expected Response Format**:
```json
{
  "certifications": [
    "AWS Certified Developer - Associate",
    "Azure Administrator Certified"
  ],
  "courses": [
    {
      "title": "AWS Developer Associate Prep",
      "provider": "Udemy",
      "platform": "Udemy",
      "url": "https://www.udemy.com/..."
    }
  ]
}
```

**Parsing**:
1. Extract JSON object
2. Validate course objects have title, provider, platform
3. Ensure urls are valid (default to Coursera if missing)
4. If fail: fallback courses from hardcoded catalog

---

#### Call 4: reflect_recommendation

**When**: Final refinement of recommendation before storage

**MCP Tool**: `reflect_recommendation(initial_recommendation, tech_stack, qa_pairs)`

**Prompt Template**:
```
Review and improve this recommendation for employee upskilling.

Initial recommendation:
{initial_recommendation}

Tech stack:
{tech_stack}

Assessment QA:
{json.dumps(qa_pairs)}

Self-reflection question:
"Is this recommendation aligned with tech stack and answers?"

Return valid JSON object with keys:
- reflection_notes
- final_recommendation
```

**Expected Response Format**:
```json
{
  "reflection_notes": "Recommendation validated against stack and answer quality. Aligned.",
  "final_recommendation": "[Refined recommendation text]"
}
```

**Parsing**:
1. Extract JSON object
2. Validate both keys are present and non-empty
3. If valid: return dict
4. If fail: return fallback with original recommendation

---

### 8.3 Fallback System

**Fallback Mechanism**: All Gemini calls have deterministic fallbacks.

#### Fallback 1: Question Generation (`_fallback_questions`)

**Trigger**: JSON parsing fails OR too few questions returned

**Logic**:
```python
templates = [
  "Describe a production issue you resolved using {skill}. ...",
  "How would you design a resilient module in {skill} ...",
  "Which performance bottlenecks are common in {skill} ...",
  "Explain your preferred testing strategy for {skill} ...",
  "How do you secure a deployment that includes {skill} ...",
  "Share one optimization you implemented with {skill} ..."
]

skills = tech_stack.split(",") or ["Software Engineering", "Cloud Fundamentals", "Data Fundamentals"]

questions = []
for i in range(question_count):
  skill = skills[i % len(skills)]
  template = templates[i % len(templates)]
  questions.append(template.format(skill=skill))

return questions
```

**Result**: Deterministic, skill-aware questions generated locally.

---

#### Fallback 2: Skill Analysis (`_fallback_analysis`)

**Trigger**: JSON parsing fails OR response invalid

**Logic**:
```python
For each QA pair:
  - Count words in answer
  - If >= 35 words: add to strengths
  - Else: add to weak_skills
  
Return {
  "strengths": ["Demonstrates practical confidence in X..."],
  "skill_gaps": [unique weak skills],
  "summary": "Skill profile indicates readiness..."
}
```

**Result**: Conservative assessment based on answer length.

---

#### Fallback 3: Course Recommendations (`_fallback_courses`)

**Trigger**: JSON parsing fails OR response invalid

**Logic**:
```python
catalog = {
  "aws": {"certification": "...", "course": {...}},
  "azure": {"certification": "...", "course": {...}},
  "python": {...},
  ... (7 total skill/platform mappings)
}

Search tech_stack + skill_gaps for catalog keywords
If match found: Return matching cert + course
Else: Return generic AWS + Azure fallback

Result: Up to 5 certs + 6 courses
```

**Catalog Coverage**: AWS, Azure, Python, Kubernetes, Spark, Salesforce, Java

---

#### Fallback 4: Recommendation Reflection (`reflect_recommendation`)

**Trigger**: JSON parsing fails

**Logic**:
```python
fallback_notes = "Recommendation alignment check complete. Focus areas adjusted to match..."
final = initial_recommendation + "\n\nRefined Action: Prioritize one foundational cert..."

return {
  "reflection_notes": fallback_notes,
  "final_recommendation": final
}
```

**Result**: Original recommendation + suffix appended.

---

### 8.4 Graceful Degradation

**If Gemini API Unavailable**:

1. No exception is raised
2. All public methods return fallback values
3. System continues to operate
4. User sees generated but not refined recommendations

**Temperature**: Constant 0.2 (low variance for determinism)

**Max Tokens**: Constant 2048

**No Retries**: If a Gemini call fails, no retry logic is implemented.

**Error Swallowing**: All exceptions caught and logged silently.

---

## 9. Audit & Logging System

### 9.1 AuditLogs Table Design

```sql
CREATE TABLE AuditLogs (
  log_id INTEGER PRIMARY KEY AUTOINCREMENT,
  agent_name TEXT NOT NULL,
  action TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  employee_id INTEGER,
  project_id INTEGER,
  metadata TEXT  -- JSON
);
```

---

### 9.2 Logging Mechanism

**Central Function**: `utils/logger.py:log_action()`

```python
def log_action(
  db_write,           # MCP tool callable
  agent_name,         # e.g., "HR Agent"
  action,             # e.g., "Employee created"
  employee_id=None,   # Context
  project_id=None,    # Context
  metadata=None       # Extra data
) -> int:             # Returns log_id
```

**How It Works**:
1. Serialize metadata dict to JSON string
2. Get current UTC timestamp (ISO format)
3. Call MCP `db_write` tool with INSERT query
4. Return lastrowid (log_id)

**All Calls via MCP**: Never called directly; always through MCP registry.

---

### 9.3 Logged Events

#### HR Agent

**Event 1**: Employee Created
```
agent_name: "HR Agent"
action: "Employee created"
employee_id: [created employee id]
metadata: {"department": X, "role": Y}
```

**Event 2**: Onboarding Status Updated
```
agent_name: "HR Agent"
action: "Onboarding status updated"
employee_id: [emp id]
metadata: {"status": "In Progress"} or {"status": "Active"}
```

**Event 3**: Project Assigned
```
agent_name: "HR Agent"
action: "Project assigned"
employee_id: [emp id]
project_id: [proj id]
metadata: {"role_on_project": "API Developer"}
```

---

#### IT Agent

**Event**: IT Provisioning Completed
```
agent_name: "IT Agent"
action: "IT provisioning completed"
employee_id: [emp id]
project_id: [optional proj id]
metadata: {
  "asset_tag": "LAP-0001",
  "vpn_profile": "CORP-STD",
  "email_group": "all-employees",
  "sso_status": "Enabled"
}
```

---

#### Training Agent

**Event**: Training Plan Assigned
```
agent_name: "Training Agent"
action: "Training plan assigned"
employee_id: [emp id]
project_id: [optional proj id]
metadata: {
  "modules": ["Code of Conduct...", "Information Security...", ...]
}
```

---

#### Skill Gap Agent

**Event 1**: Skill Gap Assessment Generated
```
agent_name: "Skill Gap Agent"
action: "Skill gap assessment generated"
employee_id: [emp id]
project_id: [proj id]
metadata: {
  "assessment_id": 1,
  "question_count": 12
}
```

**Event 2**: Skill Gap Recommendations Finalized
```
agent_name: "Skill Gap Agent"
action: "Skill gap recommendations finalized"
employee_id: [emp id]
project_id: [proj id]
metadata: {
  "assessment_id": 1,
  "identified_gaps": ["Cloud deployment", "Load testing"]
}
```

---

### 9.4 Audit Log Querying

#### Dashboard View
```sql
SELECT timestamp, agent_name, action, employee_id, project_id
FROM AuditLogs
ORDER BY log_id DESC
LIMIT 8
```

#### Audit Logs Tab
```sql
SELECT log_id, timestamp, agent_name, action, employee_id, project_id, metadata
FROM AuditLogs
ORDER BY log_id DESC

-- With filter by agent:
WHERE agent_name = [selected_agent]
```

#### Audit Compliance
- **Immutable**: Once logged, logs cannot be modified (no UPDATE on AuditLogs)
- **Centralized**: All logging goes through single log_action() function
- **Contextual**: employee_id, project_id, metadata capture business context
- **Timestamped**: All logs have UTC ISO timestamp

---

### 9.5 No Centralized Logging Configuration

**Note**: No centralized logger config (no Python logging module).

- Logging is business-event-focused, not system-focused
- No DEBUG, INFO, WARNING levels
- No log file rotation
- No external log aggregation

Each log_action() call is an explicit business event.

---

## 10. End-to-End Flow Summary

### 10.1 Complete Employee Onboarding Journey

```
┌─────────────────────────────────────────────────────────────────┐
│ WEEK 1: EMPLOYEE CREATION & INITIAL ONBOARDING                 │
└─────────────────────────────────────────────────────────────────┘

Day 1 - Employee Created
├─ HR Admin logs in via Streamlit UI
├─ Navigates to "Employees" tab
├─ Fills "Add Employee" form (name, email, dept, role, joining_date)
├─ Clicks "Create Employee"
│  ├─ Form validates all fields non-empty
│  ├─ Email regex validation
│  ├─ orchestrator.hr_agent.execute({"action": "create_employee", ...})
│  │  ├─ INSERT Employees (status="Pending")
│  │  ├─ Call log_action → INSERT AuditLogs
│  │  └─ Call send_email (simulated)
│  ├─ Display success message with employee_id
│  ├─ Rerun to refresh list
│  └─ New employee appears in Employees table
└─ [Employees table updated]


Day 2-3 - End-to-End Onboarding
├─ HR Admin navigates to "Employees" tab
├─ Selects newly created employee
├─ Clicks "Run End-to-End Onboarding"
│  ├─ orchestrator.run_onboarding(employee_id):
│  │  ├─ HRAgent: update_onboarding("In Progress")
│  │  │  └─ UPDATE Employees.status = "In Progress"
│  │  ├─ ITAgent: provision_access(employee_id)
│  │  │  ├─ Generate asset_tag "LAP-0001"
│  │  │  ├─ Create account_pack
│  │  │  └─ Call log_action
│  │  ├─ TrainingAgent: assign_training(employee_id)
│  │  │  ├─ Build modules based on role ("engineer" → add SDLC, Agile modules)
│  │  │  └─ Call log_action
│  │  └─ HRAgent: update_onboarding("Active")
│  │     └─ UPDATE Employees.status = "Active"
│  ├─ Display success with IT + Training results
│  └─ Rerun
└─ [Employees.status = "Active", AuditLogs updated 4x, 0 assessments]


┌─────────────────────────────────────────────────────────────────┐
│ WEEK 2-3: PROJECT ASSIGNMENT & SKILL ASSESSMENT                 │
└─────────────────────────────────────────────────────────────────┘

Day 8 - Project Assignment Triggers Assessment Generation
├─ Project Manager logs in
├─ Navigates to "Assign Project" tab
├─ Selects employee, project, role ("API Developer")
├─ Clicks "Assign Project and Trigger Skill Gap Assessment"
│  ├─ orchestrator.assign_project_and_trigger_skill_gap(emp_id, proj_id, role):
│  │  ├─ HRAgent: assign_project action
│  │  │  ├─ Fetch employee and project validation
│  │  │  ├─ UPDATE EmployeeProjects: mark previous as "Completed"
│  │  │  ├─ INSERT EmployeeProjects (status="Active")
│  │  │  ├─ Call log_action
│  │  │  └─ Call send_email
│  │  └─ SkillGapAgent: generate_assessment action
│  │     ├─ Call MCP "generate_assessment_questions" (Gemini or fallback)
│  │     ├─ INSERT Assessments (status="Pending")
│  │     ├─ INSERT AssessmentQuestions (12+)
│  │     └─ Call log_action
│  ├─ Store assessment_id in session state
│  ├─ Navigate user to "Skill Gap Assessment" tab
│  └─ Display assessment form with 12+ questions
└─ [EmployeeProjects updated, Assessments/AssessmentQuestions inserted]


Day 9-10 - Employee Completes Assessment
├─ Employee logs in
├─ Navigates to "Skill Gap Assessment" tab
├─ Reads 12 skill questions (auto-selected pending assessment)
├─ Types answers for each question in text areas
├─ Clicks "Submit Assessment and Generate Recommendations"
│  ├─ Form validates all answers non-empty
│  ├─ orchestrator.submit_assessment_answers(assessment_id, answers_dict):
│  │  └─ SkillGapAgent: evaluate_assessment action
│  │     ├─ Fetch QA pairs from DB
│  │     ├─ Score each answer (word count → 0-5 scale)
│  │     ├─ UPDATE AssessmentAnswers with scores
│  │     ├─ Call MCP "analyze_skill_answers" (Gemini)
│  │     │  └─ Returns {strengths, skill_gaps, summary}
│  │     ├─ Call MCP "recommend_courses" (Gemini)
│  │     │  └─ Returns {certifications, courses}
│  │     ├─ Compose draft recommendation text
│  │     ├─ Call MCP "reflect_recommendation" (Gemini)
│  │     │  └─ Returns {reflection_notes, final_recommendation}
│  │     ├─ UPDATE Assessments (status="Completed")
│  │     ├─ INSERT Recommendations (with JSON certs + courses)
│  │     ├─ Call log_action
│  │     └─ Return complete result dict
│  ├─ Store recommendation in session state
│  ├─ Display recommendation block
│  └─ Show strengths, gaps, certs, courses with links
└─ [AssessmentAnswers scored, Assessments/Recommendations inserted]


┌─────────────────────────────────────────────────────────────────┐
│ ONGOING: AUDIT & RECOMMENDATION HISTORY                          │
└─────────────────────────────────────────────────────────────────┘

Throughout
├─ Dashboard tab
│  ├─ Shows 4 metrics (employees, projects, active assignments, pending assessments)
│  └─ Displays last 8 audit log entries
├─ Audit Logs tab
│  ├─ Shows all historical audit entries
│  ├─ Filterable by agent
│  └─ Includes metadata (JSON)
└─ Skill Gap Assessment → History tab
   ├─ Shows all past recommendations
   ├─ Allows inspection of recommendation detail
   └─ Shows certs, courses, reflection notes
```

---

### 10.2 Data Flow Diagram

```
┌─────────────────┐
│  Streamlit UI   │
│  (React-like)   │
└────────┬────────┘
         │ User Action
         ▼
┌─────────────────────────────┐
│  Form/Button Handler        │
│  (render_* function)        │
└────────┬────────────────────┘
         │ Validates input
         │ Collects form data
         ▼
┌─────────────────────────────┐
│  AgentOrchestrator          │
│  OR Agent directly          │
└────────┬────────────────────┘
         │ execute(context)
         ▼
┌─────────────────────────────┐
│  Agent.plan()               │
│  (Validate & enrich)        │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Agent.use_tools()          │
│  (Call MCP tools)           │
└────────┬────────────────────┘
         │
    ┌────┴───────┐
    │             │
    ▼             ▼
┌─────────┐  ┌──────────────┐
│ DB Ops  │  │ Gemini Calls │
│ (MCP)   │  │ (MCP)        │
└────┬────┘  └──────┬───────┘
     │              │
     └──────┬───────┘
            ▼
     [External State]
     - SQLite DB
     - Google Gemini
     
     ┌─────────────────┐
     │ Returns results │
     └────────┬────────┘
              │
              ▼
┌─────────────────────────────┐
│  Agent.reflect()            │
│  (Post-process)             │
│  (Log action)               │
│  (Add agent name)           │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Return result to UI        │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Update session state       │
│  (if needed)                │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  st.rerun() or display      │
│  result                     │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Streamlit UI refreshes     │
│  (renders new page state)   │
└─────────────────────────────┘
```

---

### 10.3 Database State Evolution Example

**Initial State** (after seed_data):
```
Employees: 10 rows
Projects: 5 rows
EmployeeProjects: 5 rows (assignments)
Skills: 22 rows
Assessments: 0 rows
AssessmentQuestions: 0 rows
AssessmentAnswers: 0 rows
Recommendations: 0 rows
AuditLogs: 0 rows
```

**After Employee 11 Created**:
```
Employees: 11 rows (new person)
AuditLogs: 1 row (employee created)
```

**After Create Employee Success + End-to-End Onboarding**:
```
Employees: 11 rows (status updated to "Active")
AuditLogs: 5 rows (
  1. Employee created
  2. Onboarding status updated to "In Progress"
  3. IT provisioning completed
  4. Training plan assigned
  5. Onboarding status updated to "Active"
)
```

**After Project Assignment**:
```
EmployeeProjects: 6 rows (new assignment, previous 5 unchanged or marked "Completed")
Assessments: 1 row (status="Pending")
AssessmentQuestions: 12+ rows
AuditLogs: 7 rows (
  6. Project assigned
  7. Skill gap assessment generated
)
```

**After Assessment Submission**:
```
AssessmentAnswers: 12 rows (with scores)
Assessments: 1 row (status="Completed")
Recommendations: 1 row (full recommendation with JSON)
AuditLogs: 8 rows (
  8. Skill gap recommendations finalized
)
```

---

### 10.4 Session State Evolution

**Initial**:
```python
{
  "authenticated": False,
  "current_user": "",
  "current_page": "Dashboard",
  "pending_assessment_id": None,
  "last_recommendation": None
}
```

**After Login**:
```python
{
  "authenticated": True,
  "current_user": "admin",
  "current_page": "Dashboard",
  "pending_assessment_id": None,
  "last_recommendation": None
}
```

**After Project Assignment & Assessment Created**:
```python
{
  "authenticated": True,
  "current_user": "admin",
  "current_page": "Skill Gap Assessment",  # ← auto-navigated
  "pending_assessment_id": 1,               # ← stored for default selectbox
  "last_recommendation": None
}
```

**After Assessment Submitted**:
```python
{
  "authenticated": True,
  "current_user": "admin",
  "current_page": "Skill Gap Assessment",
  "pending_assessment_id": None,             # ← cleared
  "last_recommendation": {                   # ← full recommendation dict
    "agent": "Skill Gap Agent",
    "assessment_id": 1,
    "analysis": {...},
    "certifications": [...],
    "courses": [...],
    "reflection_notes": "...",
    "final_recommendation": "..."
  }
}
```

---

## 11. Special Implementation Notes

### 11.1 Session State Quirks

**Streamlit Reruns**:
- Every user interaction triggers a full script rerun
- Session state persists across reruns (key strategy)
- `@st.cache_resource` used for bootstrap (run once)
- Forms auto-clear on submit via `clear_on_submit=True`

**Prevent Auth Loop**:
- If not authenticated, render_auth_gate() returns False
- main() returns early if auth gate fails
- User doesn't see rest of UI

---

### 11.2 Email Simulation

**Email Tool** (app.py:register_mcp_tools):
```python
def send_email(recipient: str, subject: str, body: str) -> dict[str, str]:
  return {
    "status": "sent",
    "recipient": recipient,
    "subject": subject,
    "body": body
  }
```

**No SMTP Integration**: Emails are not actually sent; just logged in result dict.

**Called By**:
- HR Agent (when employee created, onboarding updated, project assigned)
- IT Agent (when provisioning completed)
- Training Agent (when training assigned)

---

### 11.3 Foreign Key Constraints

**Enabled**: `PRAGMA foreign_keys = ON` in get_connection()

**Implications**:
- Cannot insert Assessments with non-existent employee_id or project_id
- Cannot delete Employees with active assignments
- Referential integrity enforced

---

### 11.4 Column Truncation

**Text Sanitization** (app.py):
```python
def sanitize_text(value: str, max_len: int = 2000) -> str:
  normalized = " ".join((value or "").strip().split())
  return normalized[:max_len]
```

**Applied By**:
- HR Agent: truncates names (50), email (120), dept (80), role (80)
- IT Agent: no truncation (asset tags are auto-generated)
- Training Agent: no truncation (modules are fixed)
- App UI: applied before agent calls

---

## 12. Known Limitations & Current Behavior

### 12.1 What IS Implemented

✅ Employee CRUD (create only; no edit/delete in UI)
✅ Project display (read-only; seed data only)
✅ End-to-end onboarding workflow (4-phase)
✅ Project assignment & skill assessment generation
✅ Multi-phase skill assessment (generate → answer → evaluate → recommend)
✅ Gemini integration with fallbacks
✅ Audit logging for all agent actions
✅ Recommendation history with reflection
✅ Streamlit UI with 6 tabs
✅ Session-based authentication (hardcoded credentials)
✅ MCP tool registry pattern

### 12.2 What IS NOT Implemented

❌ Employee edit/delete functionality
❌ Project creation/edit (seed-only)
❌ Database export/analytics queries
❌ Real email sending (simulated)
❌ Multi-user authentication (hardcoded dict)
❌ Course enrollment tracking
❌ Performance tracking post-assessment
❌ Recommendation versioning (overwrite only)
❌ Agent-to-agent communication (only orchestrator)
❌ Caching of Gemini responses
❌ Retry logic for API failures
❌ Partial form completion recovery
❌ Streaming responses from Gemini

### 12.3 Database Persistence

- **Local Development**: SQLite file `onboarding.db` in project root
- **Streamlit Cloud**: Persists on server filesystem (free tier has limited persistence across restarts)
- **No Migration System**: Schema is created on first run; no migrations framework

---

## 13. Configuration & Environment

**Required Environment Variables**:
- `GOOGLE_API_KEY` (for Gemini; if missing, fallbacks used)
- `GEMINI_MODEL` (optional; defaults to "gemini-1.5-flash")

**Optional**:
- `DATABASE_URL` (not currently used; hardcoded to local SQLite)

**Streamlit Config** (`.streamlit/config.toml`):
```toml
[theme]
primaryColor = "#FF6B35"

[client]
showErrorDetails = true

[server]
port = 8501
headless = true
```

---

## 14.Appendix: Seed Data Summary

**10 Employees** (departments: Engineering, Cybersecurity, Delivery, QA, Support)

**5 Projects** (stacks: Python/FastAPI/AWS, Spark/Databricks, Salesforce, Java/K8s, SIEM/Azure)

**5 Assignments** (active employee-to-project links)

**22 Skills** (employee skill proficiencies 1-5)

---

## 15. Document Version & Status

**Version**: 1.0  
**Date**: March 2, 2026  
**Status**: Complete  
**Scope**: As-implemented behavior only (no speculation)  
**Accuracy**: Reflects actual code (lines referenced where applicable)

**Generated from codebase files**:
- app.py (834 lines)
- agents/* (4 agents, ~800 lines)
- db/* (database layer, seed data)
- mcp/registry.py (40 lines)
- utils/* (Gemini client, logger)

---

**END OF TECHNICAL DOCUMENTATION**
