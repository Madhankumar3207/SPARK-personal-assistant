"""Small, deterministic pattern recognizers used by SPARK."""

from collections import Counter
from statistics import median
import math
import re


NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30,
    "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
    "eighty": 80, "ninety": 90, "hundred": 100, "thousand": 1000,
}
NUMBER_NAMES = {value: name for name, value in NUMBER_WORDS.items()}

WORD_SEQUENCES = (
    ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"),
    ("january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"),
    ("first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth"),
)


def _display(value):
    """Avoid showing integer values as 1.0 in responses."""
    return str(int(value)) if value == int(value) else str(value)


def extract_numbers(text):
    """Backward-compatible helper: extract literal numeric tokens safely."""
    values = []
    for token in re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?(?![A-Za-z])", text):
        try:
            values.append(float(token))
        except ValueError:
            pass
    return values


def _repeating_block(values):
    for size in range(1, len(values) // 2 + 1):
        if len(values) % size == 0 and values == values[:size] * (len(values) // size):
            return values[:size]
    return None


def _differences(values):
    return [values[index + 1] - values[index] for index in range(len(values) - 1)]


def _is_prime(number):
    if number < 2 or number != int(number):
        return False
    for divisor in range(2, math.isqrt(int(number)) + 1):
        if number % divisor == 0:
            return False
    return True


def _number_lines(values):
    lines = []
    if len(values) == 1:
        return ["Single numeric value: " + _display(values[0])]

    # Two values establish a change, but not a reliable sequence rule.
    if len(values) == 2:
        return [
            "Values: " + ", ".join(_display(value) for value in values),
            "I couldn't identify a reliable pattern in that sequence.",
        ]

    block = _repeating_block(values)
    if block:
        label = "Alternating repeating pattern" if len(block) == 2 else "Repeating pattern"
        return [f"Pattern detected: {label}", "Block: [" + ", ".join(_display(x) for x in block) + "]",
                "Next number: " + _display(block[0])]

    first = _differences(values)
    increasing = all(diff > 0 for diff in first)
    decreasing = all(diff < 0 for diff in first)
    arithmetic = len(set(first)) == 1
    ratios = []
    if all(value != 0 for value in values[:-1]):
        ratios = [values[index + 1] / values[index] for index in range(len(values) - 1)]
    geometric = ratios and all(abs(ratio - ratios[0]) < 1e-9 for ratio in ratios)

    integers = all(value >= 0 and value == int(value) for value in values)
    roots = [math.isqrt(int(value)) for value in values] if integers else []
    squares = integers and all(root * root == value for root, value in zip(roots, values)) and _differences(roots) == [1] * (len(roots) - 1)
    cube_roots = [round(value ** (1 / 3)) for value in values] if integers else []
    cubes = integers and all(root ** 3 == value for root, value in zip(cube_roots, values)) and _differences(cube_roots) == [1] * (len(cube_roots) - 1)
    fibonacci = len(values) >= 3 and all(abs(values[i] - values[i - 1] - values[i - 2]) < 1e-9 for i in range(2, len(values)))
    primes = len(values) >= 3 and all(_is_prime(value) for value in values)
    signed_alternating = len(values) >= 4 and all(values[i] * values[i + 1] < 0 for i in range(len(values) - 1))
    next_value = None

    if squares:
        lines.append("Pattern detected: Square-number pattern (n²)")
        next_value = (roots[-1] + 1) ** 2
    elif cubes:
        lines.append("Pattern detected: Cube-number pattern (n³)")
        next_value = (cube_roots[-1] + 1) ** 3
    elif fibonacci:
        lines.append("Pattern detected: Fibonacci-like sequence")
        lines.append("Rule: Each value is the sum of the previous two.")
        next_value = values[-1] + values[-2]
    elif primes:
        lines.append("Pattern detected: Prime-number sequence")
    elif arithmetic:
        lines.append("Pattern detected: Arithmetic progression")
        lines.append("Difference: " + f"{first[0]:+g}")
        next_value = values[-1] + first[0]
    elif geometric:
        lines.append("Pattern detected: Geometric progression")
        lines.append("Ratio: " + _display(ratios[0]))
        next_value = values[-1] * ratios[0]
    elif signed_alternating:
        lines.append("Pattern detected: Positive/negative alternating pattern")
    elif increasing:
        lines.append("Pattern detected: Increasing sequence")
    elif decreasing:
        lines.append("Pattern detected: Decreasing sequence")

    if not arithmetic and len(first) >= 2:
        second = _differences(first)
        if len(set(second)) == 1:
            lines.append("Second differences: " + " ".join(f"{value:+g}" for value in second))
            next_value = values[-1] + first[-1] + second[0]
        elif all(second[i] > second[i - 1] for i in range(1, len(second))):
            lines.append("First differences: " + " ".join(f"{value:+g}" for value in first))
            lines.append("Observation: Differences are increasing.")
    if not lines:
        lines.append("No strong numeric pattern detected.")

    if primes:
        candidate = int(values[-1]) + 1
        while not _is_prime(candidate):
            candidate += 1
        next_value = candidate
    if next_value is not None:
        lines.append("Next number: " + _display(next_value))

    if len(values) >= 3:
        counts = Counter(values)
        most_common, frequency = counts.most_common(1)[0]
        lines.append("Stats: count={}, min={}, max={}, average={}, median={}, unique={}".format(
            len(values), _display(min(values)), _display(max(values)), _display(sum(values) / len(values)),
            _display(median(values)), len(counts)))
        if frequency > 1:
            lines.append(f"Most frequent: {_display(most_common)} ({frequency} times)")
    return lines


def analyze_numbers(numbers):
    """Retained for callers that previously supplied a numeric list."""
    return "\n".join(_number_lines(numbers)) if numbers else "No numeric values found."


def _word_lines(words):
    if not words:
        return []
    lines = []
    block = _repeating_block(words)
    if block:
        label = "Alternating repeating pattern" if len(block) == 2 else "Repeating pattern"
        lines.extend([f"Pattern detected: {label}", "Block: [" + ", ".join(block) + "]"])
        lines.append("Next: " + block[0])
    counts = Counter(words)
    repeated = [(word, count) for word, count in counts.items() if count > 1]
    for word, count in repeated[:3]:
        lines.append(f'"{word}" occurs {count} times.')
    lengths = [len(word) for word in words]
    if len(lengths) >= 3 and len(set(_differences(lengths))) == 1 and _differences(lengths)[0] != 0:
        lines.append("Word lengths: " + ", ".join(map(str, lengths)))
        lines.append("Word-length difference: " + f"{_differences(lengths)[0]:+g}")
    if len(words) >= 3 and words == list(reversed(words)):
        lines.append("Symmetrical / palindrome-like sequence")
    return lines


def _sequence_word_lines(words):
    """Recognize only consecutive known day, month, and ordinal sequences."""
    if len(words) < 2:
        return []
    for sequence in WORD_SEQUENCES:
        try:
            start = sequence.index(words[0])
        except ValueError:
            continue
        if all(sequence[(start + index) % len(sequence)] == word for index, word in enumerate(words)):
            name = "Day" if sequence[0] == "monday" else "Month" if sequence[0] == "january" else "Ordinal"
            return [f"Pattern detected: {name} sequence", f"Next: {sequence[(start + len(words)) % len(sequence)]}"]
    return []


def _letter_lines(tokens):
    letters = [token for token in tokens if len(token) == 1 and token.isalpha()]
    if len(letters) < 2:
        return []
    positions = [ord(letter.upper()) - ord("A") + 1 for letter in letters]
    diffs = _differences(positions)
    lines = []
    block = _repeating_block(letters)
    if block:
        label = "Alternating character pattern" if len(block) == 2 else "Repeating character pattern"
        lines.extend([f"Pattern detected: {label}", "Block: [" + ", ".join(block) + "]"])
    if len(set(diffs)) == 1:
        direction = "increasing" if diffs[0] > 0 else "decreasing"
        lines.extend([f"Pattern detected: Alphabetic progression ({direction})", f"Letter position difference: {diffs[0]:+g}"])
    return lines


def analyze_pattern(command):
    """Analyze the payload of an analyze/pattern command without throwing on mixed input."""
    payload = re.sub(r"^\s*(?:analyze|analyse|pattern)\b(?:\s+(?:of|in))?\s*", "", command, flags=re.I)
    if not payload:
        return "Please provide values to analyze."
    compact = payload.strip()
    if not re.search(r"\s", compact) and re.fullmatch(r"[A-Za-z0-9]+", compact) and len(compact) > 1:
        block = _repeating_block(list(compact.lower()))
        if block:
            label = "Alternating character pattern" if len(block) == 2 else "Repeating character pattern"
            return f"Pattern detected: {label}\nBlock: [" + ", ".join(block) + "]"
        if compact.isalpha():
            letter_lines = _letter_lines(list(compact))
            if letter_lines:
                return "\n".join(letter_lines)
    tokens = re.findall(r"[A-Za-z]+[-+]?\d*|[-+]?\d+(?:\.\d+)?", payload)
    if not tokens:
        return "No analyzable values found."

    # Preserve a simple spoken number sequence as words when possible.
    if len(tokens) >= 2 and all(token.lower() in NUMBER_WORDS for token in tokens):
        values = [NUMBER_WORDS[token.lower()] for token in tokens]
        differences = _differences(values)
        if len(set(differences)) == 1 and values[-1] + differences[0] in NUMBER_NAMES:
            return "\n".join([
                "Pattern detected: Number-word sequence",
                f"Rule: Each value changes by {differences[0]:+g}.",
                "Next: " + NUMBER_NAMES[values[-1] + differences[0]],
            ])

    numbers, words, combined_letters, combined_numbers = [], [], [], []
    for token in tokens:
        lower = token.lower()
        if lower in NUMBER_WORDS:
            numbers.append(float(NUMBER_WORDS[lower]))
        elif re.fullmatch(r"[-+]?\d+(?:\.\d+)?", token):
            numbers.append(float(token))
        elif re.fullmatch(r"[A-Za-z]+", token):
            words.append(lower)
        else:
            match = re.fullmatch(r"([A-Za-z]+)([-+]?\d+)", token)
            if match:
                combined_letters.append(match.group(1)[0])
                combined_numbers.append(float(match.group(2)))

    sections = []
    if numbers:
        lines = _number_lines(numbers)
        sections.append(("Numbers" if words or combined_letters else None, lines))
    if words:
        word_lines = _sequence_word_lines(words) or _word_lines(words)
        letter_lines = _letter_lines(words)
        lines = word_lines + [line for line in letter_lines if line not in word_lines]
        if lines:
            sections.append(("Words / letters" if numbers or combined_letters else None, lines))
    if combined_letters:
        lines = _letter_lines(combined_letters) + _number_lines(combined_numbers)
        if len(combined_letters) >= 2:
            lines.append("Combined structure appears sequential.")
        sections.append(("Combined tokens", lines))
    if not sections:
        return "No strong pattern detected."
    output = []
    for heading, lines in sections:
        if heading:
            output.append(heading + ":")
        output.extend(lines)
    return "\n".join(output)
