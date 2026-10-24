"""Dependency-light, content-free classification of command outcomes."""


def classify_result(response):
    """Classify known failures/clarifications without storing user command text."""
    text = str(response or "").strip().lower()
    if text.startswith(("i couldn't", "i could not", "i don't know", "i don't understand", "i can't", "that doesn't look")):
        if any(term in text for term in ("permission", "access", "configuration")):
            return False, "permission_or_configuration"
        if any(term in text for term in ("network", "internet", "browser", "api")):
            return False, "network_or_api_error"
        if any(term in text for term in ("find", "matching", "file", "folder", "application", "reminder", "task")):
            return False, "not_found_or_unsupported_target"
        return False, "unsupported_or_execution_failure"
    if text.startswith(("please tell me", "please provide", "please search", "what time", "what day", "which search result", "i found no unique", "i found multiple matching")):
        return False, "clarification_required"
    return True, "completed"
