"""General-purpose tools: web search and image description."""
import json
import os
from typing import Optional

import aiohttp
import requests
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from workflow.const import Tools
from workflow.tools.tools_config import TAVILY_API_KEY

# OpenAI web search key (shared with embedding key)
OPENAI_API_KEY: str = os.environ.get("EMBEDDING_API_KEY", "")
OPENAI_WEB_SEARCH_MODEL: str = os.environ.get(
    "OPENAI_WEB_SEARCH_MODEL", "gpt-4o-mini-search-preview"
)


# ── Web Search ────────────────────────────────────────────────────────────────


def _search_tavily(query: str, site: Optional[str] = None) -> dict:
    """Use Tavily API for web search."""
    api_key = TAVILY_API_KEY
    if not api_key:
        return {"error": "TAVILY_API_KEY not set"}

    payload: dict = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "include_answer": True,
        "max_results": 5,
    }
    if site:
        payload["include_domains"] = [site]

    response = requests.post(
        "https://api.tavily.com/search",
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    results = [
        {"title": r.get("title", ""), "url": r.get("url", ""), "content": r.get("content", "")}
        for r in data.get("results", [])
    ]
    return {"answer": data.get("answer", ""), "results": results}


def _search_openai(query: str, site: Optional[str] = None) -> dict:
    """Use OpenAI built-in web search via chat completions API."""
    from openai import OpenAI

    api_key = OPENAI_API_KEY
    if not api_key:
        return {"error": "OPENAI_API_KEY / EMBEDDING_API_KEY not set"}

    client = OpenAI(api_key=api_key)
    messages = [{"role": "user", "content": query}]

    search_context = "low"
    if site:
        messages[0]["content"] = f"{query} site:{site}"

    response = client.chat.completions.create(
        model=OPENAI_WEB_SEARCH_MODEL,
        messages=messages,
        web_search_options={"search_context_size": search_context},
        max_tokens=1500,
    )

    content = response.choices[0].message.content or ""

    # Extract citations from annotations if present
    citations = []
    annotations = getattr(response.choices[0].message, "annotations", None) or []
    for ann in annotations:
        if hasattr(ann, "url_citation"):
            citations.append({
                "title": getattr(ann.url_citation, "title", ""),
                "url": getattr(ann.url_citation, "url", ""),
            })

    return {
        "answer": content,
        "results": citations if citations else [{"title": "Web search", "url": "", "content": content[:300]}],
    }


def search(
    query: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    site: Optional[str] = None,
) -> Optional[str]:
    """Search the web and return answer + top results.

    Uses Tavily if TAVILY_API_KEY is set, otherwise falls back to OpenAI web search
    if EMBEDDING_API_KEY (OpenAI key) is set.
    """
    if TAVILY_API_KEY:
        engine = "tavily"
        try:
            data = _search_tavily(query, site)
        except Exception as e:
            return f"Tavily search exception: {e}"
    elif OPENAI_API_KEY:
        engine = "openai"
        if start_date or end_date:
            # OpenAI web search doesn't support date filtering
            query = f"{query} (from {start_date or 'any'} to {end_date or 'now'})"
        try:
            data = _search_openai(query, site)
        except Exception as e:
            return f"OpenAI search exception: {e}"
    else:
        return "Search unavailable: set TAVILY_API_KEY or EMBEDDING_API_KEY (OpenAI) environment variable."

    if "error" in data:
        return f"Search error ({engine}): {data['error']}"

    return json.dumps(
        {"engine": engine, "answer": data.get("answer", ""), "results": data.get("results", [])},
        ensure_ascii=False,
        indent=2,
    )


class SearchInput(BaseModel):
    query: str = Field(description="a simple query to search, do not include too many key words or quotation marks")
    start_date: Optional[str] = Field(
        default=None,
        description="[Optional]: filter the search results to only include pages from a specific start date.",
    )
    end_date: Optional[str] = Field(
        default=None,
        description="[Optional]: filter the search results to only include pages from a specific end date.",
    )
    site: Optional[str] = Field(
        default=None,
        description="[Optional]: restrict the search to a specific website or domain. For example, 'wikipedia.org' will only return results from wikipedia site.",
    )


class SearchOutput(BaseModel):
    answer: Optional[str] = Field(default=None, description="summary of the search results")
    results: list = Field(description="list of the search results")


search_tool = StructuredTool.from_function(
    func=search,
    name="web_search",
    description="Searches the web using Tavily or OpenAI and returns an answer summary plus top result URLs and snippets.",
    args_schema=SearchInput,
    metadata={
        "args_schema_json": SearchInput.model_json_schema(),
        "output_schema_json": SearchOutput.model_json_schema(),
    },
)

# ── Image Description ─────────────────────────────────────────────────────────
# Configure via environment variable:
#   VL_MODEL_URL  — OpenAI-compatible chat completions endpoint for a vision-language model
#   VL_MODEL_NAME — Model name (default: Qwen/Qwen2.5-VL-72B-Instruct)

async def _image_to_desc(image_url: str) -> str:
    """Describe the contents of an image given its URL."""
    vl_url = os.environ.get("VL_MODEL_URL", "")
    vl_model = os.environ.get("VL_MODEL_NAME", "Qwen/Qwen2.5-VL-72B-Instruct")

    if not vl_url:
        return "Image description unavailable: VL_MODEL_URL environment variable not set."

    req = {
        "model": vl_model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Please describe what you see in this image."},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ],
    }
    response = requests.post(vl_url + "/v1/chat/completions", stream=False, json=req)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


class ImageToDescInput(BaseModel):
    image_url: str = Field(description="Public URL of the image to describe")


image_to_desc = StructuredTool.from_function(
    coroutine=_image_to_desc,
    name="image_to_text_description",
    description=(
        "Given a public image URL, returns a textual description of the image content. "
        "Requires VL_MODEL_URL environment variable pointing to an OpenAI-compatible "
        "vision-language model endpoint."
    ),
    args_schema=ImageToDescInput,
    metadata={"args_schema_json": ImageToDescInput.schema()},
)


# ── Citation Converter ────────────────────────────────────────────────────────
# NOTE: citation_convert_tool is kept for reference but not exported in __init__.py
# because it relies on a gateway service. Users can re-enable it by self-hosting
# citation-js or wiring in their own endpoint.
