# Filter-input-data

A command-line tool that cleans expense data from CSV/XML files and loads it into a SQLite database.

## Why this project

Real-world expense data is messy: amounts are written in different styles, dates come in many formats, and some rows are incomplete. Entering or fixing this by hand, row by row, is slow and error-prone.

This tool reads the raw file, normalizes every row, rejects invalid ones with a clear reason, and inserts the clean rows into SQLite in one step.

## Features

- Reads `.csv` and `.xml` input files
- Normalizes amounts: `200,000`, `200.000`, `200 000 VND` all become `200000`
- Normalizes dates: `2026-11-19`, `2026/11/19`, `19/11/2026`, `19-11-2026`, `19.11.2026` all become `2026-11-19`
- Cleans stray whitespace, non-breaking spaces and BOM characters
- Rejects invalid rows and reports why (missing field, invalid date, non-positive amount)
- Uses only the Python standard library, so there is nothing extra to install

## Requirements

- Python 3.9 or newer

## Installation

```bash
git clone https://github.com/VulcanChangeup303/Filter-input-data.git
cd Filter-input-data
```

Optional: install it as a command (`filter-expenses`):

```bash
pip install .
```

> **Windows note:** if `filter-expenses` is not recognized after installing, the Python `Scripts` folder is not on your PATH. Either add it to PATH, or run the tool with `python app.py ...` as shown below.

## Usage

```bash
python app.py data/expenses_sample.csv
python app.py data/expenses_sample.csv --db my_expenses.db
```

| Argument | Description |
|---|---|
| `input` | Path to the `.csv` or `.xml` file to process (required) |
| `--db` | Output SQLite file (default: `expenses.db` in the current directory) |

Show all options:

```bash
python app.py --help
```

### Example output

```text
Read: data/expenses_sample.csv
Wrote <N> clean rows to: <path>/expenses.db
Rejected <M> invalid rows.
  missing_or_invalid_date: <x>
  amount_not_positive: <y>
```

> Replace the placeholders above with the real output of your own run.

## Input format

Required columns: `date`, `amount`, `category`, `description`
Optional columns: `payment_method`, `note`

CSV example:

```csv
date,amount,category,description,payment_method,note
2026-11-19,"200,000",Food,Lunch,cash,
19/11/2026,150.000 VND,Transport,Taxi,card,Airport
```

XML example:

```xml
<expenses>
  <expense>
    <date>2026-11-19</date>
    <amount>200000</amount>
    <category>Food</category>
    <description>Lunch</description>
  </expense>
</expenses>
```

Column names are case-insensitive. Amounts must be positive whole numbers (decimals and negative values are rejected).

## Database schema

Clean rows are stored in the `expenses` table:

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER | Primary key, auto-increment |
| `date` | TEXT | ISO format `YYYY-MM-DD` |
| `amount` | INTEGER | Positive whole number |
| `category` | TEXT | |
| `description` | TEXT | |
| `payment_method` | TEXT | Optional |
| `note` | TEXT | Optional |

Query the result with any SQLite tool, for example:

```bash
sqlite3 expenses.db "SELECT category, SUM(amount) FROM expenses GROUP BY category;"
```

> Running the tool twice on the same file inserts the rows twice.

## Running tests

```bash
pip install pytest
pytest
```

## Project structure

```text
Filter-input-data/
├── app.py            # main program: read, clean, load
├── data/             # sample input files
├── tests/            # pytest tests
├── pyproject.toml    # packaging configuration
├── README.md
└── LICENSE
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.