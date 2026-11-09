"""Parse common English date expressions using deterministic pattern matching."""

import calendar
import re
from datetime import date, timedelta

__all__ = ["parse"]

_MONTHS = {
    name.lower(): i
    for i in range(1, 13)
    for name in (calendar.month_name[i], calendar.month_abbr[i])
}
_MONTHS["sept"] = 9
_WEEKDAYS = {
    name.lower(): i
    for i in range(7)
    for name in (calendar.day_name[i], calendar.day_abbr[i])
}
_SMALL = dict(
    zip(
        [
            "zero",
            "one",
            "two",
            "three",
            "four",
            "five",
            "six",
            "seven",
            "eight",
            "nine",
            "ten",
            "eleven",
            "twelve",
            "thirteen",
            "fourteen",
            "fifteen",
            "sixteen",
            "seventeen",
            "eighteen",
            "nineteen",
        ],
        range(20),
        strict=True,
    )
)
_TENS = dict(
    zip(
        ["twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"],
        range(20, 100, 10),
        strict=True,
    )
)


def _number(text: str) -> int:
    if text.isdecimal():
        return int(text)
    if text in {"a", "an"}:
        return 1
    words = text.replace("-", " ").split()
    if len(words) == 1 and words[0] in _SMALL | _TENS:
        return (_SMALL | _TENS)[words[0]]
    if (
        len(words) == 2
        and words[0] in _TENS
        and words[1] in _SMALL
        and 0 < _SMALL[words[1]] < 10
    ):
        return _TENS[words[0]] + _SMALL[words[1]]
    raise ValueError(f"Unsupported number: {text!r}")


def _shift(anchor: date, amounts: dict[str, int], sign: int) -> date:
    # Calendar units are applied together first; clamp to the destination month.
    index = anchor.year * 12 + anchor.month - 1
    index += sign * (12 * amounts.get("year", 0) + amounts.get("month", 0))
    year, month = divmod(index, 12)
    month += 1
    if not 1 <= year <= 9999:
        raise ValueError("Date is outside the supported range")
    result = date(year, month, min(anchor.day, calendar.monthrange(year, month)[1]))
    return result + timedelta(
        days=sign * (7 * amounts.get("week", 0) + amounts.get("day", 0))
    )


def _duration(text: str) -> dict[str, int]:
    pattern = r"([a-z\d]+(?:[ -][a-z]+)?)\s+(years?|months?|weeks?|days?)"
    amounts: dict[str, int] = {}
    position = 0
    for match in re.finditer(pattern, text):
        separator = text[position : match.start()]
        if (position == 0 and separator) or (
            position > 0 and separator.strip() not in {"", ",", "and", ", and"}
        ):
            raise ValueError("Invalid duration")
        unit = match[2].rstrip("s")
        amounts[unit] = amounts.get(unit, 0) + _number(match[1])
        position = match.end()
    if not amounts or text[position:].strip():
        raise ValueError("Invalid duration")
    return amounts


def _parse(text: str, today: date, depth: int = 0) -> date:
    if depth > 20:
        raise ValueError("Expression is too deeply nested")
    if text in {"today", "now", "tomorrow", "yesterday"}:
        return today + timedelta(
            days={"today": 0, "now": 0, "tomorrow": 1, "yesterday": -1}[text]
        )
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return date.fromisoformat(text)
    year_first = re.fullmatch(r"(\d{4})/(\d{1,2})/(\d{1,2})", text)
    if year_first:
        return date(int(year_first[1]), int(year_first[2]), int(year_first[3]))
    numeric = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if numeric:
        return date(int(numeric[3]), int(numeric[1]), int(numeric[2]))
    weekday = re.fullmatch(r"(?:(next|last|this) )?([a-z]+)", text)
    if weekday and weekday[2] in _WEEKDAYS:
        offset = _WEEKDAYS[weekday[2]] - today.weekday()
        if weekday[1] == "last":
            offset = -((-offset) % 7 or 7)
        elif weekday[1] != "this":
            offset = offset % 7 or (7 if weekday[1] == "next" else 0)
        return today + timedelta(days=offset)
    simple = re.fullmatch(r"(next|last|this) (day|week|month|year)", text)
    if simple:
        return _shift(
            today, {simple[2]: 1}, {"next": 1, "last": -1, "this": 0}[simple[1]]
        )
    relative = re.fullmatch(r"(.+?) (before|after|from) (.+)", text)
    if relative:
        duration = relative[1]
        singular_unit = re.fullmatch(r"(?:the )?(day|week|month|year)", duration)
        if singular_unit:
            duration = f"1 {singular_unit[1]}"
        return _shift(
            _parse(relative[3], today, depth + 1),
            _duration(duration),
            -1 if relative[2] == "before" else 1,
        )
    if text.startswith("in "):
        return _shift(today, _duration(text[3:]), 1)
    if text.endswith(" ago"):
        return _shift(today, _duration(text[:-4]), -1)
    # Month names may precede or follow the day; a missing year means this year.
    cleaned = re.sub(r"(?<=\d)(st|nd|rd|th)\b", "", text).replace(",", "")
    cleaned = re.sub(r"\bthe\s+", "", cleaned)
    cleaned = cleaned.replace(" of ", " ")
    for pattern, month_group, day_group in (
        (r"([a-z]+)\.? (\d{1,2})(?: (\d{4}))?", 1, 2),
        (r"(\d{1,2}) ([a-z]+)\.?(?: (\d{4}))?", 2, 1),
    ):
        match = re.fullmatch(pattern, cleaned)
        if match and match[month_group] in _MONTHS:
            return date(
                int(match[3]) if match[3] else today.year,
                _MONTHS[match[month_group]],
                int(match[day_group]),
            )
    raise ValueError(f"Unrecognized date expression: {text!r}")


def parse(s: str, today: date | None = None) -> date:
    """Return the date described by *s*, relative to *today* (default: today).

    Input is case-insensitive and whitespace is normalized. Slash dates accept
    year/month/day or US month/day/year order. See README.md for supported forms and semantics.
    Unrecognized expressions and impossible dates raise ValueError.
    """
    if not isinstance(s, str):
        raise TypeError("Date expression must be a string")
    text = " ".join(s.lower().strip().split())
    try:
        return _parse(text, date.today() if today is None else today)
    except (OverflowError, RecursionError) as exc:
        raise ValueError("Date is outside the supported range") from exc
