import re
from pathlib import Path

from tools.app_tools import (
    open_chrome,
    open_calculator,
    open_notepad,
    open_vscode,
    open_explorer,
    open_excel,
    open_path,
    search_google,
    open_chrome_profile,
    open_url,
    open_website,
    search_youtube,
)

from tools.file_tools import (
    search_pdfs,
    search_images,
    search_videos,
    search_audio,
    find_matching_files,
    FILE_TYPE_EXTENSIONS,
    find_largest_file,
    cancel_delete,
    confirm_delete,
    copy_item,
    create_folder,
    create_text_file,
    move_item,
    rename_item,
    request_delete,
)

from analysis.pattern_analyzer import (
    analyze_pattern,
)

from tools.excel_tools import (
    update_student_mark,
    get_student_mark,
    get_all_student_marks,
    add_student,
    increase_student_mark,
)

from memory.context import (
    load_memory,
    remember,
    recall,
    show_memory,
    clear_memory,
)

from tools.utility_tools import (
    calculate,
    current_date,
    current_time,
    network_information,
    system_information,
)


last_search_results = []


def open_search_result(target):
    """Open one item from the current, in-memory file-search results."""
    global last_search_results
    if not last_search_results:
        if target.lower() in {"first", "last"} or target.isdigit():
            return "Please search for a file first."
        return open_path(target)

    if target.lower() == "first":
        matches = [last_search_results[0]]
    elif target.lower() == "last":
        matches = [last_search_results[-1]]
    elif target.isdigit():
        number = int(target)
        if not 1 <= number <= len(last_search_results):
            return f"I only found {len(last_search_results)} results."
        matches = [last_search_results[number - 1]]
    else:
        wanted = target.lower()
        matches = [file for file in last_search_results if wanted in file.name.lower()]
        if not matches:
            return "I couldn't find that file in the current results."

    if len(matches) > 1:
        last_search_results = matches
        return "I found multiple matching results:\n\n" + "\n".join(
            f"{index}. {file.name}" for index, file in enumerate(matches, 1)
        )

    try:
        import os
        os.startfile(str(matches[0]))
        return f"Opening {matches[0].name}."
    except OSError:
        return f"I couldn't open {matches[0].name}."


def format_file_size(size):
    for unit in ("bytes", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}" if unit != "bytes" else f"{size} bytes"
        size /= 1024


def best_resume_files(files):
    """Return only the best real resume candidates, excluding templates."""
    memory_name = load_memory().get("name", "").lower()
    name_parts = [part for part in memory_name.split() if len(part) > 2]
    candidates = [
        file for file in files
        if "resume" in file.stem.lower() and "template" not in file.name.lower()
    ]
    if not candidates:
        return []

    def score(file):
        name = file.name.lower()
        value = 10
        if file.suffix.lower() in {".docx", ".pdf"}:
            value += 100
        if "resume" in file.stem.lower():
            value += 20
        if name_parts and any(part in name for part in name_parts):
            value += 50
        if file.stem.lower() == "resume":
            value += 10
        return value

    highest_score = max(score(file) for file in candidates)
    return [file for file in candidates if score(file) == highest_score]

from tools.tasks import (
    add_task,
    clear_all_tasks,
    clear_completed_tasks,
    complete_task,
    remove_task,
    show_tasks,
)

from tools.learner import learn_and_execute


# -------------------------------------------------
# STUDENT NAME CLEANING
# -------------------------------------------------

def clean_student_name(name):
    return re.sub(r"['’]s$", "", name.strip())


# -------------------------------------------------
# MAIN ACTION EXECUTOR
# -------------------------------------------------

