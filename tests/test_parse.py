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


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2025/12/04", date(2025, 12, 4)),
        ("2025/1/4", date(2025, 1, 4)),
        ("2024/02/29", date(2024, 2, 29)),
        ("  2025/12/04  ", date(2025, 12, 4)),
        ("5 days before 2025/12/04", date(2025, 11, 29)),
        ("one month after 2025/01/31", date(2025, 2, 28)),
    ],
)
def test_year_first_slash_dates(text: str, expected: date) -> None:
    assert parse(text, today=date(2030, 6, 15)) == expected


@pytest.mark.parametrize(
    "text", ["2025/02/29", "2025/13/04", "2025/12/32", "0000/01/01"]
)
def test_invalid_year_first_slash_dates(text: str) -> None:
    with pytest.raises(ValueError):
        parse(text)


@pytest.mark.parametrize(
    ("month_number", "month_name"),
    list(
        enumerate(
            [
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ],
            start=1,
        )
    ),
)
@pytest.mark.parametrize(
    "template",
    [
        "{name}. 1, 2025",
        "1 {name}. 2025",
        "{name}. 1st",
        "two days after {name}. 1, 2025",
    ],
)
def test_dotted_month_names(month_number: int, month_name: str, template: str) -> None:
    text = template.format(name=month_name)
    day = 3 if text.startswith("two days") else 1
    assert parse(text, today=date(2025, 6, 15)) == date(2025, month_number, day)


def test_dotted_september_alias() -> None:
    assert parse("Sept. 1, 2025") == date(2025, 9, 1)


@pytest.mark.parametrize(
    "text", ["Dec.. 1, 2025", "Dec. 32, 2025", "Feb. 29, 2025", "Foo. 1, 2025"]
)
def test_invalid_dotted_month_dates(text: str) -> None:
    with pytest.raises(ValueError):
        parse(text)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("the day after tomorrow", date(2025, 2, 2)),
        ("day after tomorrow", date(2025, 2, 2)),
        ("the day before yesterday", date(2025, 1, 29)),
        ("day before yesterday", date(2025, 1, 29)),
        ("the week after next Tuesday", date(2025, 2, 11)),
        ("the month after today", date(2025, 2, 28)),
        ("the year before today", date(2024, 1, 31)),
        ("two weeks from the day after tomorrow", date(2025, 2, 16)),
        ("the day after the day before yesterday", date(2025, 1, 30)),
        (" THE   DAY AFTER TOMORROW ", date(2025, 2, 2)),
    ],
)
def test_singular_unit_anchors(text: str, expected: date) -> None:
    assert parse(text, today=date(2025, 1, 31)) == expected


@pytest.mark.parametrize(
    ("text", "reference", "expected"),
    [
        ("the day after tomorrow", date(2024, 2, 28), date(2024, 3, 1)),
        ("the day before yesterday", date(2025, 1, 1), date(2024, 12, 30)),
    ],
)
def test_singular_unit_date_boundaries(
    text: str, reference: date, expected: date
) -> None:
    assert parse(text, today=reference) == expected


@pytest.mark.parametrize(
    "text", ["the days after tomorrow", "the after tomorrow", "the day after nonsense"]
)
def test_invalid_singular_unit_anchors(text: str) -> None:
    with pytest.raises(ValueError):
        parse(text)
