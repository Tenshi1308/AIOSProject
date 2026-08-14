# AGENTS.md

## Project

AIOS Plugin Platform

AIOS is a standalone AI platform (multi-tenant SaaS) hosted by Ekasa.
Each client company logs in to its own AIOS workspace; nothing needs
to be installed or embedded in the client's own application.

The goal is to provide specialized AI capabilities without requiring
the client to modify or rebuild their existing application, database,
authentication, or business logic.

AIOS must adapt to the client's existing system rather than forcing
the client system to adapt to AIOS.

In this context, "plugin" means AIOS adapts to the client's existing
system (especially its database) rather than being embedded in the
client's application.

This project is a prototype for validating the product concept and
technical architecture. Prioritize a functional, demonstrable,
end-to-end prototype over production-level complexity.

The product is measured against four core principles:

- **Cost Efficient** — minimize operating cost: one shared local model
  for all branches/workers, keep models small, avoid repeated expensive
  computation through short-TTL caching, and never duplicate client
  business data in the AIOS Internal Database.
- **User Friendly** — the client should not deal with technical details;
  interactions use natural language and guided onboarding, and internal
  steps (adapters, schema analysis, mapping) remain hidden.
- **Plug and Go** — adapt to each client's existing system with minimal
  setup effort; clients without a database get one provided by Ekasa.
- **Fast** — database adaptation happens once at integration/setup (not
  per request), repeated queries reuse cached results, and responses are
  quick.

---

## Core Concept

AIOS consists of:

- AIOS Interface
- AI Manager
- Plugin Manager
- Specialized Workers
- Tools
- Database Adapter
- Schema Extraction
- AI Schema Analyzer
- Semantic Mapping
- Canonical Data Model
- AIOS Internal Database
- AIOS Data Layer
- RAG / Document Pipeline
- Local LLM

High-level architecture:

User
  ↓
AIOS Interface
  ↓
User selects capability
  ↓
AI Manager
  ↓
Selected Worker
  ↓
Tools / Data / RAG
  ↓
Response


Client integration architecture:

Client Database
  ↓
Database Adapter
  ↓
Schema Extraction
  ↓
AI Schema Analyzer
  ↓
Schema Understanding
  ↓
Semantic Mapping
  ↓
Canonical Data Model
  ↓
AIOS Data Layer
  ↓
Workers


AIOS Internal Database architecture:

AIOS Internal Database
  │
  ├── Client Metadata
  ├── Connection Metadata
  ├── Schema Metadata
  ├── Semantic Mapping
  ├── Mapping Version / Confidence
  ├── Plugin Configuration
  └── Worker Configuration


The AIOS Internal Database stores AIOS metadata, configuration,
mapping, and state.

It MUST NOT become a copy of the client's business database.

Business data remains in the Client Database.


Local AI architecture:

AI Manager / Workers / AI Schema Analyzer
  ↓
Ollama
  ↓
Local LLM

---

## User Interaction Model

AIOS is NOT a single general-purpose chatbot.

The user first selects a specific capability, domain, or worker from
the AIOS interface.

Example:

User
  ↓
Register / Login (AIOS SaaS, per company)
  ↓
Payment (payment gateway, automatic activation)
  ↓
Home — 9 branches around the AIOS hub
  ↓
Select branch
  ↓
AI Manager (primary agent of the branch)
  ↓
Selected Worker (sub-agent)
  ↓
Worker Workspace
  ↓
User interacts with the AI Manager / Worker

Before the client can use an AI Manager, its company database must be
connected (onboarding gate). Connecting the database triggers database
adaptation (see Database Adaptation Pipeline) and the client validates
the resulting mapping in the UI before use.

AIOS is viewed as an organization with 9 branches (ERP modules). Each
branch is led by one AI Manager who manages and coordinates the Worker
AI (job roles) of that branch.

Example branches:

- Strategic and Operational Planning
- Finance
- Human Resource
- Logistic Management
- Maintenance Management
- Sales and Distribution
- Quality Management
- Material Management
- Manufacturing

The exact worker list may evolve during development.

The user should not need to understand internal implementation details
such as database adapters, schema analyzers, canonical models, vector
databases, internal databases, or internal tools.

---

## AI Manager

AIOS is viewed as an organization with 9 branches (ERP modules). Each
branch is led by one AI Manager.

Example branches:

- Strategic and Operational Planning
- Finance
- Human Resource
- Logistic Management
- Maintenance Management
- Sales and Distribution
- Quality Management
- Material Management
- Manufacturing

The exact list of branches may evolve during development.

Each AI Manager is the central orchestrator for its branch.

