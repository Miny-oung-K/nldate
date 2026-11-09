from datetime import date

import pytest

from nldate import parse


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("today", date(2025, 1, 31)),
        ("tomorrow", date(2025, 2, 1)),
        ("yesterday", date(2025, 1, 30)),
        ("next Tuesday", date(2025, 2, 4)),
        ("last Friday", date(2025, 1, 24)),
        ("next Friday", date(2025, 2, 7)),
        ("this Monday", date(2025, 1, 27)),
        ("Friday", date(2025, 1, 31)),
        ("2024-02-29", date(2024, 2, 29)),
        ("12/31/2025", date(2025, 12, 31)),
        ("December 1st, 2025", date(2025, 12, 1)),
        ("1 December 2025", date(2025, 12, 1)),
        ("the 1st of Dec 2025", date(2025, 12, 1)),
        ("Sept 3", date(2025, 9, 3)),
        ("5 days before December 1st, 2025", date(2025, 11, 26)),
        ("1 year and 2 months after yesterday", date(2026, 3, 30)),
        ("two weeks from tomorrow", date(2025, 2, 15)),
        ("in 3 days", date(2025, 2, 3)),
        ("two weeks ago", date(2025, 1, 17)),
        ("in twenty-one days", date(2025, 2, 21)),
        ("a month after today", date(2025, 2, 28)),
        ("next month", date(2025, 2, 28)),
        ("last year", date(2024, 1, 31)),
        ("this week", date(2025, 1, 31)),
        ("  NEXT   tUeSdAy  ", date(2025, 2, 4)),
        ("1 day after 2 days before tomorrow", date(2025, 1, 31)),
        ("in 1 year, 2 months, and 3 days", date(2026, 4, 3)),
        ("in 0 days", date(2025, 1, 31)),
    ],
)
def test_supported_expressions(text: str, expected: date) -> None:
    assert parse(text, today=date(2025, 1, 31)) == expected


@pytest.mark.parametrize(
    "text",
    [
        "",
        "   ",
        "banana",
        "2025-02-29",
        "April 31, 2025",
        "13/01/2025",
        "in -3 days",
        "in many days",
        "in 1 day rubbish",
        "rubbish 1 day ago",
        "in 1 day or 2 days",
        "next Funday",
        "today please",
        "2025-13-01",
        "in 1000000000000 years",
    ],
)
def test_invalid_expressions(text: str) -> None:
    with pytest.raises(ValueError):
        parse(text, today=date(2025, 1, 31))


def test_leap_year_clamping() -> None:
    assert parse("in one year", date(2024, 2, 29)) == date(2025, 2, 28)
    assert parse("in one month", date(2024, 1, 31)) == date(2024, 2, 29)


def test_calendar_units_before_days() -> None:
    assert parse("in 1 month and 1 day", date(2025, 1, 31)) == date(2025, 3, 1)


def test_underflow_is_value_error() -> None:
    with pytest.raises(ValueError):
        parse("yesterday", date.min)


def test_default_reference_date() -> None:
    before = date.today()
    result = parse("today")
    after = date.today()
    assert before <= result <= after
