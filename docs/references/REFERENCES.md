# Research Reference Registry

Single source of truth for all research references used in the AIOS project.

Only references that have been verified and actually used to inform a decision
or recommendation are registered. References are identified by REF-XXX IDs and
referenced from ADRs in `docs/decisions/`.

| REF-ID | Title | Authors | Year | Venue / Source | URL / DOI | Verified |
|---|---|---|---|---|---|---|
| REF-001 | SaaS Tenant Isolation Strategies: Isolating Resources in a Multi-Tenant Environment | AWS | 2020 | AWS Whitepaper | https://docs.aws.amazon.com/whitepapers/latest/saas-tenant-isolation-strategies/saas-tenant-isolation-strategies.html | Yes |
| REF-002 | Degrees of tenant isolation for cloud-hosted software services: a cross-case analysis | Laud Charles Ochei, Julian M. Bass, Andrei Petrovski | 2018 | Journal of Cloud Computing: Advances, Systems and Applications, 7(1) | https://doi.org/10.1186/s13677-018-0121-8 | Yes |
| REF-003 | FastAPI Documentation | Sebastián Ramírez | 2026 | Official documentation | https://fastapi.tiangolo.com/ | Yes |
| REF-004 | Appropriate Uses For SQLite | SQLite Consortium | 2025 | Official documentation | https://www.sqlite.org/whentouse.html | Yes |
| REF-005 | A survey of approaches to automatic schema matching | Erhard Rahm, Philip A. Bernstein | 2001 | The VLDB Journal, 10(4): 334–350 | https://doi.org/10.1007/s007780100057 | Yes |
| REF-006 | Navigating Complexity: Orchestrated Problem Solving with Multi-Agent LLMs | Sumedh Rasal, E. J. Hauer | 2024 | arXiv | https://doi.org/10.48550/arXiv.2402.16713 | Yes |
| REF-007 | A Cost-Benefit Analysis of On-Premise Large Language Model Deployment: Breaking Even with Commercial LLM Services | Guanzhong Pan, Vishal Chodnekar, Abinas Roy, Haibo Wang | 2025 | arXiv | https://doi.org/10.48550/arXiv.2509.18101 | Yes |
| REF-008 | ReMatch: Retrieval Enhanced Schema Matching with LLMs | Eitam Sheetrit, Menachem Brief, Moshik Mishaeli, Oren Elisha | 2024 | arXiv | https://doi.org/10.48550/arXiv.2403.01567 | Yes |
| REF-009 | AgentOrchestra: Orchestrating Multi-Agent Intelligence with the Tool-Environment-Agent (TEA) Protocol | Wentao Zhang, Liang Zeng, Yuzhen Xiao, Yongcong Li, Ce Cui, Yilei Zhao, Rui Hu, Yang Liu, Yahui Zhou, Bo An | 2025 | arXiv | https://doi.org/10.48550/arXiv.2506.12508 | Yes |
| REF-010 | Dynamic Model Routing and Cascading for Efficient LLM Inference: A Survey | Yasmin Moslem, John D. Kelleher | 2026 | arXiv | https://doi.org/10.48550/arXiv.2603.04445 | Yes |
| REF-011 | Is Escalation Worth It? A Decision-Theoretic Characterization of LLM Cascades | Dylan Bouchard | 2026 | arXiv | https://doi.org/10.48550/arXiv.2605.06350 | Yes |
| REF-012 | AOrchestra: Automating Sub-Agent Creation for Agentic Orchestration | Jianhao Ruan, Zhihao Xu, Yiran Peng, Fashen Ren, Zhaoyang Yu, Xinbing Liang, Jinyu Xiang, Yongru Chen, Bang Liu, Chenglin Wu, Yuyu Luo, Jiayi Zhang | 2026 | arXiv | https://doi.org/10.48550/arXiv.2602.03786 | Yes |
| REF-013 | Schemora: schema matching via multi-stage recommendation and metadata enrichment using off-the-shelf LLMs | Osman Erman Gungor, Derak Paulsen, William Kang | 2025 | arXiv | https://doi.org/10.48550/arXiv.2507.14376 | Yes |
| REF-014 | LLMATCH: A Unified Schema Matching Framework with Large Language Models | Sha Wang, Yuchen Li, Hanhua Xiao, Bing Tian Dai, Roy Ka-Wei Lee, Yanfei Dong, Lambert Deng | 2025 | APWeb 2025 / arXiv | https://doi.org/10.48550/arXiv.2507.10897 | Yes |
| REF-015 | Bootstrapping Self-Improvement of Language Model Programs for Zero-Shot Schema Matching | Nabeel Seedat, Mihaela Van Der Schaar | 2025 | ICML 2025, PMLR 267 | https://proceedings.mlr.press/v267/seedat25a.html | Yes |
| REF-016 | Ollama Documentation | Ollama | 2026 | Official documentation | https://docs.ollama.com/ | Yes |
| REF-017 | PostgreSQL Documentation | PostgreSQL Global Development Group | 2026 | Official documentation | https://www.postgresql.org/docs/current/ | Yes |
| REF-018 | Frappe Framework Documentation | Frappe (Frappe Technologies) | 2026 | Official documentation | https://docs.frappe.io/framework | Yes |
| REF-019 | Frappe Bench — CLI to manage multi-tenant deployments for Frappe apps | Frappe (Frappe Technologies) | 2026 | Official GitHub repository | https://github.com/frappe/bench | Yes |
| REF-020 | Frappe Installation — System Requirements & Installation Steps | Frappe (Frappe Technologies) | 2026 | Official documentation | https://docs.frappe.io/framework/user/en/installation | Yes |
| REF-021 | llama.cpp — LLM inference in C/C++ | ggml-org (Georgi Gerganov et al.) | 2026 | Official GitHub repository | https://github.com/ggml-org/llama.cpp | Yes |
| REF-022 | Qwen2.5-3B-Instruct — Model Card | Alibaba Cloud (Qwen team) | 2024 | Official model card (Hugging Face) | https://huggingface.co/Qwen/Qwen2.5-3B-Instruct | Yes |

