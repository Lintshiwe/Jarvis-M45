#web_search.py
import json
import re
import sys
from pathlib import Path

try:
    import requests as _requests
    _REQUESTS = True
except ImportError:
    _REQUESTS = False

try:
    from bs4 import BeautifulSoup
    _BS4 = True
except ImportError:
    _BS4 = False

def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR        = _get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"


def _get_api_key() -> str:
    with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["gemini_api_key"]


def _gemini_search(query: str, deep: bool = False) -> str:
    from google import genai

    client = genai.Client(api_key=_get_api_key())

    if deep:
        prompt = (
            f"You are a research assistant. Conduct a thorough investigation of: {query}\n\n"
            "Instructions:\n"
            "1. Search for the most important facts, data, and analysis using Google Search.\n"
            "2. Synthesize all findings into a comprehensive report.\n"
            "3. Include key statistics, dates, and notable quotes where available.\n"
            "4. Cite sources with URLs in [Source: URL] format.\n"
            "5. Organize the response with clear sections.\n"
            "6. Be thorough — aim for at least 3-5 paragraphs of substantive findings."
        )
    else:
        prompt = query

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={"tools": [{"google_search": {}}]},
    )

    text = ""
    for part in response.candidates[0].content.parts:
        if hasattr(part, "text") and part.text:
            text += part.text

    text = text.strip()
    if not text:
        raise ValueError("Gemini returned an empty response.")
    return text


def _ddg_search(query: str, max_results: int = 6) -> list[dict]:
    try:
        from ddgs import DDGS
    except ImportError:
        from duckduckgo_search import DDGS

    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append({
                "title":   r.get("title",  ""),
                "snippet": r.get("body",   ""),
                "url":     r.get("href",   ""),
            })
    return results


def _format_ddg(query: str, results: list[dict]) -> str:
    if not results:
        return f"No results found for: {query}"

    lines = [f"Search results for: {query}\n"]
    for i, r in enumerate(results, 1):
        if r.get("title"):   lines.append(f"{i}. {r['title']}")
        if r.get("snippet"): lines.append(f"   {r['snippet']}")
        if r.get("url"):     lines.append(f"   {r['url']}")
        lines.append("")
    return "\n".join(lines).strip()


def _compare(items: list[str], aspect: str) -> str:
    query = (
        f"Compare {', '.join(items)} in terms of {aspect}. "
        "Give specific facts and data. Include sources with URLs."
    )
    try:
        return _gemini_search(query)
    except Exception as e:
        print(f"[WebSearch] ⚠️ Gemini compare failed: {e} — falling back to DDG")

    all_results: dict[str, list] = {}
    for item in items:
        try:
            all_results[item] = _ddg_search(f"{item} {aspect}", max_results=3)
        except Exception:
            all_results[item] = []

    lines = [f"Comparison — {aspect.upper()}", "─" * 40]
    for item in items:
        lines.append(f"\n▸ {item}")
        for r in all_results.get(item, [])[:2]:
            if r.get("snippet"):
                lines.append(f"  • {r['snippet']}")
    return "\n".join(lines)


def _extract_text_from_url(url: str, max_chars: int = 8000) -> str:
    """Fetch and extract readable text content from a URL."""
    if not _REQUESTS:
        return f"[Error] 'requests' library not installed. Cannot fetch URL: {url}"

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
        }
        resp = _requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        if _BS4:
            soup = BeautifulSoup(resp.text, "html.parser")
            # Remove script, style, nav, footer, header
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "iframe"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
        else:
            # Basic HTML stripping
            text = re.sub(r"<[^>]+>", " ", resp.text)
            text = re.sub(r"\s+", " ", text).strip()

        # Clean up excessive whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)

        if len(text) > max_chars:
            text = text[:max_chars] + f"\n\n... [truncated at {max_chars} chars]"

        source_info = f"=== Content from {url} ===\n\n{text}"
        return source_info

    except Exception as e:
        return f"[Error] Could not fetch {url}: {e}"


