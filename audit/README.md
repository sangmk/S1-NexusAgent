# Audit Summary — S1-NexusAgent

**Date**: 2026-05-15

## What was done

1. **Diagnosed the initial loading failure** (`ModuleNotFoundError: deepagents.backends`)
2. **Mapped every LLM construction site** across the codebase (17 sites)
3. **Classified each as replaceable vs. locked-in**
4. **Refactored `workflow/nodes/models.py`** to be provider-agnostic (ChatDeepSeek → ChatOpenAI throughout)
5. **Fixed `workflow/tools/biomini_eval_tools.py`** (last ChatDeepSeek holdout)
6. **Created `pyproject.toml`** with optional-dependency groups
7. **Updated `requirements.txt`** with all missing packages
8. **Updated `.envrc`** with venv auto-activation
9. **Verified end-to-end**: all imports resolve, all 9 model factories produce `ChatOpenAI` instances, zero `ChatDeepSeek` imports remain in `workflow/`

## Files changed

| File | Change |
|---|---|
| `workflow/nodes/models.py` | Rewritten: provider-agnostic factory using `ChatOpenAI` |
| `workflow/tools/biomini_eval_tools.py` | `ChatDeepSeek` → `ChatOpenAI`, removed unused import |
| `pyproject.toml` | **New** — pip-installable project with `[science]`, `[cli]`, `[sandbox]`, `[observability]` extras |
| `requirements.txt` | Complete dependency list (was missing ~15 packages) |
| `.envrc` | Added venv auto-activation |
| `audit/01_install_failure.md` | **New** — root cause + 3 fix options |
| `audit/02_model_lockin.md` | **New** — per-call-site replaceability analysis |
| `audit/03_supporting_libs.md` | **New** — 6-layer library stack + elegant pyproject.toml |
| `audit/04_local_deployment.md` | **New** — 3-tier deployment with minimum keys |
| `audit/models_refactored.py` | **New** — reference copy of refactored models.py |
| `workflow/nodes/models.py.bak` | Original backup |

## Key findings

### Question 1: Why initial loading fails
`deepagents` is shipped as source under `deepagents/libs/` but never installed. `PYTHONPATH` is expected but not automatic. Fix: `pip install -e ./deepagents/libs/deepagents -e ./deepagents/libs/cli` + set `PYTHONPATH`. Also missing ~15 dependency packages not listed in requirements.txt.

### Question 2: Model lock-in
- **Everything is replaceable** — all LLM calls use standard OpenAI-compatible API features (tool calling, structured output, temperature). Swap `DEEPSEEK_BASE_URL` to any OAI-compat endpoint.
- **EVO2/ESM3/MassSpec** are the only truly locked endpoints (proprietary HTTP APIs), but they're optional — set env vars empty and agent runs fine.
- **Zero `ChatDeepSeek` imports remain** after refactor.

### Question 3: Supporting libraries for rigorous reasoning
6-layer stack: agent orchestration (LangGraph), structured reasoning (Pydantic v2 `with_structured_output`), domain tools (Biopython/RDKit/etc.), observability (Langfuse, self-hostable), code sandbox, CLI. The `pyproject.toml` provides elegant `[science]`, `[cli]`, `[sandbox]`, `[observability]` extras.

### Question 4: Minimum API keys
**Tier 0** (zero keys): ollama/vllm local models. **Tier 1** (1 key): any OAI-compat provider offering chat+embeddings (OpenAI, Together, Fireworks). **Tier 2** (1-2 keys): separate chat + embedding providers if needed (e.g. DeepSeek for chat + OpenAI for embeddings). Optional extras: Tavily ($), Materials Project (free), Langfuse (self-hostable).

## Verification output (2026-05-15)

```
1. deepagents.backends...       OK
2. cli.nexus_agent...           OK
3. models.py factory (all 9)... PASS
   planner:     RunnableSequence -- model=structured
   execute:     ChatOpenAI -- model=deepseek-chat
   supervisor:  RunnableSequence -- model=structured
   classify:    RunnableSequence -- model=structured
   chat:        ChatOpenAI -- model=deepseek-chat
   intent:      RunnableSequence -- model=structured
   skill_match: RunnableSequence -- model=structured
   reflection:  RunnableSequence -- model=structured
   report:      ChatOpenAI -- model=deepseek-chat
4. tools_config + biomini...    ChatOpenAI(deepseek-chat)
5. vector_store...              OpenAIEmbeddings
6. ChatDeepSeek in workflow/... CLEAN (comment only)
```
