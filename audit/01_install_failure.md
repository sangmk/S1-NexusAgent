# Audit 01 — Why initial loading fails (and how to fix it)

## Symptom

```text
ModuleNotFoundError: No module named 'deepagents.backends'
```

This fires on **every** startup, even with faked API keys. The agent never
reaches any LLM call.

## Root cause

`cli/nexus_agent.py` line 18 imports:

```python
from deepagents.backends import CompositeBackend, LocalShellBackend
```

The repository ships `deepagents` as a **source tree** under
`deepagents/libs/deepagents/` — it is never installed as a package and is not
on `PYTHONPATH` by default.

The `requirements.txt` lists `deepagents` and `deepagents-cli` as plain names
without version pins, mirroring what a published PyPI install would look like.
But when running from a git clone with no `PYTHONPATH` set, Python cannot
resolve `deepagents.backends`.

## Additional missing dependencies (not listed at all)

| Import | Used in | In requirements.txt? |
|---|---|---|
| `langfuse` (observability tracing) | `workflow/config.py`, several nodes | **No** |
| `tavily-python` (web search) | listed as `tavily-python` in requirements.txt | marginal — name exists but pin is weak |
| `agent-sandbox` (code exec) | `workflow/codeact_remote.py` | **Yes** (but index-unstable) |
| `scikit-learn` | listed as `scikit-learn` | **Yes** but should be `scikit-learn` (hyphen) |
| `playwright` | web automation | **Yes** but requires `playwright install` post-pip |

## Fix (tested)

Three options, pick one:

### Option A — install from local source (development)

```bash
cd S1-NexusAgent
export PYTHONPATH="$(pwd):${PYTHONPATH}"
pip install -e ./deepagents/libs/deepagents -e ./deepagents/libs/cli
pip install langfuse langgraph-checkpoint-sqlite
```

### Option B — install from PyPI (quick start)

```bash
pip install deepagents==0.4.7 deepagents-cli==0.0.31 langfuse
export PYTHONPATH="$(pwd):${PYTHONPATH}"
```

### Option C — single `pyproject.toml` (recommended for local deployment)

Create a root `pyproject.toml` so `pip install -e .` handles everything (see
`03_supporting_libs.md` for the full spec).

### Verification

```bash
DEEPSEEK_API_KEY=fake python -c '
import os; os.environ["EMBEDDING_API_KEY"]="fake"
from cli.nexus_agent import create_nexus_cli_agent
print("Import OK — agent factory resolves")
'
```