Each AI Manager is responsible for managing and coordinating the
workers (Worker AI / job roles) of its branch and their required
capabilities.

AI Manager may:

- manage worker execution
- coordinate tools
- manage context
- communicate with the Local LLM
- coordinate multiple capabilities when required
- manage the overall AIOS workflow

AI Manager does NOT replace specialized workers.

Specialized workers remain responsible for domain-specific tasks.

The user selects the capability first. AI Manager then manages the
selected worker.

Do not design the system as:

User → AI Manager → AI Manager guesses the worker

Prefer:

User → Interface → Select Capability → AI Manager → Selected Worker

Each AI Manager acts as the primary agent of its branch: it talks to
the user and delegates domain-specific tasks to its workers (sub-agents).
The delegation process is transparent — the interface may show which
worker is being consulted while the AI Manager composes the response.

---

## Specialized Workers

Workers are domain-specific AI components (Worker AI) that mimic
specific job roles within a branch. Each branch is led by an AI Manager
who manages and coordinates the Worker AI of that branch.

Each worker should have a clear responsibility and should not contain
unrelated business logic.

Example branches and worker job roles:

Strategic and Operational Planning (AI Manager Strategic and Operational Planning):
- BI Analyst
- Report Developer
- Data Steward

Finance (AI Manager Finance):
- Finance Staff
- Financial Analyst
- Budgeting Staff
- Treasurer
- CFO

Human Resource (AI Manager HR):
- HR Staff
- Recruiter
- Payroll Officer
- Training Specialist
- HR Manager

Logistic Management (AI Manager Logistic Management):
- Logistics Coordinator
- Shipping & Receiving Clerk
- Fleet Manager

Maintenance Management (AI Manager Maintenance Management):
- Maintenance Planner
- Reliability Engineer
- Maintenance Technician

Sales and Distribution (AI Manager Sales):
- Sales Representative
- Customer Service
- Sales Data Analyst
- Marketing Specialist

Quality Management (AI Manager Quality Management):
- Quality Inspector
- Quality Engineer
- Quality Auditor
- Quality Control Officer

Material Management (AI Manager Material Management):
- Procurement Staff
- Senior Procurement Specialist
- Purchasing Officer
- Inventory Control Manager
- Warehouse Inventory Manager
- Retail Inventory Manager

Manufacturing (AI Manager Manufacturing):
- Production Planner
- Production Scheduler
- Production Supervisor

The exact worker list may evolve during development.

Workers may use tools and data through AIOS abstractions.

Workers should NOT directly depend on a client's specific database
schema.

Workers should operate through AIOS Data Layer / Canonical Data Model
and Database Adapter abstractions.

### Data Access Agent

The Data Access Agent is a specialized worker shared per tenant (not
per branch). It is responsible for:

- connecting to and understanding the client's database schema
  (database adaptation)
- building and persisting the semantic mapping in the AIOS Internal
  Database, including mapping version, confidence, and validation status
- re-adapting when the client schema changes
- providing actual business data to other workers through the AIOS Data
  Layer / Canonical Data Model, keeping the Client Database as the
  source of truth

All AI Managers of a tenant use the same Data Access Agent.

### Memory Agent

Each AI Manager has a Memory Agent (one per branch) that summarizes past
conversations with the client. Conversation messages and summaries are
stored in the AIOS Internal Database, tagged per branch, so the AI
Manager retains context across the chat session.

---

## Plugin Architecture

AIOS is designed as a plugin in the sense that it ADAPTS to the
client's existing system without requiring changes to it. The client's
business application and database remain untouched.

Deployment model: AIOS is a standalone SaaS with its own domain and
its own login (see Authentication & Roles). It is not embedded in the
client's application.

AIOS must NOT require the client to:

- replace its existing application
- redesign its database
- rename its tables
- rename its columns
- replace its authentication system
- migrate its business logic to AIOS

Because AIOS is a standalone SaaS, it has its own authentication layer
(login per company, with roles). This is an explicit requirement of the
SaaS deployment model and does not replace the client's own
authentication system, which continues to serve the client's own
application.

The prototype should demonstrate that AIOS can adapt to different
existing systems with minimal modification to the client's system.

---

## Authentication & Roles

AIOS is a multi-tenant SaaS: each company logs in to its own workspace,
and all company data, metadata, and mappings are isolated per company
(tenant). Data, conversations, and mappings of Client A MUST NOT be
accessed by Client B.

Before logging in, a client must register an account. After login, the
client completes payment (via a payment gateway) before using AIOS
capabilities; activation is automatic once payment succeeds.

