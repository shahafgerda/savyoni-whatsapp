"""Explicit tool registry.

TOOL_REGISTRY maps a tool name to its definition:
    {
        "schema": <provider-agnostic description used to tell the LLM about it>,
        "fn":     <python callable that performs the action>,
    }

It starts empty. External tools (calendar, gmail, reminders, human handoff)
are added here by the `wa-connect` skill. Grep for a tool name and you'll
find exactly where it lives - no framework magic.
"""

TOOL_REGISTRY: dict[str, dict] = {}
