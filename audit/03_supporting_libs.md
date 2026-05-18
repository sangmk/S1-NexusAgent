# Audit 03 — Supporting libraries for rigorous reasoning

The S1-NexusAgent's "rigorous reasoning" comes from a layered stack of
supporting libraries. Each layer serves a distinct purpose.

## Layer 1: Agent orchestration (required)

| Library | Purpose | Version constraint |
|---|---|---|
| `langgraph` | State machine for multi-node pipeline (planner→execute→supervise→reflect→report) | >=1.0.0 (v1 API, stable) |
| `langgraph-checkpoint` | Session persistence — resume long science tasks across restarts | >=4.0.0 |
| `langgraph-prebuilt` | Prebuilt agent patterns | >=1.0.0 |
| `langchain-core` | Base abstractions (tools, messages, runnables) | >=0.3.0 |
| `langchain-openai` | OpenAI-compatible chat + embedding client | any recent |
| `langchain-deepseek` | DeepSeek-specific thin wrapper (replaceable — see audit 02) | any recent |

These form the **agent skeleton**. Without them, there is no graph, no state
machine, no tool binding.

## Layer 2: Structured reasoning (required)

| Library | Purpose |
|---|---|
| `pydantic>=2.0.0` | All structured outputs (`UnknownPlan`, `SubtaskReview`, `IntentSchema`, `SkillMatchResult`, `Result`) are Pydantic v2 models. The agent uses `with_structured_output(pydantic_model)` which internally does JSON Schema → constrained generation. |

This is the **core mechanism** that makes reasoning "rigorous" — the planner,
supervisor, intent classifier, skill matcher, and reflection node all produce
typed, validated outputs rather than raw text.

## Layer 3: Tool ecosystem (domain-specific, conditionally required)

### Scientific computation
| Library | Domain | Required for |
|---|---|---|
| `biopython` | Biology | Sequence parsing, NCBI queries, protein data |
| `gget` | Biology | Gene/protein info queries |
| `gseapy` | Biology | Gene set enrichment analysis |
| `scanpy` | Biology | Single-cell analysis |
| `rdkit` | Chemistry | Molecular manipulation, fingerprints, SMILES |
| `numpy`, `scipy` | All | Numerical computation |
| `pandas` | All | Tabular data handling |
| `scikit-learn` | All | ML utilities (cosine similarity, etc.) |

### External data access
| Library | Purpose |
|---|---|
| `aiohttp`, `httpx`, `requests` | HTTP calls to NCBI, UniProt, PubChem, PDB, etc. |
| `beautifulsoup4`, `lxml` | HTML parsing for web-scraped biological databases |
| `pymongo` | Optional — large tool output caching |
| `tavily-python` | Web search (needs `TAVILY_API_KEY`) |
| `playwright` | Browser automation for dynamic sites |

## Layer 4: Observability (optional but recommended)

| Library | Purpose |
|---|---|
| `langfuse` | Full trace of every LLM call, tool invocation, and node transition. Self-hostable (https://langfuse.com/docs/deployment/self-host) — zero external dependency if self-hosted. |

Langfuse is wired into the agent via `workflow/config.py` callback handlers.
If `LANGFUSE_SECRET_KEY` is empty, tracing is a no-op. **No code change
needed to disable it.**

## Layer 5: Code execution sandbox (optional)

| Library | Purpose |
|---|---|
| `agent-sandbox` | Remote code execution in an isolated container. Default points to `localhost:9001`. The sandbox_launcher in `workflow/sandbox_launcher.py` manages lifecycle. |

Without a sandbox, the execute node can still run code locally via the shell
backend (enabled by default via `enable_shell=True`).

## Layer 6: Interactive CLI (optional for server deployment)

| Library | Purpose |
|---|---|
| `deepagents-cli`, `textual>=1.0.0`, `textual-autocomplete`, `prompt-toolkit` | Terminal UI with autocomplete, syntax highlighting, multi-thread management |
| `rich` | Terminal formatting |

For a **headless/server deployment** (REST API, cron job, Jupyter), the CLI
layer is unnecessary.

## Elegant install: single `pyproject.toml`

```toml
[project]
name = "s1-nexusagent"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "langgraph>=1.0.0",
    "langgraph-checkpoint>=4.0.0",
    "langgraph-prebuilt>=1.0.0",
    "langchain-core>=0.3.0",
    "langchain-openai",
    "langchain-deepseek",
    "pydantic>=2.0.0",
    "python-dotenv",
    "openai",
]

[project.optional-dependencies]
science = [
    "biopython",
    "gget",
    "gseapy",
    "scanpy",
    "rdkit",
    "numpy",
    "scipy",
    "pandas",
    "scikit-learn",
    "aiohttp",
    "httpx",
    "requests",
    "beautifulsoup4",
    "lxml",
    "pymongo",
    "tavily-python",
    "playwright",
]
cli = [
    "deepagents>=0.4.7",
    "deepagents-cli>=0.0.31",
    "textual>=1.0.0",
    "textual-autocomplete>=3.0.0",
    "prompt-toolkit>=3.0.0",
    "rich",
]
sandbox = ["agent-sandbox>=1.0.0"]
observability = ["langfuse"]

[tool.setuptools.packages.find]
include = ["workflow*", "cli*", "deepagents*"]

[project.scripts]
nexus = "cli.main:run_nexus_cli_async"
```

Install patterns:

```bash
# Minimal (no science tools, no CLI)
pip install -e .

# Full science suite + CLI
pip install -e ".[science,cli]"

# Everything
pip install -e ".[science,cli,sandbox,observability]"
```