Roles:

- Client — a company that uses AIOS (single role; no separate user/admin
  within a company). Registers, logs in, pays, connects its own database,
  selects a branch, uses AI capabilities, and validates its own mapping.
- Ekasa Developer — internal Ekasa who only monitors usage: input and
  consumed tokens per company, with drill-down per branch and per worker.
  Does not access client business data or conversations.

The Ekasa Developer view provides usage monitoring per company (input
and consumed tokens) with drill-down per branch and per worker, so
Ekasa can see which branches each company actually uses.

---

## Plugin Manager

Plugin Manager manages AIOS plugins and their capabilities.

It should support a modular architecture where workers and capabilities
can be added without redesigning the entire AIOS core.

Avoid tightly coupling workers to the AI Manager implementation.

Prefer clear interfaces/contracts between:

- AI Manager
- Plugin Manager
- Workers
- Tools
- Data Layer
- Internal Database

---

## Database Adaptation

Database adaptation is one of the core features of AIOS.

Different clients may have completely different database structures.

Differences may include:

- table names
- column names
- column types
- relationships
- table organization
- naming conventions
- data representation
- database engines
- semantic meaning of fields
- available business concepts

Do NOT assume that database adaptation only means mapping different
column names.

Example:

Client A:

products
- product_id
- product_name
- stock

Client B:

barang
- kode
- nama
- tersedia

Client C may use a completely different structure and naming scheme.

Some clients may not have concepts such as stock, category, supplier,
or warehouse at all.

AIOS MUST NOT assume that every client provides the same business
concepts or fields.

AIOS must use AI to analyze and understand the client's schema
semantically.

The system should adapt to the capabilities and data actually
available in each client database.

---

## Database Adaptation Pipeline

Database adaptation should primarily happen during AIOS integration
or setup, not from scratch for every user query.

Preferred conceptual flow:

Client Database
  ↓
Database Adapter
  ↓
Schema Extraction
  ↓
AI Schema Analyzer
  ↓
Schema Understanding
  ↓
Semantic Mapping
  ↓
Canonical Data Model
  ↓
AIOS Data Layer
  ↓
Workers


The AI Schema Analyzer should analyze more than names.

It may consider:

- tables
- columns
- data types
- relationships
- constraints
- sample values
- naming patterns
- semantic meaning
- available business concepts

The system should produce a reusable understanding/mapping of the
client database.

The mapping should be stored in AIOS Internal Database when persistence
is required.

Do not repeatedly perform complete schema analysis for every normal
user request unless explicitly required.

The client validates the resulting mapping in the UI: the mapping is
shown with its confidence, the client confirms correct mappings and may
edit mappings manually. Low-confidence mappings are flagged for
confirmation.

If the client schema changes, AIOS should be able to detect, re-analyze,
or update the affected mapping. When a schema change is detected, AIOS
re-adapts automatically and shows the client a pop-up explaining that
the schema changed, requesting confirmation and allowing manual edits.

---

## AIOS Internal Database

AIOS has an Internal Database for persistent metadata, configuration,
mapping, and state required by the AIOS platform.

The Internal Database is NOT a replacement for the Client Database.

The Internal Database MUST NOT store a full copy of the client's
business data.

The Client Database remains the source of truth for client business data.

The Internal Database may store:

- client metadata
- database connection metadata
- schema metadata
- schema extraction results when useful
- semantic mappings
- canonical mapping information
- mapping version
- mapping confidence
- mapping validation status
- plugin metadata
- worker configuration
- tool configuration
- AIOS integration metadata
- usage / token metering data (per company, branch, worker)

Concept:

AIOS Internal Database
  │
  ├── Client Metadata
  ├── Connection Metadata
  ├── Schema Metadata
  ├── Semantic Mapping
  ├── Mapping Version / Confidence
  ├── Plugin Configuration
  └── Worker Configuration

Client Database
  │
  └── Actual Business Data


The Internal Database is used to allow AIOS to persist knowledge about
each client integration.

Example:

Client A
  ├── Schema Metadata
  ├── Schema Mapping
  └── Worker / Plugin Configuration

Client B
  ├── Schema Metadata
  ├── Schema Mapping
  └── Worker / Plugin Configuration

Client-specific metadata and mappings MUST remain logically isolated.

A mapping belonging to Client A MUST NOT be used to access Client B.

The Internal Database should support schema mapping persistence so that
AIOS does not need to perform complete schema analysis again after
every restart or normal request.

If the client schema changes, the affected metadata and mappings must
be updated accordingly.

Do not create unnecessary tables or entities.

