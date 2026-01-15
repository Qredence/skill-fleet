"""Research tools for deep understanding phase.

Provides web search (Google Search API via Gemini) and filesystem search
capabilities to gather context before skill creation.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def web_search_research(query: str, max_results: int = 5) -> dict[str, Any]:
    """Execute web search using Google Search API for Gemini.

    Uses Google's Search API integration with Gemini as documented at:
    https://ai.google.dev/gemini-api/docs/google-search

    Args:
        query: Search query string
        max_results: Maximum number of results to return

    Returns:
        Dict with keys:
            - success: bool
            - results: list[dict] with {url, title, snippet, ...}
            - error: str | None
            - query: str
    """
    try:
        # Use Google Search API for Gemini
        # Based on: https://ai.google.dev/gemini-api/docs/google-search
        from google import genai
        from google.genai import types

        # Resolve API credentials preferring LiteLLM proxy (LITELLM_API_KEY)
        from ...common.env_utils import resolve_api_credentials

        creds = resolve_api_credentials(prefer_litellm=True)
        api_key = creds.get("api_key")
        if not api_key:
            return {
                "success": False,
                "results": [],
                "error": "No LITELLM_API_KEY or GOOGLE_API_KEY/GEMINI_API_KEY set",
                "query": query,
            }

        # Initialize client — if using LiteLLM proxy provide base_url if present
        # Note: google.genai.Client does not accept base_url in __init__.
        # Ignoring base_url if present to prevent initialization error.
        client = genai.Client(api_key=api_key)

        # Define Google Search tool for grounding
        grounding_tool = types.Tool(google_search=types.GoogleSearch())

        # Configure request with Google Search tool
        config = types.GenerateContentConfig(
            tools=[grounding_tool],
            temperature=1,
        )

        # Make request with search query
        response = client.models.generate_content(
            model="gemini/gemini-3-flash-preview",
            contents=f"Search for and summarize the top {max_results} most relevant results about: {query}. Include URLs and key information.",
            config=config,
        )

        # Parse response to extract search results
        results = _parse_search_response(response, max_results)

        return {
            "success": True,
            "results": results,
            "error": None,
            "query": query,
        }
    except ImportError:
        logger.warning("google-genai package not installed, web search unavailable")
        return {
            "success": False,
            "results": [],
            "error": "google-genai package not installed",
            "query": query,
        }
    except Exception as e:
        logger.warning(f"Web search failed: {e}")
        return {
            "success": False,
            "results": [],
            "error": str(e),
            "query": query,
        }


def _parse_search_response(response, max_results: int) -> list[dict[str, Any]]:
    """Parse Gemini search response to extract structured results.

    Args:
        response: Gemini API response object
        max_results: Maximum number of results to extract

    Returns:
        List of result dicts with {url, title, snippet}
    """
    results = []

    try:
        # Extract grounding metadata from response
        # Response structure depends on Gemini API version
        # Check for grounding metadata
        if hasattr(response, "grounding_metadata"):
            grounding = response.grounding_metadata
            if hasattr(grounding, "grounding_chunks"):
                for chunk in grounding.grounding_chunks[:max_results]:
                    result = {}
                    if hasattr(chunk, "web"):
                        web = chunk.web
                        result["url"] = getattr(web, "uri", "")
                        result["title"] = getattr(web, "title", "")
                    # Try to extract snippet from response text
                    result["snippet"] = ""
                    results.append(result)

        # Also parse from response text if available
        if hasattr(response, "text") and response.text:
            # Response text may contain URLs and summaries
            # This is a fallback if grounding_metadata parsing doesn't work
            text = response.text
            # Extract URLs and content (basic parsing)
            # More sophisticated parsing can be added based on actual API response format
            if not results:
                # If no results from grounding metadata, create a simple result from text
                results.append(
                    {
                        "url": "",
                        "title": "Search results summary",
                        "snippet": text[:500] if len(text) > 500 else text,
                    }
                )

    except Exception as e:
        logger.warning(f"Failed to parse search response: {e}")

    return results[:max_results]


def filesystem_research(query: str, workspace_path: Path, max_results: int = 10) -> dict[str, Any]:
    """Search filesystem using codebase_search and read_file tools.

    Uses semantic search to find relevant files and code snippets.

    Args:
        query: Search query string
        workspace_path: Root path of workspace to search
        max_results: Maximum number of results to return

    Returns:
        Dict with keys:
            - success: bool
            - files_found: list[str] of file paths
            - snippets: list[dict] with {file, content_snippet, relevance}
            - error: str | None
            - query: str
    """
    try:
        # Use codebase_search tool if available
        # For now, use a simple file search fallback
        results = _simple_file_search(query, workspace_path, max_results)

        return {
            "success": True,
            "files_found": results.get("files", []),
            "snippets": results.get("snippets", []),
            "error": None,
            "query": query,
        }
    except Exception as e:
        logger.warning(f"Filesystem search failed: {e}")
        return {
            "success": False,
            "files_found": [],
            "snippets": [],
            "error": str(e),
            "query": query,
        }


def _simple_file_search(query: str, workspace_path: Path, max_results: int) -> dict[str, Any]:
    """Simple file search fallback implementation.

    Searches for files containing query terms in their names or paths.
    This is a basic implementation - can be enhanced with semantic search later.

    Args:
        query: Search query
        workspace_path: Root path to search
        max_results: Maximum results

    Returns:
        Dict with files and snippets
    """
    files_found = []
    snippets = []

    try:
        # Search for Python, Markdown, and JSON files
        query_terms = query.lower().split()

        # Search in common directories
        search_dirs = [
            workspace_path / "skills",
            workspace_path / "src",
            workspace_path / "docs",
        ]

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            # Search for files matching query terms
            for file_path in search_dir.rglob("*.py"):
                if len(files_found) >= max_results:
                    break

                file_name = file_path.name.lower()
                file_str = str(file_path).lower()

                # Check if any query term matches
                if any(term in file_name or term in file_str for term in query_terms):
                    files_found.append(str(file_path.relative_to(workspace_path)))

                    # Try to extract a snippet
                    try:
                        content = file_path.read_text(encoding="utf-8", errors="ignore")
                        # Find first occurrence of query term
                        for term in query_terms:
                            idx = content.lower().find(term.lower())
                            if idx != -1:
                                start = max(0, idx - 100)
                                end = min(len(content), idx + 300)
                                snippet = content[start:end].strip()
                                snippets.append(
                                    {
                                        "file": str(file_path.relative_to(workspace_path)),
                                        "content_snippet": snippet,
                                        "relevance": 0.7,  # Simple relevance score
                                    }
                                )
                                break
                    except Exception:
                        # Skip files that cannot be read or parsed
                        pass

        # Also search for Markdown files
        for search_dir in search_dirs:
            if not search_dir.exists() or len(files_found) >= max_results:
                break

            for file_path in search_dir.rglob("*.md"):
                if len(files_found) >= max_results:
                    break

                file_name = file_path.name.lower()
                if any(term in file_name for term in query_terms):
                    rel_path = str(file_path.relative_to(workspace_path))
                    if rel_path not in files_found:
                        files_found.append(rel_path)

    except Exception as e:
        logger.warning(f"Simple file search error: {e}")

    return {
        "files": files_found[:max_results],
        "snippets": snippets[:max_results],
    }


def gather_context(
    topic: str,
    workspace_path: Path | None,
    research_types: list[str] | None = None,
) -> dict[str, Any]:
    """Gather context from both web and filesystem search.

    Args:
        topic: Topic to research
        workspace_path: Workspace root path (optional, for filesystem search)
        research_types: List of research types to perform ["web", "filesystem", "both"]
                       Default: ["both"]

    Returns:
        Combined context dict with web and filesystem results
    """
    if research_types is None:
        research_types = ["both"]

    context = {
        "web": {},
        "filesystem": {},
    }

    # Perform web search if requested
    if "web" in research_types or "both" in research_types:
        web_result = web_search_research(topic, max_results=5)
        context["web"] = web_result

    # Perform filesystem search if requested
    if "filesystem" in research_types or "both" in research_types:
        if workspace_path and workspace_path.exists():
            fs_result = filesystem_research(topic, workspace_path, max_results=10)
            context["filesystem"] = fs_result
        else:
            context["filesystem"] = {
                "success": False,
                "files_found": [],
                "snippets": [],
                "error": "Workspace path not provided or does not exist",
                "query": topic,
            }

    return context
