"""Safe, offline utility actions for calculator and system requests."""

import ast
import ctypes
from datetime import datetime
import operator
import os
import platform
import re
import shutil
import socket
import subprocess
import sys


_OPERATORS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Mod: operator.mod, ast.Pow: operator.pow,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}

_NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40,
    "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80,
    "ninety": 90, "hundred": 100, "thousand": 1000,
}


def _number_words_to_digits(text):
    """Convert simple spoken number phrases without interpreting normal prose."""
    words = text.split()
    result, index = [], 0
    while index < len(words):
        if words[index] not in _NUMBER_WORDS:
            result.append(words[index])
            index += 1
            continue
        total = current = 0
        while index < len(words) and words[index] in _NUMBER_WORDS:
            value = _NUMBER_WORDS[words[index]]
            if value == 100:
                current = max(1, current) * value
            elif value == 1000:
                total += max(1, current) * value
                current = 0
            else:
                current += value
            index += 1
        result.append(str(total + current))
    return " ".join(result)


def _evaluate(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_evaluate(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        left, right = _evaluate(node.left), _evaluate(node.right)
        if abs(left) > 10**12 or abs(right) > 10**12 or (isinstance(node.op, ast.Pow) and abs(right) > 100):
            raise ValueError("That calculation is too large.")
        return _OPERATORS[type(node.op)](left, right)
    raise ValueError("Only basic arithmetic is supported.")


def calculate(expression):
    """Evaluate a basic arithmetic expression using a restricted AST, never eval."""
    expression = expression.lower().strip()
    expression = _number_words_to_digits(expression)
    percent = re.fullmatch(r"(.+?)\s*%\s+of\s+(.+)", expression)
    if percent:
        expression = f"({percent.group(1)} / 100) * ({percent.group(2)})"
    expression = (expression.replace("multiplied by", "*").replace("times", "*")
                 .replace("divided by", "/").replace("plus", "+")
                 .replace("minus", "-").replace("to the power of", "**")
                 .replace("^", "**"))
    if not re.fullmatch(r"[0-9+\-*/%.()\s]+", expression):
        return "Please use a basic arithmetic expression, such as: calculate (10 + 5) * 2."
    try:
        value = _evaluate(ast.parse(expression, mode="eval").body)
    except ZeroDivisionError:
        return "I can't divide by zero."
    except (SyntaxError, ValueError):
        return "I couldn't calculate that expression."
    display = int(value) if isinstance(value, float) and value.is_integer() else value
    return f"Answer: {display}"


def system_information():
    """Read local machine details with safe fallbacks for unavailable fields."""
    lines = [
        "System Information:",
        f"OS: {platform.system()} {platform.release()} ({platform.version()})",
        f"Computer: {platform.node() or 'Unavailable'}",
        f"CPU: {platform.processor() or platform.machine() or 'Not available'}",
        f"Python: {platform.python_version()}",
    ]
    ram = _total_ram_bytes()
    lines.append(f"RAM: {ram / (1024 ** 3):.1f} GB" if ram else "RAM: Not available")
    lines.append(f"GPU: {_first_command_line(['wmic', 'path', 'win32_VideoController', 'get', 'name']) or 'Not available'}")
    lines.append("Storage:")
    storage = _storage_lines()
    lines.extend(storage or ["Not available"])
    return "\n".join(lines)


def _total_ram_bytes():
    if os.name == "nt":
        class MemoryStatus(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("memory_load", ctypes.c_ulong),
                        ("total_phys", ctypes.c_ulonglong), ("avail_phys", ctypes.c_ulonglong),
                        ("total_page_file", ctypes.c_ulonglong), ("avail_page_file", ctypes.c_ulonglong),
                        ("total_virtual", ctypes.c_ulonglong), ("avail_virtual", ctypes.c_ulonglong),
                        ("avail_extended_virtual", ctypes.c_ulonglong)]
        try:
            status = MemoryStatus()
            status.length = ctypes.sizeof(status)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
            return status.total_phys
        except (AttributeError, OSError):
            return None
    if hasattr(os, "sysconf"):
        try:
            return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
        except (ValueError, OSError, AttributeError):
            return None
    return None


def _first_command_line(command):
    """Run a read-only local information query and return its first data line."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=3, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return lines[1] if len(lines) > 1 else None


def _storage_lines():
    drives = [f"{letter}:\\" for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{letter}:\\")]
    if not drives:
        drives = [os.path.abspath(os.sep)]
    lines = []
    for drive in drives:
        try:
            usage = shutil.disk_usage(drive)
            lines.append(f"{drive}: {usage.free / (1024 ** 3):.1f} GB free / {usage.total / (1024 ** 3):.1f} GB")
        except OSError:
            continue
    return lines


def network_information():
    """Return minimal local network status without exposing external identifiers."""
    hostname = socket.gethostname() or "Not available"
    try:
        local_ip = socket.gethostbyname(hostname)
        if local_ip.startswith("127."):
            raise OSError
    except OSError:
        local_ip = "Not available"
    wifi = _wifi_name() or "Not available"
    try:
        connection = socket.create_connection(("1.1.1.1", 53), timeout=1)
        connection.close()
        internet = "Connected"
    except OSError:
        internet = "Disconnected"
    return "\n".join([
        "Network Information:", f"Hostname: {hostname}", f"Local IP: {local_ip}",
        f"WiFi: {wifi}", f"Internet: {internet}",
    ])


def _wifi_name():
    try:
        result = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True, timeout=3, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    match = re.search(r"^\s*SSID\s*:\s*(.+)$", result.stdout, flags=re.MULTILINE | re.IGNORECASE)
    return match.group(1).strip() if match else None


def current_time():
    return "It's " + datetime.now().strftime("%I:%M %p").lstrip("0") + "."


def current_date():
    return "Today is " + datetime.now().strftime("%B %d, %Y").replace(" 0", " ") + "."