The Internal Database schema must be derived from actual functional
requirements.

Do not store client business records in the Internal Database merely
to simplify worker implementation.

---

## Database Adapter

Database Adapter is the abstraction layer between AIOS and the client's
database.

Its responsibility is to provide a consistent way for AIOS to interact
with different database systems.

Do not allow workers to directly depend on client-specific SQL schemas.

Prefer:

Worker
  ↓
AIOS Data Layer / Canonical Model
  ↓
Database Adapter
  ↓
Client Database

The adapter should hide database-specific implementation details from
workers whenever practical.

The Database Adapter accesses business data from the Client Database.

The AIOS Internal Database is used for AIOS metadata, mapping,
configuration, and state, not as the primary source of client business
data.

---

## Canonical Data Model

The Canonical Data Model provides a semantic representation used
internally by AIOS.

It is an abstraction layer, NOT a copy of the client's database.

Its purpose is to allow workers to work with concepts rather than
client-specific table and column names.

Example:

Client-specific data:

barang.nama
barang.tersedia

may be understood internally as:

Product.name
Product.stock

Another client may have completely different structures but map to the
same canonical concepts.

Canonical concepts are NOT mandatory fields that every client must have.

Example:

Product
- name
- price
- stock (optional)
- category (optional)
- supplier (optional)

If a client does not provide a particular concept, AIOS MUST NOT invent
or fabricate the missing data.

Workers must be aware of which concepts are actually available for the
current client.

The Canonical Data Model should remain flexible and capability-aware.

Workers should primarily operate through the canonical model or AIOS
data abstractions.

Workers must NOT directly depend on raw client database structures.

---

## RAG / Document Pipeline

RAG is conceptually separate from database schema adaptation.

Structured client data:

Client Database
  ↓
Database Adapter
  ↓
Schema Analysis
  ↓
Canonical Data Model

Unstructured documents:

PDF / Documents
  ↓
Parser
  ↓
Chunking
  ↓
Embedding
  ↓
Vector Store
  ↓
Retrieval
  ↓
Document Worker

Do not mix the database adaptation pipeline and RAG pipeline into one
conceptual process.

A worker may use both structured data and documents when a task requires
both.

> Prototype scope: RAG / document handling is deferred in the prototype.
> The prototype focuses on structured data from the Client Database;
> document handling (RAG) may be added in a later phase.

---

## Local AI

The prototype uses Ollama as the LLM runtime. In the SaaS deployment,
Ollama runs on the Ekasa server, which means company data flows to the
Ekasa server. This is an accepted trade-off for the prototype; a future
phase may offer per-company LLM deployment options.

Use Ollama as the model runtime unless a project requirement explicitly
changes this.

The prototype should prioritize:

- simple models
- reasonable performance
- easy setup
- demonstrability

Do NOT over-engineer the AI model.

This is a prototype intended to validate the concept. Production-level
model optimization is outside the initial scope.

---

## Interface

The interface should not be designed as one generic chatbot.

The interface should expose distinct capabilities/workspaces.

Home screen: the 9 branches (ERP modules) are arranged around a central
"AIOS" hub. Hovering near a branch shows a preview of the workers in
that branch (informational only — workers are not clickable from the
preview). Clicking a branch opens the chat view for that branch.

Chat view (after selecting a branch):

- Left panel: placeholder quick-access boxes (e.g., revenue, growth);
  content may be added later.
- Right side: chat with the branch's AI Manager (the primary agent),
  including suggestion boxes with example questions.

The AI Manager acts as the primary agent of its branch: it delegates
to its specialized workers (sub-agents) and the delegation process is
transparent to the user.

The interface should make the purpose of each branch and worker clear.

Internal implementation details should remain hidden unless needed for
administration/debugging.

The Ekasa Developer view provides usage monitoring per company (input
and consumed tokens) with drill-down per branch and per worker.

---

## Prototype Scope

The prototype should work as completely as reasonably possible.

Prioritize an end-to-end working flow over isolated demonstrations.

A successful prototype should demonstrate:

1. AIOS can be integrated as a plugin.
2. User can select a specific AI capability.
3. AI Manager can manage the selected worker.
4. Worker can execute domain-specific tasks.
5. AIOS can use a local LLM through Ollama.
6. AIOS can connect to a client database through an adapter.
7. AI can analyze a client's database schema.
8. Different database structures can be mapped to a canonical model.
9. Schema mappings can be persisted in the AIOS Internal Database.
10. Multiple client configurations can be managed independently.
11. Workers can operate through the canonical model rather than raw
    client schemas.
