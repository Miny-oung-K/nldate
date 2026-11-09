# nldate

A small Python library that turns common English date expressions into
`datetime.date` values using pattern matching. No runtime dependencies or LLMs.
Requires Python 3.12 or newer.

```python
from datetime import date
from nldate import parse

parse("5 days before December 1st, 2025")  # date(2025, 11, 26)
parse("next Tuesday", today=date(2025, 1, 31))  # date(2025, 2, 4)
parse("two weeks from tomorrow", today=date(2025, 1, 31))  # date(2025, 2, 15)
```

## Supported expressions

- `today`, `now`, `tomorrow`, `yesterday`
- ISO dates: `2025-12-01`
- Year-first slash dates: `2025/12/04`, `2025/1/4`
- US numeric dates: `12/01/2025` (month/day/year)
- Named months: `December 1st, 2025`, `1 Dec 2025`, `the 1st of December`
- Weekdays: `Tuesday`, `next Tuesday`, `last Tue`, `this Tuesday`
- Relative units: `next week`, `last month`, `this year`
- Durations: `in 3 days`, `two weeks ago`, `in 1 year and 2 months`
- Anchored durations: `5 days before December 1st, 2025`,
  `1 year and 2 months after yesterday`, `two weeks from tomorrow`
- Nested anchors: `1 day after 2 days before tomorrow`

Input is case-insensitive and surrounding/repeated whitespace is ignored.
Month and weekday names accept full names or standard three-letter abbreviations
(`Sept` is also accepted). Month abbreviations may include a period, as in
`Dec. 1, 2025` or `1 Dec. 2025`. Durations support nonnegative digits, `a`/`an`, and
English numbers zero through ninety-nine, including `twenty-one`. Units may be
singular or plural; duration components can be separated by spaces, commas,
or `and`.

## Date rules

`today` is the supplied reference date, or `date.today()` when omitted. Missing
years use the reference year. A bare weekday means its next occurrence, including
today. `next` and `last` weekdays are strictly future/past; `this` refers to the
weekday in the current Monday–Sunday week.

Weeks are seven days. Years and months are shifted together first, with the day
clamped to the final month's length, then weeks and days are added. For example,
one month after January 31, 2025 is February 28; one year after February 29, 2024
is February 28, 2025. Zero durations are valid.

Unrecognized strings, impossible dates, and out-of-range results raise
`ValueError`. Non-string input raises `TypeError`. This is a deliberately bounded
English grammar: holidays, times of day, time zones, and arbitrary prose are not
supported.

## Development and verification

The project was created with `uv init --package`; source is in `src/nldate/`.

```sh
uv sync --locked
uv run pytest
uv run mypy src/
uv run ruff check
uv run ruff format --check
```

The test suite checks fixed reference dates, assignment examples, leap years,
month boundaries, nested expressions, invalid inputs, and the default reference.

## Publish on GitHub

From this directory, authenticate and create a public repository:

```sh
gh auth login --hostname github.com
gh repo create nldate --public --source=. --remote=origin --push
```

Submit the resulting public repository URL to Gradescope.
