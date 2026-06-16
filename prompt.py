"""Builds the system prompt from spec.json.

Kept in its own file so wa-maintain can regenerate the bot's character
without touching any logic. The tool-availability section is dynamic:
it reads TOOL_REGISTRY so adding a tool in wa-connect automatically tells
the LLM about it - no risk of forgetting to announce a new capability.
"""
from config import SPEC


def _tools_section(tool_registry) -> str:
    if not tool_registry:
        return "אין לך כלים חיצוניים כרגע. ענה אך ורק מהמידע שניתן לך כאן."
    lines = ["יש לך הכלים הבאים, השתמש בהם כשצריך:"]
    for name, td in tool_registry.items():
        desc = td.get("schema", {}).get("description", "")
        lines.append(f"- `{name}`: {desc}")
    return "\n".join(lines)


def build_system_prompt(tool_registry=None) -> str:
    tool_registry = tool_registry or {}

    identity = SPEC["identity"]
    scope = SPEC["scope"]
    knowledge = SPEC.get("knowledge", {})
    kb = knowledge.get("kb_sections", {})

    in_scope = "\n".join(f"  • {t}" for t in scope.get("in_scope", []))
    out_scope = "\n".join(f"  • {t}" for t in scope.get("out_of_scope", []))

    hours = kb.get("hours", "").strip()
    faq = kb.get("faq", "").strip()
    static = knowledge.get("static_knowledge", "").strip()

    parts = [
        f"אתה {identity['name']}, מענה אוטומטי בוואטסאפ.",
        f"סגנון הדיבור שלך: {identity['tone_description']}.",
        "",
        "כשמישהו פותח שיחה בברכה (כמו 'היי' או 'שלום'), פתח בהודעה הזו בדיוק:",
        f"\"{identity['greeting_example']}\"",
        "",
        "מי אתה ומה תפקידך:",
        static,
        "",
        "מידע שאתה רשאי למסור:",
    ]
    if hours:
        parts.append(f"- שעות פעילות: {hours}")
    if faq:
        parts.append(f"- {faq}")

    parts += [
        "",
        "נושאים שאתה כן עונה עליהם:",
        in_scope or "  • מסירת מידע כללי בלבד",
        "",
        "נושאים שאתה לא מטפל בהם:",
        out_scope or "  • כל נושא אישי או רגיש",
        "",
        "כשמישהו שואל על נושא שאינו בתחומך, ענה בנימוס בדיוק כך:",
        f"\"{scope.get('out_of_scope_response', '')}\"",
        "",
        "כללי תשובה:",
        "- ענה בעברית בלבד.",
        "- תשובות קצרות, ענייניות ומנומסות. אל תמציא מידע שאין לך.",
        "- אל תבטיח לטפל בבקשות, להעביר הודעות או לתאם דברים - אתה רק מוסר מידע ומפנה למזכירות.",
        "- אם אינך יודע משהו, הפנה למזכירות.",
        "",
        _tools_section(tool_registry),
    ]

    return "\n".join(parts)