12. AIOS can retrieve client business data from the Client Database
    without duplicating it into the Internal Database.
13. AIOS can handle document-based knowledge through RAG. (Deferred in
    the prototype; the prototype focuses on structured data.)
14. Multiple client database structures can be demonstrated.
15. The complete flow can be demonstrated through the interface.
16. Users can log in per company (multi-tenant SaaS) with role-based
    access (Client and Ekasa Developer roles).
17. Ekasa developers can monitor usage (tokens) per company with
    drill-down per branch and worker.

Prefer a smaller number of fully working workers over many incomplete
workers.

---

## Development Priority

Prioritize implementation in this general order:

1. Requirements and architecture
2. AIOS Core
3. AI Manager
4. Plugin Manager
5. Worker architecture
6. Internal Database design
7. Internal Database implementation
8. Local LLM integration
9. Database Adapter
10. Schema Extraction
11. AI Schema Analyzer
12. Semantic Mapping
13. Canonical Data Model
14. AIOS Data Layer
15. Worker-to-data integration
16. RAG / Document Worker (deferred; add later if RAG is brought back)
17. Interface
18. Multi-client simulation
19. End-to-end testing
20. Optimization and documentation

Do not skip architectural dependencies simply to reach the UI faster.

Do not implement Internal Database entities before their purpose and
requirements are established.

---

## Working Method

BEFORE starting a new stage, new task, or significant change, always
ask the intern for approval first.

Wait for explicit approval before executing.

Do not assume previous instructions are approval to start the next stage.

Work incrementally.

Do not implement the entire platform in one step.

Complete one stage first, report the result, and wait for approval before
moving to the next stage.

When offering to continue to the next step (for example "Mau lanjut ke
langkah berikutnya?"), always explain where the continuation leads: what
will be done, what the outcome will be, and which direction the flow goes.
Do not offer a continuation without clarifying its destination.

When analyzing or planning, do not modify project files unless the user
has explicitly authorized implementation.

---

## Change Discipline

When implementing an approved task:

- modify only what is necessary
- avoid unrelated refactoring
- do not redesign the architecture without approval
- do not introduce unnecessary dependencies
- preserve existing working functionality
- explain significant architectural decisions briefly

If a requested change conflicts with the current architecture, stop and
explain the conflict before making a major architectural change.

---

## Flowchart / Documentation Rules

Flowcharts describe the architecture and logic of AIOS.

When creating or editing `.drawio` files:

- focus only on the requested diagram task
- do not implement application code unless explicitly requested
- do not change architecture without approval
- use clear hierarchical layouts
- avoid overlapping nodes
- avoid arrows crossing through nodes
- avoid unnecessary edge crossings
- keep related components grouped
- use consistent spacing
- separate major pipelines when necessary

For complex systems, prefer multiple focused diagrams instead of one
unreadable diagram.

Recommended diagrams:

1. User Interaction Flow
2. AIOS System Architecture
3. Database Adaptation Flow
4. AIOS Internal Database / Data Flow
5. RAG / Document Flow
6. Worker / AI Manager Flow
7. Plugin Integration Flow

Do not combine unrelated diagrams into one diagram unless explicitly
requested.

---

## Code Quality

Keep the prototype:

- modular
- readable
- maintainable
- easy to demonstrate
- easy to extend

Prefer simple solutions over unnecessary abstraction.

Do not add production-level infrastructure unless it directly supports
the prototype.

Avoid premature optimization.

---

## Testing

Testing must validate both functionality and adaptability.

Do not test only one database structure.

Use multiple simulated client systems with substantially different
schemas.

Test:

- different table names
- different column names
- different relationships
- different data representations
- different database engines where practical
- schema understanding
- semantic mapping
- canonical model generation
- mapping persistence
- client isolation (multi-tenant, via login)
- role-based access (Client vs Ekasa Developer roles)
- usage / token metering
- worker queries
- incorrect or ambiguous mappings
- schema changes
- error handling
- Internal Database versus Client Database data boundaries

The most important question is:

"Can AIOS adapt to a client's existing system without requiring the
client to redesign that system?"

---

## Current Project Principle

The central principle of AIOS is:

CLIENT SYSTEM STAYS.
AIOS ADAPTS.

AIOS should provide:

Plug in
  ↓
Adapt
  ↓
Understand
  ↓
Persist Metadata
  ↓
Use

The client should not have to redesign its existing system just to use
AIOS.

The Client Database remains the source of truth for business data.

The AIOS Internal Database stores the metadata, mapping, configuration,
and state required to make AIOS adaptable, reusable, and suitable for
multiple clients.