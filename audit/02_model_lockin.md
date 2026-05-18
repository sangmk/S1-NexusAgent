# Audit 02 — Model/vendor lock-in analysis

## Every LLM/embedding construction site

### Category A: Central model factory (`workflow/nodes/models.py`)

**9 node-specific functions**, all hardcoded to `ChatDeepSeek`:

| Function | Uses `with_structured_output`? | Replaceable? |
|---|---|---|
| `get_planner_model` | Yes (`UnknownPlan`) | ✅ Any OAI-compat with structured output |
| `get_execute_model` | No (tool-calling only) | ✅ Any OAI-compat with tool calling |
| `get_supervisor_model` | Yes (`SubtaskReview`) | ✅ Any OAI-compat with structured output |
| `get_classify_model` | Yes (`Result`) | ✅ Any OAI-compat with structured output |
| `get_normal_chat_model` | No | ✅ Any OAI-compat |
| `get_intent_model` | Yes (`IntentSchema`) | ✅ Any OAI-compat with structured output |
| `get_skill_match_model` | Yes (`SkillMatchResult`) | ✅ Any OAI-compat with structured output |
| `get_reflection_model` | Yes (`Result`) | ✅ Any OAI-compat with structured output |
| `get_report_model` | No | ✅ Any OAI-compat |

**Verdict**: All 9 functions use **standard OpenAI-compatible API features**
(tool calling, structured output via JSON mode, temperature, max_tokens,
timeout). None use DeepSeek-only features. The `ChatDeepSeek` class itself is
a thin subclass of `ChatOpenAI`. **All are replaceable with `ChatOpenAI`**
pointing to any OpenAI-compatible endpoint (OpenAI, Groq, Together, Fireworks,
local vLLM/Ollama, etc.).

### Category B: Tool-level LLM instances

| File | Class used | Locked? |
|---|---|---|
| `workflow/tools/tools_config.py:17` | `ChatOpenAI` → DeepSeek via env | ✅ Already uses `ChatOpenAI` — generic |
| `workflow/tools/bio_database.py:35` | `ChatOpenAI` → DeepSeek via env | ✅ Generic |
| `workflow/tools/bio_genomics.py:30` | `ChatOpenAI` via `get_llm()` → DeepSeek | ✅ Generic |
| `workflow/tools/biomini_eval_tools.py:38` | `ChatDeepSeek` | ⚠️ Only `ChatDeepSeek` holdout — trivial to swap |
| `workflow/tool_retriever.py:157` | `ChatOpenAI` | ✅ Generic |
| `workflow/tool_retriever_optimized.py:181` | `ChatOpenAI` | ✅ Generic |
| `workflow/utils/retriever.py:74` | `ChatOpenAI` | ✅ Generic |

**Verdict**: Only **one** hardcoded `ChatDeepSeek` call site outside
`models.py`. The rest already use the generic `ChatOpenAI`.

### Category C: Embedding

| Location | Class | Locked? |
|---|---|---|
| `workflow/tools/__init__.py:398` | `OpenAIEmbeddings` → Qwen3-Embedding-8B | ✅ Uses standard `OpenAIEmbeddings` — works with any embedding model behind an OAI-compat endpoint (text-embedding-3-small, Cohere via proxy, local sentence-transformers server, etc.) |

**Verdict**: The embedding model name `Qwen/Qwen3-Embedding-8B` is a
**runtime config value**, not a code dependency. Swap `EMBEDDING_MODEL` in
`.env` and it works with any embeddings endpoint.

### Category D: Self-hosted science model endpoints (HTTP calls, not LangChain)

| Endpoint | Used in | Locked? |
|---|---|---|
| EVO2 (DNA generation) | bio tools | ⚠️ Requires the specific EVO2 model server — no standard API |
| ESM3 (protein structure) | bio tools | ⚠️ Requires ESM3 server with its specific API contract |
| MassSpec (mass spectrometry) | chem tools | ⚠️ Requires a specific self-hosted model endpoint |
| VL model (image description) | general tools | ✅ OAI-compat vision endpoint — replaceable |

**Verdict**: EVO2, ESM3, and MassSpec endpoints are **completely optional**
— the agent runs fine without them. They're only called when a user asks a
biology/chemistry question that triggers those specific tools. For a
general-purpose deployment, **set those env vars empty** and the tools become
no-ops.

### Category E: External third-party APIs (not LLMs)

| API | Env var | Optional? |
|---|---|---|
| Tavily (web search) | `TAVILY_API_KEY` | Optional — `web_search` tool fails gracefully |
| Materials Project | `MP_API_KEY` | Optional — material tools check for it |
| NCBI/UniProt/PubChem | Public, rate-limited free access | No key needed |
| Langfuse (tracing) | `LANGFUSE_SECRET_KEY` | Optional — do NOT set and tracing is a no-op |

## What CAN be replaced (summary)

- **Every LLM call site** → any OpenAI-compatible provider via env vars.
  Change `DEEPSEEK_BASE_URL` to `https://api.openai.com/v1` and
  `DEEPSEEK_V3_2_MODEL` to `gpt-4o` and everything works.
- **Embedding** → any model behind an OAI-compat `/v1/embeddings` endpoint.
- **Vision model** → any OAI-compat `/v1/chat/completions` with image support.

## What CANNOT be replaced without code changes

- **`ChatDeepSeek` → `ChatOpenAI`** in `workflow/nodes/models.py` (trivial
  one-line swap per function — we already prepared the refactor in
  `models_refactored.py`).
- **EVO2/ESM3/MassSpec** — these call **proprietary HTTP endpoints** with
  domain-specific input/output schemas. They require the matching model server
  or equivalent. But they're **completely optional** and only fire on specific
  science queries.

## What IS model/version-specific (traps)

| Trap | Details |
|---|---|
| Embedding model `Qwen/Qwen3-Embedding-8B` expects 8192-dim vectors | If you swap to `text-embedding-3-small` (1536-dim), the InMemoryVectorStore works fine but retrieval quality may differ. The dimension is auto-detected by `OpenAIEmbeddings` — no code change needed. |
| Structured output schemas reference `planner_output.UnknownPlan` etc. | These are Pydantic models defined in `workflow/prompt/`. They work with any model supporting JSON mode. DeepSeek's implementation is standard. |
| `max_tokens: 8192` on many models | If swapping to a model with lower context (e.g. llama-3.2-3b which caps at 2048), adjust the config. |
| Timeout expectations | `timeout=30` on some models — fine for most providers. |
