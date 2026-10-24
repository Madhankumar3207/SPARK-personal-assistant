import re
from datetime import datetime


awaiting_chrome_profile = False
pending_chrome_query = None
active_chrome_account = None
pending_file_delete = False
pending_task_clear = False


def understand_command(command):

    global awaiting_chrome_profile
    global pending_chrome_query
    global active_chrome_account
    global pending_file_delete
    global pending_task_clear

    # -------------------------------------------------
    # CLEAN COMMAND
    # -------------------------------------------------

    original_text = command.strip()
    command = original_text.lower()

    if not command:
        return {"action": "UNKNOWN", "original_command": ""}

    if pending_file_delete:
        if command in {"yes", "yes delete it", "confirm", "go ahead", "delete it"}:
            pending_file_delete = False
            return {"action": "FILE_DELETE_CONFIRM"}
        if command in {"no", "cancel", "don't delete", "stop"}:
            pending_file_delete = False
            return {"action": "FILE_DELETE_CANCEL"}
        # A confirmation must apply only to the immediately pending action.
        pending_file_delete = False

    if pending_task_clear:
        if command in {"yes", "confirm", "go ahead"}:
            pending_task_clear = False
            return {"action": "TASK_CLEAR_ALL_CONFIRM"}
        if command in {"no", "cancel", "stop"}:
            pending_task_clear = False
            return {"action": "TASK_CLEAR_ALL_CANCEL"}
        pending_task_clear = False

    mode_controls = {
        "voice on": ("voice", True),
        "turn voice on": ("voice", True),
        "start voice": ("voice", True),
        "enable voice": ("voice", True),
        "voice mode on": ("voice", True),
        "voice off": ("voice", False),
        "turn voice off": ("voice", False),
        "stop voice": ("voice", False),
        "disable voice": ("voice", False),
        "voice mode off": ("voice", False),
        "chat on": ("chat", True),
        "turn chat on": ("chat", True),
        "start chat": ("chat", True),
        "enable chat": ("chat", True),
        "chat off": ("chat", False),
        "turn chat off": ("chat", False),
        "disable chat": ("chat", False)
    }

    if command in mode_controls:

        mode, enabled = mode_controls[command]

        return {
            "action": "MODE_CONTROL",
            "mode": mode,
            "enabled": enabled
        }

    if command.isdigit():
        return {"action": "OPEN_SEARCH_RESULT", "target": command}

    natural_memory_match = re.match(
        r"^(?:my name is|i am|call me)\s+(.+)$",
        command
    )

    if natural_memory_match:

        return {
            "action": "MEMORY",
            "type": "REMEMBER",
            "key": "name",
            "value": natural_memory_match.group(1).strip()
        }

    # -------------------------------------------------
    # BASIC CONVERSATION
    # -------------------------------------------------

    if command in [
        "hello",
        "hello spark",
    ]:
        return {
            "action": "CONVERSATION",
            "type": "HELLO"
        }

    if command in [
        "hi",
        "hi spark",
    ]:
        return {
            "action": "CONVERSATION",
            "type": "HI"
        }

    if command in [
        "hey",
        "hey spark",
    ]:
        return {
            "action": "CONVERSATION",
            "type": "HEY"
        }

    if command == "good morning":
        return {
            "action": "CONVERSATION",
            "type": "GOOD_MORNING"
        }

    if command == "good afternoon":
        return {
            "action": "CONVERSATION",
            "type": "GOOD_AFTERNOON"
        }

    if command == "good evening":
        return {
            "action": "CONVERSATION",
            "type": "GOOD_EVENING"
        }

    if command == "how are you":
        return {
            "action": "CONVERSATION",
            "type": "HOW_ARE_YOU"
        }

    if command == "who are you":
        return {
            "action": "CONVERSATION",
            "type": "WHO_ARE_YOU"
        }

    if command == "what can you do":
        return {
            "action": "CONVERSATION",
            "type": "WHAT_CAN_YOU_DO"
        }

    if command == "help":
        return {
            "action": "CONVERSATION",
            "type": "HELP"
        }

    if command in {"thanks", "thank you", "thanks spark", "thank you spark"}:
        return {"action": "CONVERSATION", "type": "THANKS"}

    if command in {"general", "okay", "ok", "fine", "good"}:
        return {"action": "CONVERSATION", "type": "READY"}

    # -------------------------------------------------
    # EXIT
    # -------------------------------------------------

    if command in ["exit", "quit", "exit spark", "quit spark"]:
        return {
            "action": "EXIT"
        }

    if command in {"bye", "bye spark"}:
        return {"action": "CONVERSATION", "type": "BYE"}

    if command in {
        "shutdown", "shut down", "shutdown computer", "shut down computer",
        "restart", "restart computer", "reboot computer", "lock", "lock computer",
        "sleep", "sleep computer", "hibernate", "hibernate computer",
        "sign out", "sign out computer", "log out", "log out computer",
    } or re.match(r"^(?:(?:shut ?down|restart|reboot|lock|sleep|hibernate|sign out|log out) (?:my )?(?:computer|pc|laptop)|turn off (?:my )?(?:computer|pc|laptop))$", command):
        return {"action": "POWER_CONTROL_DISABLED"}

    # -------------------------------------------------
    # NEW UTILITY COMMANDS (specific checks before generic routing)
    # -------------------------------------------------

    if command in [
        "what is my system", "system information", "show system info",
        "show my system", "show my system information", "show system information",
        "system specs", "show my system specs", "what computer am i using",
        "what processor do i have", "what cpu do i have", "how much ram do i have",
        "what graphics card do i have", "what gpu do i have",
        "what windows version am i using", "what operating system am i using",
        "how much storage do i have",
    ]:
        return {"action": "SYSTEM_INFORMATION"}

    if command in [
        "show my ip", "what is my ip", "what is my ip address", "show my ip address",
        "show network information", "network information", "what network am i connected to",
        "what wifi am i connected to", "what wifi am i using", "is my internet connected",
        "check my internet", "check network connection",
    ]:
        return {"action": "NETWORK_INFORMATION"}

    if command in ["what time is it", "current time", "tell me the time"]:
        return {"action": "TIME"}

    if command in ["what is today's date", "what is todays date", "what date is it", "current date", "today's date"]:
        return {"action": "DATE"}

    calculator_match = re.match(r"^(?:calculate|what is)\s+(.+)$", command)
    if calculator_match and re.search(r"(?:\d|zero|one|two|three|four|five|six|seven|eight|nine|ten|plus|minus|times|divided|\+|\-|\*|/|\^|%)", calculator_match.group(1)):
        return {"action": "CALCULATOR", "expression": calculator_match.group(1).strip()}

    # -------------------------------------------------
    # TASK MANAGEMENT
    # -------------------------------------------------

    if command in {"show my tasks", "show tasks", "my tasks", "what are my tasks", "list my tasks", "list tasks", "view my tasks", "pending tasks"}:
        return {"action": "TASK_SHOW"}

    if command in {"clear completed tasks", "remove completed tasks", "delete completed tasks"}:
        return {"action": "TASK_CLEAR_COMPLETED"}

    if command in {"clear all tasks", "delete all tasks", "remove all tasks"}:
        pending_task_clear = True
        return {"action": "TASK_CLEAR_ALL"}

    add_match = re.match(r"^(?:add|create)(?: a)? task(?:\s+(.+))?$", command)
    if not add_match:
        add_match = re.match(r"^remind me to\s+(.+)$", command)
    if not add_match:
        add_match = re.match(r"^task\s+(.+)$", command)
    if add_match:
        if add_match.group(1):
            task_text = original_text[add_match.start(1):add_match.end(1)].strip()
        else:
            task_text = ""
        return {"action": "TASK_ADD", "task": task_text}

    ordinal_numbers = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5}
    complete_match = re.match(r"^(?:complete|finish) (?:task )?(\d+)$", command)
    ordinal_match = re.match(r"^(?:complete|finish) my (first|second|third|fourth|fifth) task$", command)
    mark_match = re.match(r"^mark task (\d+) complete$", command)
    if complete_match or ordinal_match or mark_match:
        number = int((complete_match or mark_match).group(1)) if (complete_match or mark_match) else ordinal_numbers[ordinal_match.group(1)]
        return {"action": "TASK_COMPLETE", "number": number}
    if command.startswith("complete task") or command.startswith("finish task") or command.startswith("mark task"):
        return {"action": "TASK_COMPLETE", "number": None}

    remove_match = re.match(r"^(?:remove|delete) (?:task )?(\d+)$", command)
    remove_ordinal = re.match(r"^(?:remove|delete) my (first|second|third|fourth|fifth) task$", command)
    if remove_match or remove_ordinal:
        number = int(remove_match.group(1)) if remove_match else ordinal_numbers[remove_ordinal.group(1)]
        return {"action": "TASK_REMOVE", "number": number}
    if command.startswith("remove task") or command.startswith("delete task"):
        return {"action": "TASK_REMOVE", "number": None}

    if awaiting_chrome_profile:

        awaiting_chrome_profile = False
        active_chrome_account = command

        return {
            "action": "CHROME_PROFILE_OPEN",
            "account": command,
            "query": pending_chrome_query
        }

    # -------------------------------------------------
    # MEMORY - REMEMBER
    # -------------------------------------------------

    if command.startswith("remember "):

        text = command[9:].strip()

        text = re.sub(
            r"^that\s+",
            "",
            text
        )

        match = re.search(
            r"my (.+?) is (.+)",
            text
        )

        if match:

            key = match.group(1).strip()
            value = match.group(2).strip()

            return {
                "action": "MEMORY",
                "type": "REMEMBER",
                "key": key,
                "value": value
            }

        return {
            "action": "MEMORY",
            "type": "REMEMBER",
            "key": "note",
            "value": text
        }

    # -------------------------------------------------
    # MEMORY - RECALL
    # -------------------------------------------------

    match = re.match(
        r"(?:what\s+is+s?|what'?s|tell\s+me|do\s+you\s+remember)\s+my\s+(.+)",
        command
    )

    if match:

        key = match.group(1).strip()

        return {
            "action": "MEMORY",
            "type": "RECALL",
            "key": key
        }

    # -------------------------------------------------
    # MEMORY - SHOW
    # -------------------------------------------------

    if command in [
        "show my memory",
        "show my memories",
        "show memory",
        "what did i ask you to remember",
        "what do you remember about me",
        "what do you remember",
        "what do you know about me",
        "tell me what you remember",
        "what have you remembered"
    ]:

        return {
            "action": "MEMORY",
            "type": "SHOW"
        }

    # -------------------------------------------------
    # MEMORY - CLEAR
    # -------------------------------------------------

    if command in [
        "clear my memory",
        "clear memory",
        "forget everything"
    ]:

        return {
            "action": "MEMORY",
            "type": "CLEAR"
        }

    # -------------------------------------------------
    # PATTERN ANALYSIS
    # -------------------------------------------------

    if "pattern" in command or "analyze" in command or "analyse" in command:

        return {
            "action": "PATTERN_ANALYSIS",
            "original_command": command
        }

    # -------------------------------------------------
    # WEB OPENING AND FILE MANAGEMENT
    # -------------------------------------------------

    website = re.match(r"^open (google|youtube|gmail|github|chatgpt|instagram|linkedin|whatsapp|whatsapp web|facebook|amazon|microsoft|wikipedia|google drive|google maps)$", command)
    if website:
        return {"action": "WEB_OPEN", "website": website.group(1)}

    url_match = re.match(r"^open\s+(https?://\S+)$", command)
    if url_match:
        return {"action": "OPEN_WEBSITE_URL", "url": url_match.group(1)}

    if command == "open a website":
        return {"action": "OPEN_WEBSITE_URL", "url": ""}

    # File searches are deterministic and take precedence over browser search.
    if re.match(r"^(?:find|search for|search|show)\b", command):
        search_text = re.sub(r"^(?:find|search(?:\s+for)?|show)(?:\s+for)?\s+", "", command).strip()
        find_open = re.match(r"^(.+?)\s+and\s+open(?:\s+it)?$", search_text)
        if find_open:
            return {"action": "SEARCH_AND_OPEN_FILE", "description": re.sub(r"^(?:my|the|a|an)\s+", "", find_open.group(1)).strip()}
        file_type = None
        if re.search(r"\bpdfs?\b", search_text):
            file_type = "pdf"
        elif re.search(r"\b(?:images?|photos?)\b", search_text):
            file_type = "image"
        elif re.search(r"\bvideos?\b", search_text):
            file_type = "video"
        elif re.search(r"\b(?:audio|audios|music)\b", search_text):
            file_type = "audio"
        description = re.sub(r"\b(?:pdfs?|images?|photos?|videos?|audios?|music|files?)\b", "", search_text).strip()
        if file_type or description:
            return {"action": "SEARCH_FILE", "type": file_type, "date": None, "time": None, "description": re.sub(r"^(?:my|the|a|an)\s+", "", description).strip()}

    folder_match = re.match(r"^create (?:a )?folder (?:in|on) (desktop|downloads|documents|pictures|videos|music) (?:called|named) (.+)$", command)
    if folder_match:
        return {"action": "FILE_CREATE_FOLDER", "name": folder_match.group(2).strip(), "location": folder_match.group(1)}
    folder_match = re.match(r"^create (?:a )?folder (?:called|named) (.+?)(?: (?:in|on) (desktop|downloads|documents|pictures|videos|music))?$", command)
    if not folder_match:
        folder_match = re.match(r"^create (.+?) folder(?: (?:in|on) (desktop|downloads|documents|pictures|videos|music))?$", command)
    if folder_match:
        return {"action": "FILE_CREATE_FOLDER", "name": folder_match.group(1).strip(), "location": folder_match.group(2)}

    text_match = re.match(r"^create (?:a )?(?:text )?file (?:called )?(.+?)(?: (?:in|on) (desktop|downloads|documents|pictures|videos|music))?$", command)
    if not text_match:
        text_match = re.match(r"^create (.+?\.txt)(?: (?:in|on) (desktop|downloads|documents|pictures|videos|music))?$", command)
    if text_match:
        return {"action": "FILE_CREATE_TEXT", "name": text_match.group(1).strip(), "location": text_match.group(2)}

    rename_match = re.match(r"^rename (?:the )?(?:folder )?(.+?) to (.+)$", command)
    if rename_match:
        return {"action": "FILE_RENAME", "source": rename_match.group(1).strip(), "destination": rename_match.group(2).strip()}

    transfer_match = re.match(r"^(copy|move) (?:the )?(?:folder )?(.+?) to (desktop|downloads|documents|pictures|videos|music)$", command)
    if transfer_match:
        return {"action": "FILE_COPY" if transfer_match.group(1) == "copy" else "FILE_MOVE", "source": transfer_match.group(2).strip(), "location": transfer_match.group(3)}

    delete_match = re.match(r"^delete (?:the )?(file|folder)\s+(.+)$", command)
    if delete_match:
        pending_file_delete = True
        return {"action": "FILE_DELETE", "source": delete_match.group(2).strip()}

    # -------------------------------------------------
    # BROWSER SEARCH
    # -------------------------------------------------

    match = re.match(
        r"^search youtube for\s+(.+)$",
        command
    )

    if not match:
        match = re.match(r"^youtube\s+(.+)$", command)

    if match:

        return {
            "action": "WEB_SEARCH",
            "engine": "youtube",
            "query": match.group(1).strip()
        }

    match = re.match(
        r"^search (?:the )?web for\s+(.+)$",
        command
    )

    if match:

        return {
            "action": "WEB_SEARCH",
            "engine": "google",
            "query": match.group(1).strip()
        }

    chrome_query = None

    match = re.match(
        r"^open chrome (?:in|start|with) (.+?) and search(?: for)?\s+(.+)$",
        command
    )

    if match:

        return {
            "action": "CHROME_PROFILE_OPEN",
            "account": match.group(1).strip(),
            "query": match.group(2).strip()
        }

    match = re.match(
        r"^open chrome (?:in|start|with)\s+(.+)$",
        command
    )

    if match:

        return {
            "action": "CHROME_PROFILE_OPEN",
            "account": match.group(1).strip(),
            "query": None
        }

    match = re.match(
        r"^open chrome and search(?: for)?\s+(.+)$",
        command
    )

    if match:
        chrome_query = match.group(1).strip()

    match = re.match(
        r"^search google(?: for)?(?:\s+(.+))?$",
        command
    )

    if match:
        chrome_query = (match.group(1) or "").strip()

    match = re.match(r"^google\s+(.+)$", command)

    if match:
        chrome_query = match.group(1).strip()

    match = re.match(r"^search for\s+(.+)\s+on google$", command)

    if match:
        chrome_query = match.group(1).strip()

    if chrome_query is not None:

        if active_chrome_account:

            return {
                "action": "CHROME_PROFILE_OPEN",
                "account": active_chrome_account,
                "query": chrome_query
            }

        return {"action": "WEB_SEARCH", "engine": "google", "query": chrome_query}

    if command.startswith("search "):

        query = re.sub(
            r"^search(?: for)?\s+",
            "",
            command
        )

        file_search_terms = [
            "pdf",
            "image",
            "images",
            "photo",
            "photos",
            "video",
            "videos",
            "audio",
            "audios",
            "music"
        ]

        if (
            query
            and not query.startswith("my ")
            and not any(
                term in query
                for term in file_search_terms
            )
        ):

            return {
                "action": "BROWSER_SEARCH",
                "query": query
            }

    # -------------------------------------------------
    # APP CONTROL
    # -------------------------------------------------

    if "open" in command and "chrome" in command:

        return {
            "action": "OPEN_APP",
            "target": "chrome"
        }

    elif "open" in command and "calculator" in command:

        return {
            "action": "OPEN_APP",
            "target": "calculator"
        }

    elif "open" in command and "notepad" in command:

        return {
            "action": "OPEN_APP",
            "target": "notepad"
        }

    elif "open" in command and (
        "vscode" in command or
        "vs code" in command
    ):

        return {
            "action": "OPEN_APP",
            "target": "vscode"
        }

    elif "open" in command and (
        "file explorer" in command or
        command == "open explorer"
    ):

        return {
            "action": "OPEN_APP",
            "target": "explorer"
        }

    elif "open" in command and "excel" in command:

        return {
            "action": "OPEN_APP",
            "target": "excel"
        }

    # -------------------------------------------------
    # OPEN FILE / FOLDER
    # -------------------------------------------------

    if command.startswith("open "):

        target = command[5:].strip()

        target = re.sub(
            r"^(my|the)\s+",
            "",
            target
        )

        target = re.sub(
            r"\s+(file|folder)$",
            "",
            target
        )

        target = re.sub(
            r"\s+excel$",
            "",
            target
        )

        target = target.strip()

        if target:

            return {
                "action": "OPEN_SEARCH_RESULT",
                "target": target
            }

    # -------------------------------------------------
    # EXCEL CONTROL - UPDATE MARK
    # -------------------------------------------------

    if (
        ("change" in command or
         "update" in command or
         "set" in command)
        and "mark" in command
    ):

        return {
            "action": "EXCEL_CONTROL",
            "type": "UPDATE_MARK",
            "original_command": command
        }

    # -------------------------------------------------
    # GET MARK
    # -------------------------------------------------

    if "what is" in command and "mark" in command:

        return {
            "action": "EXCEL_CONTROL",
            "type": "GET_MARK",
            "original_command": command
        }

    # -------------------------------------------------
    # SHOW ALL MARKS
    # -------------------------------------------------

    if (
        "show all" in command
        and "mark" in command
    ):

        return {
            "action": "EXCEL_CONTROL",
            "type": "SHOW_ALL_MARKS",
            "original_command": command
        }

    # -------------------------------------------------
    # ADD STUDENT
    # -------------------------------------------------

    if (
        "add" in command
        and "mark" in command
    ):

        return {
            "action": "EXCEL_CONTROL",
            "type": "ADD_STUDENT",
            "original_command": command
        }

    # -------------------------------------------------
    # INCREASE MARK
    # -------------------------------------------------

    if (
        "increase" in command
        and "mark" in command
    ):

        return {
            "action": "EXCEL_CONTROL",
            "type": "INCREASE_MARK",
            "original_command": command
        }

    # -------------------------------------------------
    # FILE SEARCH
    # -------------------------------------------------

    largest_file_match = (
        re.search(r"\b(?:largest|biggest)\b", command)
        and re.search(r"\bfile\b", command)
        and re.search(
            r"\b(downloads|desktop|documents|pictures|videos|music)\b",
            command
        )
    )

    if largest_file_match:

        return {
            "action": "FIND_LARGEST_FILE",
            "folder": largest_file_match.group(1)
        }

    find_and_open_match = re.match(r"^find\s+(?:my\s+)?(.+?)\s+and\s+open$", command)
    if find_and_open_match:
        return {
            "action": "SEARCH_AND_OPEN_FILE",
            "description": find_and_open_match.group(1).strip(),
        }

    if any(
        word in command
        for word in ["find", "search", "show"]
    ):

        if "pdf" in command:

            file_type = "pdf"

        elif (
            "image" in command or
            "images" in command or
            "photo" in command or
            "photos" in command
        ):

            file_type = "image"

        elif (
            "video" in command or
            "videos" in command
        ):

            file_type = "video"

        elif (
            "audio" in command or
            "audios" in command or
            "music" in command
        ):

            file_type = "audio"

        else:

            file_type = None

        date = None

        if "yesterday" in command:

            date = "yesterday"

        elif "today" in command:

            date = "today"

        elif "this week" in command:

            date = "this_week"

        else:

            date_match = re.search(r"\bfrom\s+(\d{4}-\d{2}-\d{2})\b", command)
            if date_match:
                try:
                    datetime.strptime(date_match.group(1), "%Y-%m-%d")
                    date = date_match.group(1)
                except ValueError:
                    pass

        time_filter = None
        time_match = re.search(r"\b(?:at|around)\s+(\d{1,2})(?::\d{2})?\s*(a\.?(?:m)\.?|p\.?(?:m)\.?)\b", command)
        if time_match:
            hour = int(time_match.group(1))
            meridiem = time_match.group(2)[0]
            if 1 <= hour <= 12:
                time_filter = (hour % 12) + (12 if meridiem == "p" else 0)

        description = ""

        if (
            command.startswith("find ")
            or command.startswith("search ")
            or command.startswith("show ")
        ):

            description = re.sub(
                r"^(find|search|show)(\s+for)?\s+",
                "",
                command
            )

            description = re.sub(
                r"\b(pdfs?|images?|photos?|videos?|audios?|music)\b",
                "",
                description
            )

            description = re.sub(
                r"\b(today|yesterday|this week)\b",
                "",
                description
            )

            description = re.sub(
                r"\bfrom\s+\d{4}-\d{2}-\d{2}\b",
                "",
                description
            )

            description = re.sub(r"\bfrom\b", "", description)

            description = re.sub(
                r"\b(?:at|around)\s+\d{1,2}(?::\d{2})?\s*(?:a\.?(?:m)\.?|p\.?(?:m)\.?)\b",
                "",
                description
            )

            description = re.sub(
                r"\bfiles?\s+from\b",
                "",
                description
            )

            description = re.sub(
                r"^(my|the|a|an)\s+",
                "",
                description
            ).strip()

        if file_type or description or date:

            return {
                "action": "SEARCH_FILE",
                "type": file_type,
                "date": date,
                "time": time_filter,
                "description": description,
            }

    # -------------------------------------------------
    # UNKNOWN
    # -------------------------------------------------

    return {
        "action": "UNKNOWN",
        "original_command": original_text,
    }
