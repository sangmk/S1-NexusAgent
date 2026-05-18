# Audit 04 — Minimum API keys for local deployment

The S1-NexusAgent can run at three tiers. Each tier defines the absolute
minimum set of env vars (set in `.env` or exported in shell).

## Tier 0: Zero external dependency (local models only)

Uses `ollama` or `vllm` running on the same machine. **No external API key
whatsoever.**

```bash
# .env
DEEPSEEK_API_KEY=ollama          # ollama ignores the key value
DEEPSEEK_BASE_URL=http://localhost:11434/v1
DEEPSEEK_V3_2_MODEL=qwen2.5:32b
EMBEDDING_API_KEY=ollama
EMBEDDING_BASE_URL=http://localhost:11434/v1
EMBEDDING_MODEL=nomic-embed-text

# Optional — leave empty
TAVILY_API_KEY=
MP_API_KEY=
LANGFUSE_SECRET_KEY=
SANDBOX_URL=http://localhost:9001   # if you run agent-sandbox locally
```

What works:
- Full agent graph (plan → execute → supervise → reflect → report)
- Tool retrieval with local embeddings
- Local shell code execution (no remote sandbox needed)

What doesn't work:
- `web_search` tool (needs Tavily key)
- Materials Project tools (needs MP key)
- Self-hosted science models (EVO2/ESM3/MassSpec)

## Tier 1: One cloud API key (simplest usable deployment)

Use **any OpenAI-compatible provider** for both chat and embeddings. Benefits:
better model quality, faster, zero GPU management.

```bash
# .env
DEEPSEEK_API_KEY=sk-...           # Your provider's API key
DEEPSEEK_BASE_URL=https://api.openai.com/v1   # or Groq, Together, etc.
DEEPSEEK_V3_2_MODEL=gpt-4o       # or any model your provider supports
EMBEDDING_API_KEY=sk-...         # Same key if provider supports embeddings
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_MODEL=text-embedding-3-small
```

**Minimum keys: exactly 1** — the provider's API key.

| Provider | Chat + Embeddings? | One key works? |
|---|---|---|
| OpenAI | Yes | ✅ |
| DeepSeek | Chat only (no embeddings) | ⚠️ Need separate embedding provider |
| Groq | Chat only | ⚠️ Need separate embedding provider |
| Together AI | Both | ✅ |
| Fireworks | Both | ✅ |
| OpenRouter | Both (with some models) | ✅ |

If your chat provider doesn't offer embeddings (DeepSeek, Groq), you need a
**second key** for embeddings. Many users point embeddings to OpenAI's free
tier or a local `ollama` instance.

## Tier 2: Full local + optional cloud services

```bash
# .env — only uncomment what you need
DEEPSEEK_API_KEY=sk-...           # Required: LLM
EMBEDDING_API_KEY=sk-...         # Required: embeddings
TAVILY_API_KEY=tvly-...          # Optional: web search
MP_API_KEY=...                   # Optional: materials science
LANGFUSE_SECRET_KEY=...          # Optional: observability
LANGFUSE_PUBLIC_KEY=...          # Optional: observability
```

**Minimum keys: 1–2** (LLM + optionally separate embedding provider).

## What is NEVER required

| Service | Why it's optional |
|---|---|
| Anthropic API key | The agent uses OpenAI-compatible APIs throughout. No Anthropic dependency. |
| Google Gemini key | Not used. |
| Azure OpenAI | Not used (can be used by changing `base_url`). |
| Materials Project | Only for `mat_sci.py` tools — empty key → tools skip MP queries gracefully. |
| EVO2/ESM3/MassSpec | Self-hosted endpoints — only fire when user runs specific bio/chem tools. |
| Langfuse | Empty `LANGFUSE_SECRET_KEY` → tracing disabled. |
| MinIO | Only for large tool output caching — empty config → tools use in-memory instead. |
| MCP servers | `--no-mcp` flag disables all MCP loading. |

## Quick-start cheat sheet (Tier 1)

```bash
# 1. Clone
git clone <repo> && cd S1-NexusAgent

# 2. Install
python -m venv .venv && source .venv/bin/activate
export PYTHONPATH="$(pwd):${PYTHONPATH}"
pip install -e ./deepagents/libs/deepagents -e ./deepagents/libs/cli
pip install langfuse

# 3. One env var
export DEEPSEEK_API_KEY="sk-your-key-here"
export EMBEDDING_API_KEY="$DEEPSEEK_API_KEY"   # same key for OpenAI
export EMBEDDING_BASE_URL="https://api.openai.com/v1"
export EMBEDDING_MODEL="text-embedding-3-small"

# 4. Run
python nexus_cli.py --no-mcp --no-conversation-log
```