## Verification Notes

- REF-001: Whitepaper page notes it is "for historical reference only" (August 2020). Still cited because the isolation concepts (silo/pool/bridge models, tenant context) remain the canonical reference for SaaS tenant isolation.
- REF-002: Verified via DOI and multiple independent citations; the original SpringerOpen page blocks automated access, so the metadata was cross-checked through citing works (Ochei, Bass, Petrovski, Journal of Cloud Computing 7(1), 2018).
- REF-003, REF-004, REF-016, REF-017: Official documentation verified directly at the listed URLs.
- REF-016 (Ollama) tetap terdaftar sebagai kandidat alternatif LLM runtime (lihat ADR-006).
- REF-018, REF-019, REF-020: Verified directly at the listed URLs on 2026-08-20 (docs.frappe.io framework installation page and github.com/frappe/bench). REF-020 confirms Frappe v14/v15 requirements: MariaDB 10.6.6+, Python 3.10+, NodeJS 18+, Redis/Valkey 6, Yarn 1.12+, pip 20+.
- REF-021: Verified directly at the listed URL on 2026-08-20 (github.com/ggml-org/llama.cpp). README documents the OpenAI-compatible API server (`llama-server`), CPU-only inference, and 4-bit (Q4_K_M) quantization support.
- REF-022: Verified directly at the listed URL on 2026-08-20 (huggingface.co/Qwen/Qwen2.5-3B-Instruct). Official model card: 3.09B params, causal LM, context 32K/generation 8K; GGUF variants (including q4_K_M) available at Qwen/Qwen2.5-3B-Instruct-GGUF.
- REF-005, REF-006, REF-007, REF-008, REF-009, REF-010, REF-011, REF-012, REF-013, REF-014, REF-015: Verified directly on the publisher/arXiv pages.

## Not Registered (kept out per AGENTS.md section 8)

- OWASP Multi-Tenant Security Cheat Sheet — the URL returns 404; the resource could not be verified.
- Doan, Halevy, Ives "Principles of Data Integration" — verified as a book but not yet required by any decision in this prototype.
- Other schema-matching surveys (Shvaiko & Euzenat 2005; Alwan et al. 2017) — not yet required by any ADR in this phase.
- Multi-tenant SaaS blog posts / vendor engineering posts (lower-tier) — superseded by REF-001 and REF-002 where they would have been used.