def execute_action(command):

    global last_search_results

    action = command.get("action")


    # -------------------------------------------------
    # VOICE / CHAT CONTROLS
    # -------------------------------------------------

    if action == "MODE_CONTROL":

        if command.get("message"):
            return command.get("message")

        mode = command.get("mode", "Mode").capitalize()
        status = "enabled" if command.get("enabled") else "disabled"

        return f"{mode} mode {status}."


    # -------------------------------------------------
    # BASIC CONVERSATION
    # -------------------------------------------------

    if action == "CONVERSATION":
        responses = {
            "HELLO": "I'm here bro! ⚡",
            "HI": "I'm here bro! ⚡",
            "HEY": "I'm here bro! ⚡",
            "GOOD_MORNING": "Good morning bro! ⚡",
            "GOOD_AFTERNOON": "Good afternoon bro! ⚡",
            "GOOD_EVENING": "Good evening bro! ⚡",
            "HOW_ARE_YOU": "I'm doing great bro! ⚡",
            "WHO_ARE_YOU": "I'm SPARK, your desktop assistant. ⚡",
            "WHAT_CAN_YOU_DO": "I can help with files, apps, memory, Excel, tasks, system information, and more. ⚡",
            "HELP": "Ask me to open apps, search files, manage memory, Excel marks, tasks, or system information. ⚡",
            "THANKS": "You're welcome bro! ⚡",
        }
        return responses.get(command.get("type"), "I'm here bro! ⚡")


    # -------------------------------------------------
    # EXIT
    # -------------------------------------------------

    if action == "EXIT":
        return "Goodbye bro! ⚡"

    if action == "POWER_CONTROL_DISABLED":
        return "I don't have computer power controls enabled."

    if action == "CALCULATOR":
        return calculate(command.get("expression", ""))

    if action in {"SYSTEM_INFO", "SYSTEM_INFORMATION"}:
        return system_information()

    if action == "NETWORK_INFORMATION":
        return network_information()

    if action == "TIME":
        return current_time()

    if action == "DATE":
        return current_date()

    if action == "TASK_ADD":
        return add_task(command.get("task", ""))

    if action == "TASK_SHOW":
        return show_tasks()

    if action == "TASK_COMPLETE":
        return complete_task(command.get("number"))

    if action == "TASK_REMOVE":
        return remove_task(command.get("number"))

    if action == "TASK_CLEAR_COMPLETED":
        return clear_completed_tasks()

    if action == "TASK_CLEAR_ALL":
        return "Are you sure you want to clear all tasks? Say yes or no."

    if action == "TASK_CLEAR_ALL_CONFIRM":
        return clear_all_tasks()

    if action == "TASK_CLEAR_ALL_CANCEL":
        return "Okay bro, I kept your tasks. ⚡"

    if action == "WEB_OPEN":
        return open_website(command.get("website", ""))

    if action == "OPEN_WEBSITE_URL":
        return open_url(command.get("url", ""))

    if action == "FILE_CREATE_FOLDER":
        return create_folder(command.get("name", ""), command.get("location"))

    if action == "FILE_CREATE_TEXT":
        return create_text_file(command.get("name", ""), command.get("location"))

    if action == "FILE_RENAME":
        return rename_item(command.get("source", ""), command.get("destination", ""))

    if action == "FILE_COPY":
        return copy_item(command.get("source", ""), command.get("location", ""))

    if action == "FILE_MOVE":
        return move_item(command.get("source", ""), command.get("location", ""))

    if action == "FILE_DELETE":
        return request_delete(command.get("source", ""))

    if action == "FILE_DELETE_CONFIRM":
        return confirm_delete()

    if action == "FILE_DELETE_CANCEL":
        return cancel_delete()


    # -------------------------------------------------
    # CHROME PROFILE
    # -------------------------------------------------

    if action == "CHROME_PROFILE_REQUEST":
        return "Which Chrome account should I use?"

    if action == "CHROME_PROFILE_OPEN":

        account = command.get("account")
        query = command.get("query")

        if query is None:
            return open_chrome_profile(account)

        return search_google(query, account)


    # -------------------------------------------------
    # BROWSER SEARCH
    # -------------------------------------------------

    if action == "BROWSER_SEARCH":

        query = command.get("query")

        if not query:
            return "Please tell me what you want to search for."

        return search_google(query)


    # -------------------------------------------------
    # WEB SEARCH
    # -------------------------------------------------

    if action == "WEB_SEARCH":

        engine = command.get("engine")
        query = command.get("query")

        if engine == "youtube":
            return search_youtube(query)

        return search_google(query)


    # -------------------------------------------------
    # OPEN APPLICATION
    # -------------------------------------------------

    if action == "OPEN_APP":

        target = command.get("target")

        if target == "chrome":
            return open_chrome()

        elif target == "calculator":
            return open_calculator()

        elif target == "notepad":
            return open_notepad()

        elif target == "vscode":
            return open_vscode()

        elif target == "explorer":
            return open_explorer()

        elif target == "excel":
            return open_excel()

        return "I don't know that application yet."


    # -------------------------------------------------
    # OPEN FILE / FOLDER
    # -------------------------------------------------

    if action == "OPEN_SEARCH_RESULT":

        target = command.get("target")

        if not target:
            return "Please tell me what you want me to open."

        return open_search_result(target)

    if action == "OPEN_PATH":

        target = command.get("target")

        if not target:
            return "Please tell me what you want me to open."

        return open_path(target)

    if action == "SEARCH_AND_OPEN_FILE":

        files = find_matching_files(command.get("description", ""))
        if "resume" in command.get("description", "").lower():
            files = best_resume_files(files)
        if not files:
            return "I couldn't find any matching files."

        last_search_results = files
        if len(files) == 1:
            return open_search_result("1")

        return "I found multiple matching files:\n\n" + "\n".join(
            f"{index}. {file.name}" for index, file in enumerate(files, 1)
        ) + "\n\nPlease say open 1, open first, or open last."

    if action == "FIND_LARGEST_FILE":

        folder = command.get("folder")
        file = find_largest_file(folder)

        if file is None:
            return f"I couldn't find any files in {folder.title()}."

        try:
            size = format_file_size(file.stat().st_size)
        except OSError:
            return f"I couldn't read the size of {file.name}."

        return (
            f"The largest file in {folder.title()} is:\n"
            f"{file.name}\n"
            f"Size: {size}\n"
            f"Path: {file}"
        )


    # -------------------------------------------------
    # FILE SEARCH
    # -------------------------------------------------

    if action == "SEARCH_FILE":

        file_type = command.get("type")
        date_filter = command.get("date")
        time_filter = command.get("time")
        description = command.get("description", "")

        # Search by description
        if description:

            files = find_matching_files(
                description,
                date_filter,
                FILE_TYPE_EXTENSIONS.get(file_type),
                time_filter,
            )

        # Search by file type
        elif file_type == "pdf":

            files = search_pdfs(date_filter, time_filter)

        elif file_type == "image":

            files = search_images(date_filter, time_filter)

        elif file_type == "video":

            files = search_videos(date_filter, time_filter)

        elif file_type == "audio":

            files = search_audio(date_filter, time_filter)

        else:

            return "I don't know that file type yet."


        # No results
        if not files:

            last_search_results = []

            label = {"image": "photos", "video": "videos", "audio": "audio"}.get(
                file_type, "files"
            )

            if date_filter:

                return f"I couldn't find any matching {label}."

            return f"I couldn't find any matching {label}."


        last_search_results = files
        label = {"image": "photos", "video": "videos", "audio": "audio"}.get(
            file_type, "matching files"
        )
        return "I found {} {}:\n\n{}".format(
            len(files), label,
            "\n".join(f"{index}. {file.name}" for index, file in enumerate(files, 1))
        )


    # -------------------------------------------------
    # PATTERN ANALYSIS
    # -------------------------------------------------

    if action == "PATTERN_ANALYSIS":

        original_command = command.get(
            "original_command",
            ""
        )

        return analyze_pattern(original_command)


    # -------------------------------------------------
    # EXCEL CONTROL
    # -------------------------------------------------

    if action == "EXCEL_CONTROL":

        original_command = command.get(
            "original_command",
            ""
        )

        excel_type = command.get("type")

        # Change this ONLY if your Excel file
        # is located somewhere else.
        file_path = Path.home() / "OneDrive" / "Documents" / "test.xlsx"

        if not file_path.is_file():
            return f"I couldn't find the Excel file at {file_path}."


        # -------------------------------------------------
        # GET STUDENT MARK
        # -------------------------------------------------

        if excel_type == "GET_MARK":

            match = re.search(
                r"what is (.+?) mark",
                original_command
            )

            if not match:

                return (
                    "Please tell me the student's name."
                )

            student_name = clean_student_name(
                match.group(1)
            )

            return get_student_mark(
                file_path,
                student_name
            )


        # -------------------------------------------------
        # SHOW ALL MARKS
        # -------------------------------------------------

        elif excel_type == "SHOW_ALL_MARKS":

            return get_all_student_marks(
                file_path
            )


        # -------------------------------------------------
        # ADD STUDENT
        # -------------------------------------------------

        elif excel_type == "ADD_STUDENT":

            match = re.search(
                r"add (.+?) with mark (\d+(?:\.\d+)?)",
                original_command
            )

            if not match:

                return (
                    "Please use: "
                    "add Arun with mark 88"
                )

            mark = float(
                match.group(2)
            )

            if mark.is_integer():
                mark = int(mark)

            student_name = clean_student_name(
                match.group(1)
            )

            return add_student(
                file_path,
                student_name,
                mark
            )


        # -------------------------------------------------
        # INCREASE MARK
        # -------------------------------------------------

        elif excel_type == "INCREASE_MARK":

            match = re.search(
                r"increase (.+?) mark by (\d+(?:\.\d+)?)",
                original_command
            )

            if not match:

                return (
                    "Please use: "
                    "increase Kavin mark by 5"
                )

            amount = float(
                match.group(2)
            )

            if amount.is_integer():
                amount = int(amount)

            student_name = clean_student_name(
                match.group(1)
            )

            return increase_student_mark(
                file_path,
                student_name,
                amount
            )


        # -------------------------------------------------
        # UPDATE / CHANGE MARK
        # -------------------------------------------------

        elif excel_type == "UPDATE_MARK":

            numbers = re.findall(
                r"\b\d+(?:\.\d+)?\b",
                original_command
            )

            if not numbers:

                return (
                    "Please tell me the mark to set."
                )

            mark = float(
                numbers[-1]
            )

            if mark.is_integer():
                mark = int(mark)

            match = re.search(
                r"(?:change|update|set)\s+(.+?)\s+mark",
                original_command
            )

            if not match:

                return (
                    "Please use: "
                    "change Madhan mark to 95"
                )

            student_name = clean_student_name(
                match.group(1)
            )

            return update_student_mark(
                file_path,
                student_name,
                mark
            )


        return (
            "I don't know that Excel operation yet."
        )


    # -------------------------------------------------
    # MEMORY
    # -------------------------------------------------

    if action == "MEMORY":

        memory_type = command.get("type")


        # Remember
        if memory_type == "REMEMBER":

            return remember(
                command.get("key"),
                command.get("value")
            )


        # Recall
        elif memory_type == "RECALL":

            return recall(
                command.get("key")
            )


        # Show memory
        elif memory_type == "SHOW":

            return show_memory()


        # Clear memory
        elif memory_type == "CLEAR":

            return clear_memory()


        return (
            "I don't understand that memory command."
        )


    # -------------------------------------------------
    # UNKNOWN
    # -------------------------------------------------

    if action == "UNKNOWN":

        return learn_and_execute(command.get("original_command", ""))

    return (
        "I don't know how to perform that task yet. Try asking me to open an "
        "app, search files, manage Excel marks, analyze a pattern, calculate something, "
        "or check system information."
    )
