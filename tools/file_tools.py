from pathlib import Path
from datetime import datetime, timedelta
import shutil


# =================================================
# SEARCH FOLDERS
# =================================================

SEARCH_FOLDERS = [
    Path.home() / "Downloads",
    Path.home() / "Desktop",
    Path.home() / "Documents",
    Path.home() / "Pictures",
    Path.home() / "Videos",
    Path.home() / "Music",
    Path.home() / "OneDrive",
]

COMMON_FOLDERS = {
    "desktop": Path.home() / "Desktop",
    "downloads": Path.home() / "Downloads",
    "documents": Path.home() / "Documents",
    "pictures": Path.home() / "Pictures",
    "videos": Path.home() / "Videos",
    "music": Path.home() / "Music",
}

_pending_delete_path = None


# =================================================
# IGNORED FOLDERS
# =================================================

IGNORED_FOLDERS = {
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
}


# =================================================
# PREFERRED EXTENSIONS
# =================================================

PREFERRED_EXTENSIONS = [
    ".xlsx",
    ".xls",
    ".docx",
    ".doc",
    ".pdf",
    ".pptx",
    ".ppt",
    ".txt",
    ".py",
    ".rs",
]


# =================================================
# FILE TYPE EXTENSIONS
# =================================================

FILE_TYPE_EXTENSIONS = {
    "pdf": [
        ".pdf"
    ],

    "image": [
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp"
    ],

    "video": [
        ".mp4",
        ".mkv",
        ".avi",
        ".mov"
    ],

    "audio": [
        ".mp3",
        ".wav",
        ".m4a",
        ".aac",
        ".flac",
        ".ogg"
    ],
}


# =================================================
# SUPPORTED EXTENSIONS
# =================================================

SUPPORTED_EXTENSIONS = (
    PREFERRED_EXTENSIONS
    + FILE_TYPE_EXTENSIONS["image"]
    + FILE_TYPE_EXTENSIONS["video"]
    + FILE_TYPE_EXTENSIONS["audio"]
)


# =================================================
# CHECK IGNORED PATH
# =================================================

def is_ignored(path):

    return any(
        part in IGNORED_FOLDERS
        for part in path.parts
    )


# =================================================
# GET SEARCH KEYWORDS
# =================================================

def get_keywords(description):

    ignored_words = {
        "my",
        "the",
        "a",
        "an",
        "file",
        "document"
    }

    return [
        word
        for word in description.lower().split()
        if word not in ignored_words
    ]


# =================================================
# FIND MATCHING FILES
# =================================================

def find_matching_files(
    description,
    date_filter=None,
    extensions=None,
    time_filter=None,
):

    keywords = get_keywords(description)

    results = []

    for folder in SEARCH_FOLDERS:

        if not folder.exists():
            continue

        try:

            for file in folder.rglob("*"):

                if not file.is_file():
                    continue

                if is_ignored(file):
                    continue

                # ---------------------------------
                # EXTENSION FILTER
                # ---------------------------------

                if (
                    extensions is not None
                    and file.suffix.lower() not in extensions
                ):
                    continue

                # ---------------------------------
                # DATE FILTER
                # ---------------------------------

                if not matches_timestamp(file, date_filter, time_filter):
                    continue

                # ---------------------------------
                # KEYWORD MATCH
                # ---------------------------------

                file_name = file.name.lower()

                keyword_count = sum(
                    keyword in file_name
                    for keyword in keywords
                )

                if keywords and keyword_count == 0:
                    continue

                # ---------------------------------
                # EXTENSION RANK
                # ---------------------------------

                try:

                    extension_rank = PREFERRED_EXTENSIONS.index(
                        file.suffix.lower()
                    )

                except ValueError:

                    extension_rank = len(
                        PREFERRED_EXTENSIONS
                    )

                results.append(
                    (
                        keyword_count,
                        extension_rank,
                        file
                    )
                )

        except (PermissionError, OSError):

            continue

    # ---------------------------------------------
    # SORT RESULTS
    # ---------------------------------------------

    results.sort(
        key=lambda result: (
            -result[0],
            result[1],
            str(result[2]).lower()
        )
    )

    return [
        result[2]
        for result in results[:20]
    ]


