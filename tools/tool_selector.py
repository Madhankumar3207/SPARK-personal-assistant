"""Map analyzed SPARK actions to their existing capability families."""


ACTION_CAPABILITIES = {
    "MEMORY": "MEMORY",
    "SEARCH_FILE": "FILE_SEARCH",
    "FIND_LARGEST_FILE": "FILE_SEARCH",
    "OPEN_PATH": "FILE_OPEN",
    "OPEN_SEARCH_RESULT": "FILE_OPEN",
    "EXCEL_CONTROL": "EXCEL",
    "OPEN_APP": "APP_CONTROL",
    "WEB_OPEN": "WEB_INFORMATION",
    "WEB_SEARCH": "WEB_INFORMATION",
    "BROWSER_SEARCH": "WEB_INFORMATION",
    "OPEN_WEBSITE_URL": "WEB_INFORMATION",
    "CONVERSATION": "CONVERSATION",
    "PATTERN_ANALYSIS": "PATTERN_ANALYSIS",
    "SYSTEM_INFORMATION": "SYSTEM_INFORMATION",
    "NETWORK_INFORMATION": "NETWORK_INFORMATION",
    "CALCULATOR": "CALCULATOR",
}


def select_tool(command):
    """Annotate an already analyzed command without changing its existing action."""
    selected = dict(command)
    selected["capability"] = ACTION_CAPABILITIES.get(
        selected.get("action"),
        "SAFE_SELF_LEARNING" if selected.get("action") == "UNKNOWN" else None,
    )
    return selected