def _deep_research(query: str, depth: int = 3, speak=None) -> str:
    """Multi-pass research: search, extract key URLs, fetch content, synthesize."""
    results_parts = []

    # Phase 1: Initial search with Gemini (gets sources + summary)
    if speak:
        speak("Beginning deep research, sir. Searching for initial sources.")
    print(f"[WebSearch] 🧬 Deep research phase 1 — initial search")
    try:
        initial = _gemini_search(
            f"Research the following topic thoroughly. Include specific facts, "
            f"statistics, and cite your sources with URLs: {query}",
            deep=True
        )
        results_parts.append(f"## Initial Research\n{initial}")
    except Exception as e:
        print(f"[WebSearch] ⚠️ Phase 1 failed: {e}")
        try:
            ddg = _ddg_search(query, max_results=8)
            results_parts.append(_format_ddg(query, ddg))
        except Exception:
            results_parts.append(f"[Search unavailable]")

    # Phase 2: Extract key URLs from initial results and fetch their content
    urls_to_fetch = []
    url_pattern = re.findall(r'https?://[^\s\)\]\"]+', "\n".join(results_parts))
    # Filter and deduplicate
    seen = set()
    for u in url_pattern:
        u = u.rstrip(".,;:")
        if u not in seen and len(urls_to_fetch) < depth:
            seen.add(u)
            # Only fetch articles, not search result pages
            skip_domains = ["google.com/search", "bing.com/search", "duckduckgo.com"]
            if not any(s in u for s in skip_domains):
                urls_to_fetch.append(u)

    if urls_to_fetch and speak:
        speak(f"Extracting content from {len(urls_to_fetch)} sources, sir.")

    for i, url in enumerate(urls_to_fetch):
        print(f"[WebSearch] 📄 Fetching [{i+1}/{len(urls_to_fetch)}]: {url[:80]}")
        content = _extract_text_from_url(url)
        if content and not content.startswith("[Error]"):
            results_parts.append(f"\n## Source Content ({url})\n{content[:4000]}")

    # Phase 3: Synthesis with Gemini
    if speak:
        speak("Synthesizing findings into a comprehensive report, sir.")
    print(f"[WebSearch] 🧬 Deep research phase 3 — synthesis")

    synthesis_prompt = (
        f"You are a research analyst. Based on the following research, "
        f"write a comprehensive, well-structured report on: {query}\n\n"
        f"Research data:\n\n" + "\n---\n".join(results_parts[-5:])[:12000] +
        f"\n\n---\n\nInstructions:\n"
        f"1. Synthesize key findings into a clear report with sections\n"
        f"2. Include specific facts, numbers, and data points\n"
        f"3. Cite your sources with [Source: URL] format\n"
        f"4. Be thorough and detailed — aim for 4+ paragraphs\n"
        f"5. Use markdown formatting for readability"
    )

    try:
        from google import genai
        client = genai.Client(api_key=_get_api_key())
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=synthesis_prompt,
        )
        synthesis = response.text.strip()
        return synthesis
    except Exception as e:
        print(f"[WebSearch] ⚠️ Synthesis failed: {e}")
        # Return raw collected data
        return "\n\n".join(results_parts)


def web_search(
    parameters:     dict,
    response=None,
    player=None,
    session_memory=None,
) -> str:
    params = parameters or {}
    query  = params.get("query", "").strip()
    mode   = params.get("mode",  "search").lower().strip()
    items  = params.get("items", [])
    aspect = params.get("aspect", "general").strip() or "general"
    url    = params.get("url", "").strip()
    deep   = str(params.get("deep", "")).lower() in ("true", "yes", "1")
    depth  = int(params.get("depth", 3))

    # URL content extraction mode
    if params.get("action") == "extract" or (url and not query):
        if not url:
            return "Please provide a URL to extract content from, sir."
        print(f"[WebSearch] 📄 Extracting: {url}")
        result = _extract_text_from_url(url)
        return result

    if not query and not items:
        return "Please provide a search query, sir."

    if items and mode != "compare":
        mode = "compare"

    if player:
        player.write_log(f"[Search] {query or ', '.join(items)}")

    print(f"[WebSearch] 🔍 Query: {query!r}  Mode: {mode}  Deep: {deep}")

    try:
        # Deep research mode
        if mode == "deep" or deep:
            print("[WebSearch] 🧬 Deep research mode activated")
            result = _deep_research(query, depth=depth)
            print("[WebSearch] ✅ Deep research complete.")
            return result

        # Comparison mode
        if mode == "compare" and items:
            print(f"[WebSearch] 📊 Comparing: {items}")
            result = _compare(items, aspect)
            print("[WebSearch] ✅ Compare done.")
            return result

        # Standard search
        print("[WebSearch] 🌐 Trying Gemini...")
        try:
            result = _gemini_search(query)
            print("[WebSearch] ✅ Gemini OK.")
            return result
        except Exception as e:
            print(f"[WebSearch] ⚠️ Gemini failed ({e}) — trying DDG...")
            results = _ddg_search(query)
            result  = _format_ddg(query, results)
            print(f"[WebSearch] ✅ DDG: {len(results)} result(s).")
            return result

    except Exception as e:
        print(f"[WebSearch] ❌ All backends failed: {e}")
        return f"Search failed, sir: {e}"
