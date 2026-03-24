"""
PI System Knowledge Provider

Uses Gemini AI with Google File Search Store to answer PI System questions
with document-backed, source-cited responses.

Usage:
    python pi_knowledge.py "How does swinging door compression work?"
    python pi_knowledge.py --json "What is PI Asset Framework?"

Environment:
    GOOGLE_GENERATIVE_AI_API_KEY  — Gemini API key
    GOOGLE_FILE_SEARCH_STORE      — Google File Search Store name
"""

import argparse
import json
import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load env from project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, "..", "..", "..")
load_dotenv(os.path.join(PROJECT_ROOT, ".env.local"))

API_KEY = os.getenv("GOOGLE_GENERATIVE_AI_API_KEY")
FILE_STORE = os.getenv("GOOGLE_FILE_SEARCH_STORE")
MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = """You are a senior AVEVA/OSIsoft PI System engineer with 15+ years of experience.
Answer the question using the documents in your knowledge base. Be specific and technical:
- Include exact parameter names, API endpoints, code snippets, and configuration values
- Reference specific documentation sections when possible
- If the knowledge base doesn't cover the topic, say so clearly
- Structure your answer with headers and code blocks where appropriate
- Keep answers focused and actionable — no fluff"""


def query(question: str, verbose: bool = False) -> dict:
    """Query Gemini with file search for PI System knowledge.

    Returns dict with 'answer', 'sources', and 'model' keys.
    """
    if not API_KEY:
        return {"error": "GOOGLE_GENERATIVE_AI_API_KEY not set", "answer": None, "sources": []}
    if not FILE_STORE:
        return {"error": "GOOGLE_FILE_SEARCH_STORE not set", "answer": None, "sources": []}

    client = genai.Client(api_key=API_KEY)

    tools = [types.Tool(file_search=types.FileSearch(file_search_store_names=[FILE_STORE]))]

    response = client.models.generate_content(
        model=MODEL,
        contents=question,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=tools,
            temperature=0.2,
        ),
    )

    answer = ""
    sources = []

    for candidate in response.candidates:
        for part in candidate.content.parts:
            if part.text:
                answer += part.text

    # Extract grounding metadata / sources if available
    if response.candidates and response.candidates[0].grounding_metadata:
        gm = response.candidates[0].grounding_metadata
        if gm.grounding_chunks:
            for chunk in gm.grounding_chunks:
                source = {}
                if hasattr(chunk, "retrieved_context") and chunk.retrieved_context:
                    ctx = chunk.retrieved_context
                    if hasattr(ctx, "title") and ctx.title:
                        source["title"] = ctx.title
                    if hasattr(ctx, "uri") and ctx.uri:
                        source["uri"] = ctx.uri
                if source:
                    sources.append(source)
        if gm.grounding_supports and verbose:
            for support in gm.grounding_supports:
                if hasattr(support, "segment") and support.segment:
                    seg = support.segment
                    print(f"  [Source support] text={seg.text[:80]}..." if seg.text and len(seg.text) > 80 else f"  [Source support] text={seg.text}", file=sys.stderr)

    # Deduplicate sources by title
    seen = set()
    unique_sources = []
    for s in sources:
        key = s.get("title", s.get("uri", ""))
        if key and key not in seen:
            seen.add(key)
            unique_sources.append(s)

    return {
        "answer": answer.strip(),
        "sources": unique_sources,
        "model": MODEL,
    }


def main():
    parser = argparse.ArgumentParser(description="Query PI System knowledge base via Gemini")
    parser.add_argument("question", help="The PI System question to answer")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show source support details")
    args = parser.parse_args()

    result = query(args.question, verbose=args.verbose)

    if result.get("error"):
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result["answer"])
        if result["sources"]:
            print("\n---\nSources:")
            for s in result["sources"]:
                title = s.get("title", "Unknown")
                uri = s.get("uri", "")
                print(f"  - {title}" + (f" ({uri})" if uri else ""))


if __name__ == "__main__":
    main()
