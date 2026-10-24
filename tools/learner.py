"""Rule-based, allowlisted learning for safe reusable SPARK capabilities."""

import json
import re
from pathlib import Path

from config.paths import runtime_file

from tools.app_tools import open_path
from tools.file_tools import (
    COMMON_FOLDERS,
    FILE_TYPE_EXTENSIONS,
    files_in_folder,
    find_largest_file,
    find_matching_files,
    find_most_recent_file,
)


SKILLS_FILE = runtime_file("skills", "learned_skills.json")
SAFE_CAPABILITIES = {
    "find_largest_file", "find_most_recent_file", "count_files",
    "average_numbers", "extract_email_addresses", "sort_numbers", "find_and_open",
}
DANGEROUS_TERMS = {
    "shutdown", "restart", "lock computer", "sleep computer", "hibernate",
    "sign out", "delete", "erase", "password", "credential", "security",
    "administrator", "privilege", "command prompt", "powershell",
}


def _load_skills():
    try:
        with SKILLS_FILE.open(encoding="utf-8") as file:
            return json.load(file).get("skills", {})
    except FileNotFoundError:
        _save_skills({})
        return {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_skills(skills):
    try:
        SKILLS_FILE.parent.mkdir(exist_ok=True)
        with SKILLS_FILE.open("w", encoding="utf-8") as file:
            json.dump({"skills": skills}, file, indent=2)
        return True
    except OSError:
        return False


def _folder_from_request(text):
    match = re.search(r"\b(downloads|desktop|documents|pictures|videos|music)\b", text.lower())
    return match.group(1) if match else None


def _extensions_from_request(text):
    text = text.lower()
    for file_type, extensions in FILE_TYPE_EXTENSIONS.items():
        if file_type in text or file_type.rstrip("o") + "s" in text:
            return extensions
    extension = re.search(r"\b(jpg|jpeg|png|gif|webp|pdf|mp3|wav|m4a|aac|flac|ogg|mp4|mkv|avi|mov)\b", text)
    return ["." + extension.group(1)] if extension else None


def _definition(capability):
    definitions = {
        "find_largest_file": ("Find the largest file in a specified folder", ["largest file", "biggest file", "which file is largest"], ["identify target folder", "scan safe folder", "compare file sizes", "return largest file"]),
        "find_most_recent_file": ("Find the most recently modified file in a specified folder", ["most recently modified", "newest file"], ["identify target folder", "scan safe folder", "compare modification times", "return newest file"]),
        "count_files": ("Count files of a specified type in a folder", ["count how many", "how many jpg files"], ["identify folder and type", "scan safe folder", "count matches"]),
        "average_numbers": ("Calculate the average of supplied numbers", ["average of"], ["parse numbers", "calculate average", "return result"]),
        "extract_email_addresses": ("Extract email addresses from supplied text", ["extract email addresses"], ["read supplied text", "find email patterns", "return matches"]),
        "sort_numbers": ("Sort supplied numbers", ["sort numbers", "largest to smallest"], ["parse numbers", "sort values", "return result"]),
        "find_and_open": ("Find a file and open the best matching result", ["find my resume and open it"], ["search matching files", "select best result", "open one file"]),
    }
    description, triggers, steps = definitions[capability]
    return {"description": description, "triggers": triggers, "steps": steps, "status": "validated"}


def _validate(capability):
    return capability in SAFE_CAPABILITIES and callable({
        "find_largest_file": find_largest_file,
        "find_most_recent_file": find_most_recent_file,
        "count_files": files_in_folder,
        "find_and_open": find_matching_files,
    }.get(capability, lambda: True))


def _learn(capability):
    if not _validate(capability):
        return False, False
    skills = _load_skills()
    existing = skills.get(capability, {}).get("status") == "validated"
    if not existing:
        skills[capability] = _definition(capability)
        if not _save_skills(skills):
            return False, False
    return True, existing


def _number_values(text):
    return [float(value) for value in re.findall(r"[-+]?\d*\.?\d+", text)]


def _execute(capability, text, folder, extensions):
    if capability == "find_largest_file":
        file = find_largest_file(folder, extensions)
        return f"The largest file is {file.name} ({file.stat().st_size:,} bytes)." if file else "I couldn't find any matching files."
    if capability == "find_most_recent_file":
        file = find_most_recent_file(folder, extensions)
        return f"The most recently modified file is {file.name}." if file else "I couldn't find any matching files."
    if capability == "count_files":
        return f"I found {len(files_in_folder(folder, extensions))} matching files."
    if capability == "average_numbers":
        values = _number_values(text)
        return f"The average is {sum(values) / len(values):g}." if values else "Please provide numbers to average."
    if capability == "extract_email_addresses":
        emails = re.findall(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, re.I)
        return "Email addresses: " + ", ".join(emails) if emails else "I couldn't find any email addresses."
    if capability == "sort_numbers":
        values = _number_values(text)
        descending = "largest to smallest" in text.lower() or "descending" in text.lower()
        return "Sorted: " + ", ".join(f"{value:g}" for value in sorted(values, reverse=descending)) if values else "Please provide numbers to sort."
    if capability == "find_and_open":
        query = re.sub(r"^find\s+(?:my\s+)?|\s+and\s+open$", "", text, flags=re.I).strip()
        matches = find_matching_files(query)
        return open_path(str(matches[0])) if matches else "I couldn't find a matching file."


def _identify(text):
    lowered = text.lower()
    if re.search(r"\b(largest|biggest)\b.*\bfile\b", lowered):
        return "find_largest_file"
    if "most recently modified" in lowered or "newest file" in lowered:
        return "find_most_recent_file"
    if re.search(r"\bcount\b.*\bfiles?\b|\bhow many\b.*\bfiles?\b", lowered):
        return "count_files"
    if "average of" in lowered:
        return "average_numbers"
    if "extract email addresses" in lowered:
        return "extract_email_addresses"
    if re.match(r"^sort\b", lowered) and re.search(r"\d", lowered):
        return "sort_numbers"
    if re.match(r"^find\s+.+\s+and\s+open$", lowered):
        return "find_and_open"
    return None


def learn_and_execute(request):
    """Analyze one unknown request, learn only validated safe capabilities, then run it."""
    text = (request or "").strip()
    if not text or any(term in text.lower() for term in DANGEROUS_TERMS):
        return "I couldn't safely learn how to perform that task yet."

    capability = _identify(text)
    folder = _folder_from_request(text)
    extensions = _extensions_from_request(text)
    if capability in {"find_largest_file", "find_most_recent_file", "count_files"}:
        if folder not in COMMON_FOLDERS:
            return "I analyzed the task, but I couldn't safely create a reliable capability without a supported folder."

    if not capability:
        return "I couldn't safely learn how to perform that task yet."

    validated, reused = _learn(capability)
    if not validated:
        return "I analyzed the task, but I couldn't safely create a reliable capability for it yet."
    try:
        result = _execute(capability, text, folder, extensions)
    except (OSError, ValueError, ZeroDivisionError) as error:
        skills = _load_skills()
        skills.setdefault(capability, _definition(capability))["last_failure"] = str(error)[:120]
        skills[capability]["status"] = "inactive"
        _save_skills(skills)
        return "I couldn't safely learn how to perform that task yet."

    prefix = "Using learned capability." if reused else "I learned and validated a safe capability."
    return f"{prefix} {result}"
