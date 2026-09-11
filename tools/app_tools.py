import subprocess
import os
import re
import webbrowser
from urllib.parse import urlparse
from urllib.parse import quote_plus

from tools.file_tools import find_matching_files
from config.chrome_profiles import CHROME_PROFILES

WEBSITES = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "gmail": "https://mail.google.com",
    "github": "https://github.com",
    "chatgpt": "https://chatgpt.com",
    "instagram": "https://www.instagram.com",
    "linkedin": "https://www.linkedin.com",
    "facebook": "https://www.facebook.com",
    "amazon": "https://www.amazon.in",
    "microsoft": "https://www.microsoft.com",
    "whatsapp": "https://web.whatsapp.com",
    "whatsapp web": "https://web.whatsapp.com",
    "wikipedia": "https://www.wikipedia.org",
    "google drive": "https://drive.google.com",
    "google maps": "https://maps.google.com",
}


def open_excel():
    subprocess.Popen(["start", "excel"], shell=True)
    return "Excel opened successfully."
    
def open_chrome():
    subprocess.Popen("start chrome", shell=True)
    return "Chrome opened successfully."


def open_website(name):
    """Open one of SPARK's explicitly supported websites in Chrome."""
    website = name.lower().strip()
    url = WEBSITES.get(website)
    if not url:
        return "I don't know that website yet."
    try:
        if not webbrowser.open(url):
            return "I couldn't open the default browser."
    except webbrowser.Error:
        return "I couldn't open the default browser."
    return f"Opening {website.title()}."


def open_url(url):
    """Open an explicitly supplied, valid HTTP(S) URL in the default browser."""
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return "That doesn't look like a valid website URL."
    try:
        if not webbrowser.open(url):
            return "I couldn't open the default browser."
    except webbrowser.Error:
        return "I couldn't open the default browser."
    return "Opening website."


def get_chrome_profile(account):

    return CHROME_PROFILES.get(account.lower().strip())


def open_chrome_profile(account):

    profile = get_chrome_profile(account)

    if profile is None:
        return "I don't have that Chrome profile configured yet."

    subprocess.Popen(
        f'start chrome --profile-directory="{profile["profile_directory"]}"',
        shell=True
    )

    return (
        f"Opening Chrome with "
        f"{profile['display_name']} profile."
    )


def search_google(query, account=None):

    profile_argument = ""

    if account:

        profile = get_chrome_profile(account)

        if profile is None:
            return "I don't have that Chrome profile configured yet."

        profile_argument = (
            f' --profile-directory="{profile["profile_directory"]}"'
        )

    if query:
        search_url = (
            "https://www.google.com/search?q="
            + quote_plus(query)
        )
    else:
        search_url = "https://www.google.com"

    try:
        if account:
            subprocess.Popen(
                f'start chrome{profile_argument} "{search_url}"',
                shell=True
            )
        elif not webbrowser.open(search_url):
            return "I couldn't open the default browser."
    except (OSError, webbrowser.Error):
        return "I couldn't open the default browser."

    if query:
        return f'Searching Google for "{query}".'

    return "Opening Google."


def search_youtube(query):

    search_url = (
        "https://www.youtube.com/results?search_query="
        + quote_plus(query)
    )

    try:
        if not webbrowser.open(search_url):
            return "I couldn't open the default browser."
    except webbrowser.Error:
        return "I couldn't open the default browser."

    return f'Searching YouTube for "{query}".'


def open_files(files):

    opened = False

    for file in files:

        try:
            os.startfile(str(file))
            opened = True

        except OSError:
            continue

    return opened


def open_calculator():
    subprocess.Popen("start calc", shell=True)
    return "Calculator opened successfully."


def open_notepad():
    subprocess.Popen("start notepad", shell=True)
    return "Notepad opened successfully."


def open_vscode():
    subprocess.Popen("code", shell=True)
    return "VS Code opened successfully."


def open_explorer():
    subprocess.Popen("explorer", shell=True)
    return "File Explorer opened successfully."

def open_path(path):

    try:

        path = path.strip().strip('"')

        search_name = re.sub(
            r"^(my|the|a|an)\s+",
            "",
            path,
            flags=re.IGNORECASE
        )

        search_name = re.sub(
            r"\s+(file|document)$",
            "",
            search_name,
            flags=re.IGNORECASE
        ).strip()

        # ---------------------------------
        # DIRECT PATH
        # ---------------------------------

        if os.path.exists(path):

            os.startfile(path)

            return f"Opening {path}"

        # ---------------------------------
        # COMMON FOLDERS
        # ---------------------------------

        folders = {
            "downloads": os.path.expanduser("~/Downloads"),
            "documents": os.path.expanduser("~/Documents"),
            "desktop": os.path.expanduser("~/Desktop"),
            "videos": os.path.expanduser("~/Videos"),
            "pictures": os.path.expanduser("~/Pictures"),
            "music": os.path.expanduser("~/Music")
        }

        if search_name.lower() in folders:

            folder_path = folders[search_name.lower()]

            if os.path.exists(folder_path):

                os.startfile(folder_path)

                return f"Opening {search_name}"

        # ---------------------------------
        # SEARCH LOCATIONS
        # ---------------------------------

        search_locations = [
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Videos"),
            os.path.expanduser("~/Pictures"),
            os.path.expanduser("~/OneDrive")
        ]

        # ---------------------------------
        # 1. EXACT FILE NAME
        # ---------------------------------

        for location in search_locations:

            if not os.path.exists(location):
                continue

            for root, dirs, files in os.walk(location):

                dirs[:] = [
                    d for d in dirs
                    if d not in [
                        "node_modules",
                        ".git",
                        "__pycache__"
                    ]
                ]

                for file in files:

                    if file.lower() == path.lower():

                        full_path = os.path.join(root, file)

                        os.startfile(full_path)

                        return f"Opening {file}"

        # ---------------------------------
        # 2. FILE WITHOUT EXTENSION
        # ---------------------------------

        preferred_extensions = [
            ".xlsx",
            ".xls",
            ".docx",
            ".doc",
            ".pdf",
            ".pptx",
            ".ppt",
            ".txt",
            ".py",
            ".rs"
        ]

        # Search ONE extension across ALL locations
        # before trying the next extension.

        for extension in preferred_extensions:

            wanted_file = path + extension

            for location in search_locations:

                if not os.path.exists(location):
                    continue

                for root, dirs, files in os.walk(location):

                    dirs[:] = [
                        d for d in dirs
                        if d not in [
                            "node_modules",
                            ".git",
                            "__pycache__"
                        ]
                    ]

                    for file in files:

                        if file.lower() == wanted_file.lower():

                            full_path = os.path.join(root, file)

                            os.startfile(full_path)

                            return f"Opening {file}"

        # ---------------------------------
        # 3. KEYWORD / DESCRIPTION MATCH
        # ---------------------------------

        matches = find_matching_files(search_name)

        if matches:

            file_path = str(matches[0])

            os.startfile(file_path)

            return f"Opening {matches[0].name}"

        # ---------------------------------
        # NOT FOUND
        # ---------------------------------

        return f"I couldn't find '{path}'."

    except Exception as e:

        return f"Could not open {path}: {e}"