# =================================================
# SEARCH FILES BY EXTENSION
# =================================================

def search_files(
    extension,
    date_filter=None,
    time_filter=None,
):

    results = []

    for folder in SEARCH_FOLDERS:

        if not folder.exists():
            continue

        try:

            for file in folder.rglob(
                f"*.{extension}"
            ):

                if not file.is_file():
                    continue

                if is_ignored(file):
                    continue

                # ---------------------------------
                # DATE FILTER
                # ---------------------------------

                if not matches_timestamp(file, date_filter, time_filter):
                    continue

                results.append(file)

                if len(results) >= 20:
                    return results

        except (PermissionError, OSError):

            continue

    return results


# =================================================
# PDF SEARCH
# =================================================

def matches_timestamp(file, date_filter=None, time_filter=None):
    """Match a file's modification date and, when requested, local hour."""
    if date_filter is None and time_filter is None:
        return True
    try:
        modified = datetime.fromtimestamp(file.stat().st_mtime)
    except OSError:
        return False

    today = datetime.now().date()
    if date_filter == "today":
        target_date = today
    elif date_filter == "yesterday":
        target_date = today - timedelta(days=1)
    elif date_filter == "this_week":
        target_date = None
        if modified.date() < today - timedelta(days=today.weekday()):
            return False
    elif date_filter:
        try:
            target_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
        except ValueError:
            return False
    else:
        target_date = None

    return ((target_date is None or modified.date() == target_date)
            and (time_filter is None or modified.hour == time_filter))


def search_pdfs(date_filter=None, time_filter=None):

    return search_files(
        "pdf",
        date_filter, time_filter
    )


# =================================================
# IMAGE SEARCH
# =================================================

def search_images(date_filter=None, time_filter=None):

    extensions = [
        "jpg",
        "jpeg",
        "png",
        "gif",
        "webp"
    ]

    results = []

    for extension in extensions:

        results.extend(
            search_files(
                extension,
                date_filter, time_filter
            )
        )

        if len(results) >= 20:
            break

    return results[:20]


# =================================================
# VIDEO SEARCH
# =================================================

def search_videos(date_filter=None, time_filter=None):

    extensions = [
        "mp4",
        "mkv",
        "avi",
        "mov"
    ]

    results = []

    for extension in extensions:

        results.extend(
            search_files(
                extension,
                date_filter, time_filter
            )
        )

        if len(results) >= 20:
            break

    return results[:20]


# =================================================
# AUDIO SEARCH
# =================================================

def search_audio(date_filter=None, time_filter=None):

    extensions = [
        "mp3",
        "wav",
        "m4a",
        "aac",
        "flac",
        "ogg"
    ]

    results = []

    for extension in extensions:

        results.extend(
            search_files(
                extension,
                date_filter, time_filter
            )
        )

        if len(results) >= 20:
            break

    return results[:20]


def files_in_folder(folder_name, extensions=None):
    """Safely enumerate files in one configured user folder."""
    folder = COMMON_FOLDERS.get((folder_name or "").lower())
    if folder is None or not folder.exists():
        return []
    try:
        return [
            file for file in folder.rglob("*")
            if file.is_file()
            and not is_ignored(file)
            and (extensions is None or file.suffix.lower() in extensions)
        ]
    except (OSError, PermissionError):
        return []


def find_largest_file(folder_name, extensions=None):
    files = files_in_folder(folder_name, extensions)
    try:
        return max(files, key=lambda file: file.stat().st_size) if files else None
    except OSError:
        return None


def find_most_recent_file(folder_name, extensions=None):
    files = files_in_folder(folder_name, extensions)
    try:
        return max(files, key=lambda file: file.stat().st_mtime) if files else None
    except OSError:
        return None


# =================================================
# SAFE FILE MANAGEMENT
# =================================================

