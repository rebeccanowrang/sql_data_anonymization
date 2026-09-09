# SQL Data Anonymization

## Student Information

**Student:** Rebecca Nowrang  
**Course:** ICS 499 – Software Engineering and Capstone Project  
**Institution:** Metro State University  
**Assignment:** SQL Data Anonymization

## Project Overview

This project anonymizes Personally Identifiable Information (PII) contained in a MySQL SQL export while preserving the usefulness of the data for development and testing.

The program focuses on the four PII categories required by the assignment:

1. Names
2. Addresses
3. Email addresses
4. Phone numbers

The input is a MySQL `.sql` file containing statements such as `CREATE TABLE` and `INSERT INTO`. The output is a new SQL file in which identified PII values are replaced by realistic synthetic values.

The solution intentionally does **not** create a reverse mapping file.

## Technology Selection

### Programming Language: Python 3

I selected Python because it provides strong string-processing support, regular expressions, hashing/HMAC libraries in the standard library, simple automated testing with `unittest`, and access to the Faker synthetic-data library.

### External Library: Faker

[Faker](https://faker.readthedocs.io/) generates realistic names, addresses, user names, cities, states, and postal codes. This is more useful for testing than replacing information with generic values such as `XXXX`.

The project pins the Faker version in `requirements.txt` because Faker's own documentation notes that seeded output can change when provider datasets change between versions.

### Standard-Library Components

- `re` – identifies SQL constructs and field names.
- `hmac` and `hashlib` – derive deterministic seeds without writing a mapping file.
- `argparse` – command-line interface.
- `unittest` – automated tests.
- `pathlib` – file handling.

## Research and Design Decisions

### Data Masking

Masking obscures data, often by replacing part or all of a value. For example, a phone number could become `XXX-XXX-1234`. That is not the approach used here because the assignment requires realistic synthetic replacement values.

### Anonymization / De-identification

NIST describes de-identification as removing or reducing the association between identifying data and a data subject. This project follows that goal at an assignment scale by replacing the four required direct identifiers with synthetic values.

### Pseudonymization

Pseudonymization replaces identifying values with substitutes while preserving useful relationships. The deterministic replacement behavior in this project has pseudonymization-like properties because repeated source values receive repeated replacements. However, the program does not create a recovery table and is designed for the assignment's one-way workflow.

### Synthetic Data

Synthetic values resemble realistic data without copying the original PII. This is the main technique used in the project. Faker creates plausible replacement names and addresses, while email and phone values are generated in valid-looking formats.

### Hashing

The original PII is **not** replaced directly with a hash because a hash such as `8b1a9953...` would not resemble realistic test data. Instead, HMAC-SHA256 is used internally to derive deterministic seeds that drive synthetic generation.

### Tokenization

Tokenization normally replaces sensitive values with tokens, often relying on a protected mapping or token vault. A mapping file is unnecessary for this assignment, so tokenization was not selected.

## Anonymization Strategy

### 1. Read the Entire SQL File

The program processes the SQL file as a whole. This is important because the same value may appear in multiple tables.

### 2. Read CREATE TABLE Metadata

`CREATE TABLE` statements are inspected to learn column order. This allows the program to understand an `INSERT INTO table VALUES (...)` statement even when the INSERT statement does not repeat the column names.

### 3. Identify Sensitive Columns

The program uses column names to identify the four required categories.

Examples:

- `name`, `customer_name`, `contact_name` → name
- `address`, `shipping_address`, `billing_address` → address
- `email`, `email_address` → email
- `phone`, `phone_number`, `mobile` → phone

A generic column called `name` is treated as PII only when the table name looks person-related (for example, `customers`, `contacts`, `employees`, or `leads`). This reduces the risk of changing a non-sensitive field such as `products.name`.

### 4. Generate Realistic Synthetic Values

For each original PII value, the program derives a deterministic seed using:

`HMAC-SHA256(key, category + original value)`

The seed initializes a local Faker generator. The result is realistic but does not require a reverse mapping file.

### 5. Maintain Consistency

If the same name, address, email, or phone appears repeatedly, the same input category/value pair receives the same synthetic replacement.

This also works across tables because the entire SQL file is processed through one anonymization engine.

### 6. Preserve SQL Strings Safely

Replacement strings are SQL-escaped before being written. Apostrophes are represented using doubled single quotes, so a value such as `O'Neil` remains valid inside a MySQL string literal.

### 7. Preserve Non-Sensitive Data

Identifiers, prices, order totals, statuses, loyalty levels, delivery methods, and product names are not intentionally changed.

## Installation

Python 3.9+ is recommended.

Create a virtual environment if desired:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependency:

```bash
pip install -r requirements.txt
```

## How to Run

Basic usage:

```bash
python3 anonymizer.py original.sql anonymized.sql
```

For deterministic output with your own secret key:

```bash
export ANONYMIZATION_KEY="replace-this-with-a-private-random-key"
python3 anonymizer.py original.sql anonymized.sql
```

You can also pass a key directly:

```bash
python3 anonymizer.py original.sql anonymized.sql --key "class-demo-key"
```

The program prints the number of unique values replaced in each category and does not create a reverse mapping file.

## Expected Input

A MySQL SQL export containing `CREATE TABLE` and normal `INSERT INTO ... VALUES ...` statements.

Both of these styles are supported:

```sql
INSERT INTO customers VALUES (...);
```

and:

```sql
INSERT INTO customers (customer_id, name, email) VALUES (...);
```

Multi-row `VALUES` statements are supported.

## Generated Output

The output is another `.sql` file with the same general SQL structure and non-sensitive values, but required PII fields are replaced with synthetic values.

Example concept:

```text
Original:
John Smith
123 Main Street, Minneapolis, MN 55401
john.smith@gmail.com
612-555-1234

Anonymized:
Synthetic Name
Synthetic Minnesota-style address
synthetic_user@example.com
synthetic formatted phone
```

The actual values are generated by the program.

## Consistency Across Tables

The included `original.sql` intentionally repeats the same customer data in:

- `customers`
- `orders`
- `shipping`

After anonymization, the same original values receive the same replacements in each table. This provides evidence that consistency is maintained across SQL statements and tables.

## Testing

Run:

```bash
python3 -m unittest -v test_anonymizer.py
```

The automated tests verify:

- original names are removed;
- original addresses are removed;
- original emails are removed;
- original phone numbers are removed;
- all four required categories are processed;
- repeated values stay consistent across tables;
- generated email/phone/address formats are reasonable;
- non-sensitive values remain present;
- `CREATE TABLE` structure remains;
- `INSERT INTO` statements remain;
- the same key produces the same result;
- a different key produces different synthetic output.

See [TESTING.md](TESTING.md) for the captured test evidence.

## Important Design Decisions

### Why Deterministic Synthetic Substitution?

A simple random replacement map would keep values consistent only during one execution. Deterministic HMAC-derived Faker seeds make it possible to reproduce the same anonymized data with the same key while still producing realistic data.

### Why Not Store a Mapping File?

The assignment explicitly does not require a mapping file and asks for a one-way workflow. The program therefore never writes original-to-replacement mappings to disk.

### Why Use `example.com` for Synthetic Email?

`example.com` is reserved for documentation/examples and prevents generated test email from accidentally targeting a real user's mailbox.

### Phone Formatting

The generator creates synthetic digits and, when possible, preserves the punctuation pattern of the original phone. For example, `612-555-1234` remains in a `###-###-####` style and `(651) 555-8822` remains in a parenthesized style.

## Known Limitations

This is a course project, not a production-grade SQL parser or a formal privacy guarantee.

- Field detection is based mainly on table/column names.
- Unusual schemas may require adding field-name rules.
- The parser is designed for ordinary MySQL `INSERT ... VALUES` exports; advanced constructs such as `INSERT ... SELECT`, stored procedures, delimiter changes, or unusual SQL modes are outside the project scope.
- The solution only targets the four PII categories required by the assignment.
- It does not evaluate re-identification risk or provide a formal privacy model such as differential privacy.
- Deterministic output depends on using the same key, Faker version, and locale.
- If the deterministic key is public, an attacker with likely candidate inputs could test guesses. A real organization should protect the key and conduct a broader privacy-risk review.

## Project Files

```text
sql_data_anonymization/
├── README.md
├── anonymizer.py
├── requirements.txt
├── original.sql
├── anonymized.sql
├── test_anonymizer.py
├── TESTING.md
└── RESEARCH.md
```

## References

- NIST Special Publication 800-188, *De-Identifying Government Datasets: Techniques and Governance*: https://csrc.nist.gov/pubs/sp/800/188/final
- NISTIR 8053, *De-Identification of Personal Information*: https://www.nist.gov/publications/de-identification-personal-information
- Faker documentation: https://faker.readthedocs.io/
- Python `hmac` documentation: https://docs.python.org/3/library/hmac.html
- Python `unittest` documentation: https://docs.python.org/3/library/unittest.html

## AI Usage

ChatGPT was used as a development and research assistant to help:

- interpret the assignment requirements;
- compare anonymization approaches;
- design the field-identification and consistency strategy;
- generate and review Python code;
- design test cases;
- improve documentation.

I reviewed the generated solution and used automated tests to validate its behavior. The final design uses realistic synthetic substitution rather than plain masking, maintains cross-table consistency, and preserves non-sensitive SQL values.