def _destination_folder(name):
    folder = COMMON_FOLDERS.get((name or "desktop").lower())
    if folder is None:
        return None
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    return folder


def _find_item(name):
    """Resolve an exact file/folder name only beneath configured user folders."""
    wanted = Path(name.strip().strip('"')).name.lower()
    if not wanted:
        return None
    for folder in SEARCH_FOLDERS:
        if not folder.exists():
            continue
        try:
            for item in folder.rglob("*"):
                if item.name.lower() == wanted and not is_ignored(item):
                    return item
        except (OSError, PermissionError):
            continue
    return None


def create_folder(name, location=None):
    destination = _destination_folder(location)
    folder_name = Path(name.strip().strip('"')).name
    if not destination or not folder_name:
        return "Please provide a folder name and a supported location."
    path = destination / folder_name
    if path.exists():
        return "That folder already exists."
    try:
        path.mkdir()
        return f"Created folder {folder_name}."
    except (OSError, PermissionError) as error:
        return f"Couldn't create the folder: {error}"


def create_text_file(name, location=None):
    destination = _destination_folder(location)
    file_name = Path(name.strip().strip('"')).name
    if not file_name.lower().endswith(".txt"):
        file_name += ".txt"
    if not destination or not file_name:
        return "Please provide a file name and a supported location."
    path = destination / file_name
    if path.exists():
        return f"{file_name} already exists."
    try:
        path.touch(exist_ok=False)
        return f"Created {file_name}."
    except (OSError, PermissionError) as error:
        return f"Couldn't create the file: {error}"


def rename_item(source_name, destination_name):
    source = _find_item(source_name)
    if source is None:
        return f"I couldn't find {source_name}."
    destination = source.with_name(Path(destination_name.strip().strip('"')).name)
    if destination.exists():
        return "A file or folder with that name already exists."
    try:
        source.rename(destination)
        return f"Renamed {source.name} to {destination.name}."
    except (OSError, PermissionError) as error:
        return f"Couldn't rename {source.name}: {error}"


def copy_item(source_name, location):
    source = _find_item(source_name)
    destination_folder = _destination_folder(location)
    if source is None:
        return f"I couldn't find {source_name}."
    if destination_folder is None:
        return "Please choose Desktop, Downloads, Documents, Pictures, Videos, or Music."
    destination = destination_folder / source.name
    if destination.exists():
        return "A file or folder with that name already exists at the destination."
    try:
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)
        return f"Copied {source.name} to {location.title()}."
    except (OSError, PermissionError) as error:
        return f"Couldn't copy {source.name}: {error}"


def move_item(source_name, location):
    source = _find_item(source_name)
    destination_folder = _destination_folder(location)
    if source is None:
        return f"I couldn't find {source_name}."
    if destination_folder is None:
        return "Please choose Desktop, Downloads, Documents, Pictures, Videos, or Music."
    destination = destination_folder / source.name
    if destination.exists():
        return "A file or folder with that name already exists at the destination."
    try:
        shutil.move(str(source), str(destination))
        return f"Moved {source.name} to {location.title()}."
    except (OSError, PermissionError) as error:
        return f"Couldn't move {source.name}: {error}"


def request_delete(name):
    global _pending_delete_path
    source = _find_item(name)
    if source is None:
        return f"I couldn't find {name}."
    _pending_delete_path = source
    return f"Are you sure you want to delete {source}? Say yes or no."


def confirm_delete():
    global _pending_delete_path
    source, _pending_delete_path = _pending_delete_path, None
    if source is None:
        return "No delete action is waiting for confirmation."
    try:
        if source.is_dir():
            shutil.rmtree(source)
        else:
            source.unlink()
        return f"Deleted {source.name}."
    except FileNotFoundError:
        return "That file or folder is no longer available."
    except (OSError, PermissionError) as error:
        return f"Couldn't delete {source.name}: {error}"


def cancel_delete():
    global _pending_delete_path
    _pending_delete_path = None
    return "Delete cancelled."
