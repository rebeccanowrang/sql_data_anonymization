#!/usr/bin/env python3
"""
ICS 499 SQL Data Anonymizer

Anonymizes four PII categories in MySQL INSERT statements:
- names
- addresses
- email addresses
- phone numbers

Design goals:
- realistic synthetic replacements
- consistent replacement of repeated values
- consistency across tables/statements
- preserve non-sensitive values and SQL structure
- one-way workflow: no reverse mapping file is produced
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from faker import Faker


NON_COLUMN_PREFIXES = (
    "PRIMARY ", "KEY ", "UNIQUE ", "CONSTRAINT ", "FOREIGN ",
    "CHECK ", "INDEX ", "FULLTEXT ", "SPATIAL "
)

PERSON_TABLE_HINTS = (
    "customer", "contact", "person", "people", "user", "employee",
    "lead", "patient", "student", "donor", "member", "client", "staff"
)


def normalize_identifier(identifier: str) -> str:
    return identifier.strip().strip("`").lower()


def split_top_level(text: str, delimiter: str = ",") -> List[str]:
    """Split text on a delimiter while ignoring quoted strings and nested parentheses."""
    parts: List[str] = []
    start = 0
    depth = 0
    i = 0
    in_string = False

    while i < len(text):
        ch = text[i]

        if in_string:
            if ch == "'":
                if i + 1 < len(text) and text[i + 1] == "'":
                    i += 2
                    continue
                in_string = False
            elif ch == "\\" and i + 1 < len(text):
                i += 2
                continue
        else:
            if ch == "'":
                in_string = True
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            elif ch == delimiter and depth == 0:
                parts.append(text[start:i])
                start = i + 1
        i += 1

    parts.append(text[start:])
    return parts


def split_sql_statements(sql: str) -> List[str]:
    """Split SQL at semicolons outside single-quoted strings."""
    statements: List[str] = []
    start = 0
    i = 0
    in_string = False

    while i < len(sql):
        ch = sql[i]
        if in_string:
            if ch == "'":
                if i + 1 < len(sql) and sql[i + 1] == "'":
                    i += 2
                    continue
                in_string = False
            elif ch == "\\" and i + 1 < len(sql):
                i += 2
                continue
        else:
            if ch == "'":
                in_string = True
            elif ch == ";":
                statements.append(sql[start:i + 1])
                start = i + 1
        i += 1

    if start < len(sql):
        statements.append(sql[start:])
    return statements


def sql_unquote(token: str) -> Optional[str]:
    stripped = token.strip()
    if len(stripped) >= 2 and stripped[0] == "'" and stripped[-1] == "'":
        value = stripped[1:-1]
        value = value.replace("''", "'")
        value = value.replace("\\'", "'")
        return value
    return None


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def parse_create_table_columns(sql: str) -> Dict[str, List[str]]:
    """Build table -> column-order metadata from CREATE TABLE statements."""
    schemas: Dict[str, List[str]] = {}
    pattern = re.compile(
        r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?"
        r"(?P<table>`?[A-Za-z_][\w$]*`?)\s*\((?P<body>.*?)\)\s*;",
        re.IGNORECASE | re.DOTALL,
    )

    for match in pattern.finditer(sql):
        table = normalize_identifier(match.group("table"))
        columns: List[str] = []
        for item in split_top_level(match.group("body")):
            definition = item.strip()
            upper = definition.upper()
            if not definition or upper.startswith(NON_COLUMN_PREFIXES):
                continue
            column_match = re.match(r"`?([A-Za-z_][\w$]*)`?\s+", definition)
            if column_match:
                columns.append(normalize_identifier(column_match.group(1)))
        if columns:
            schemas[table] = columns
    return schemas


def classify_column(table: str, column: str) -> Optional[str]:
    """Return one of name/address/email/phone, or None."""
    table = normalize_identifier(table)
    column = normalize_identifier(column)
    flat = re.sub(r"[^a-z0-9]+", "_", column).strip("_")

    # Order matters: email_address should be email, not address.
    if flat in {"email", "email_address", "e_mail", "emailaddress"} or "email" in flat:
        return "email"

    if any(word in flat for word in ("phone", "telephone", "mobile", "cellphone", "cell_phone")):
        return "phone"

    if (
        flat in {"address", "street", "street_address", "mailing_address",
                 "shipping_address", "billing_address", "home_address"}
        or flat.endswith("_address")
    ):
        return "address"

    explicit_names = {
        "full_name", "fullname", "first_name", "firstname", "last_name",
        "lastname", "customer_name", "contact_name", "person_name",
        "employee_name", "lead_name", "client_name", "name"
    }
    if flat in explicit_names:
        # A generic "name" is only treated as PII in person-like tables.
        if flat != "name" or any(hint in table for hint in PERSON_TABLE_HINTS):
            return "name"

    return None


@dataclass
class AnonymizationEngine:
    key: str
    locale: str = "en_US"
    mappings: Dict[str, Dict[str, str]] = field(default_factory=lambda: {
        "name": {}, "address": {}, "email": {}, "phone": {}
    })
    reverse: Dict[str, Dict[str, str]] = field(default_factory=lambda: {
        "name": {}, "address": {}, "email": {}, "phone": {}
    })

    def _seed(self, category: str, original: str, attempt: int = 0) -> int:
        msg = f"{category}\0{original}\0{attempt}".encode("utf-8")
        digest = hmac.new(self.key.encode("utf-8"), msg, hashlib.sha256).digest()
        return int.from_bytes(digest[:8], "big")

    def _faker(self, category: str, original: str, attempt: int = 0) -> Faker:
        fake = Faker(self.locale)
        fake.seed_instance(self._seed(category, original, attempt))
        return fake

    def _make_name(self, original: str, fake: Faker) -> str:
        # Preserve a one-token vs. multi-token shape where practical.
        if len(original.strip().split()) <= 1:
            return fake.first_name()
        return fake.name()

    def _make_address(self, original: str, fake: Faker) -> str:
        return f"{fake.street_address()}, {fake.city()}, {fake.state_abbr()} {fake.postcode()}"

    def _make_email(self, original: str, fake: Faker) -> str:
        local = re.sub(r"[^a-z0-9._-]", "", fake.user_name().lower())
        if not local:
            local = "user"
        return f"{local}@example.com"

    def _make_phone(self, original: str, fake: Faker) -> str:
        digits_count = sum(ch.isdigit() for ch in original)
        if digits_count == 0:
            digits_count = 10

        rng = fake.random
        if digits_count == 10:
            generated = (
                str(rng.randint(2, 9))
                + "".join(str(rng.randint(0, 9)) for _ in range(2))
                + str(rng.randint(2, 9))
                + "".join(str(rng.randint(0, 9)) for _ in range(6))
            )
        else:
            generated = "".join(str(rng.randint(0, 9)) for _ in range(digits_count))

        # Preserve the original punctuation/spacing if it contained the same number of digits.
        if sum(ch.isdigit() for ch in original) == len(generated):
            iterator = iter(generated)
            return "".join(next(iterator) if ch.isdigit() else ch for ch in original)

        # Default US-style presentation.
        if len(generated) == 10:
            return f"{generated[:3]}-{generated[3:6]}-{generated[6:]}"
        return generated

    def anonymize(self, category: str, original: str) -> str:
        if original == "":
            return original

        if original in self.mappings[category]:
            return self.mappings[category][original]

        for attempt in range(100):
            fake = self._faker(category, original, attempt)
            if category == "name":
                replacement = self._make_name(original, fake)
            elif category == "address":
                replacement = self._make_address(original, fake)
            elif category == "email":
                replacement = self._make_email(original, fake)
            elif category == "phone":
                replacement = self._make_phone(original, fake)
            else:
                raise ValueError(f"Unknown category: {category}")

            # Avoid unchanged values and accidental collisions within a category.
            if replacement == original:
                continue
            owner = self.reverse[category].get(replacement)
            if owner is None or owner == original:
                self.mappings[category][original] = replacement
                self.reverse[category][replacement] = original
                return replacement

        raise RuntimeError(f"Could not create unique replacement for {category}: {original!r}")


INSERT_RE = re.compile(
    r"^(?P<prefix>\s*INSERT\s+INTO\s+)"
    r"(?P<table>`?[A-Za-z_][\w$]*`?)"
    r"(?P<columns>\s*\((?P<column_body>.*?)\))?"
    r"(?P<between>\s+VALUES\s*)"
    r"(?P<values>.*)"
    r"(?P<semicolon>;\s*)$",
    re.IGNORECASE | re.DOTALL,
)


def parse_value_rows(values_text: str) -> Optional[List[List[str]]]:
    """Parse VALUES (...) , (...) into token lists. Returns None on unsupported syntax."""
    rows: List[List[str]] = []
    i = 0
    n = len(values_text)

    while i < n:
        while i < n and (values_text[i].isspace() or values_text[i] == ","):
            i += 1
        if i >= n:
            break
        if values_text[i] != "(":
            return None

        start = i + 1
        depth = 1
        i += 1
        in_string = False

        while i < n and depth > 0:
            ch = values_text[i]
            if in_string:
                if ch == "'":
                    if i + 1 < n and values_text[i + 1] == "'":
                        i += 2
                        continue
                    in_string = False
                elif ch == "\\" and i + 1 < n:
                    i += 2
                    continue
            else:
                if ch == "'":
                    in_string = True
                elif ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        row_body = values_text[start:i]
                        rows.append(split_top_level(row_body))
                        i += 1
                        break
            i += 1
        else:
            return None

    return rows


def anonymize_insert_statement(
    statement: str,
    schemas: Dict[str, List[str]],
    engine: AnonymizationEngine,
) -> str:
    match = INSERT_RE.match(statement)
    if not match:
        return statement

    table = normalize_identifier(match.group("table"))

    if match.group("column_body") is not None:
        columns = [
            normalize_identifier(x)
            for x in split_top_level(match.group("column_body"))
        ]
    else:
        columns = schemas.get(table, [])

    if not columns:
        return statement

    rows = parse_value_rows(match.group("values"))
    if rows is None:
        return statement

    output_rows: List[str] = []

    for row in rows:
        new_values: List[str] = []
        for index, raw_token in enumerate(row):
            token = raw_token.strip()
            if index >= len(columns):
                new_values.append(token)
                continue

            category = classify_column(table, columns[index])
            original = sql_unquote(token)

            if category is None or original is None:
                new_values.append(token)
                continue

            replacement = engine.anonymize(category, original)
            new_values.append(sql_quote(replacement))

        output_rows.append("(" + ", ".join(new_values) + ")")

    columns_text = match.group("columns") or ""
    return (
        match.group("prefix")
        + match.group("table")
        + columns_text
        + match.group("between")
        + ",\n".join(output_rows)
        + match.group("semicolon")
    )


def anonymize_sql(sql: str, key: str, locale: str = "en_US") -> Tuple[str, AnonymizationEngine]:
    schemas = parse_create_table_columns(sql)
    engine = AnonymizationEngine(key=key, locale=locale)

    output: List[str] = []
    for statement in split_sql_statements(sql):
        if re.match(r"^\s*INSERT\s+INTO\b", statement, re.IGNORECASE):
            output.append(anonymize_insert_statement(statement, schemas, engine))
        else:
            output.append(statement)

    return "".join(output), engine


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replace names, addresses, emails, and phone numbers in MySQL INSERT statements."
    )
    parser.add_argument("input", type=Path, help="Original MySQL .sql file")
    parser.add_argument("output", type=Path, help="Destination anonymized .sql file")
    parser.add_argument(
        "--key",
        default=os.environ.get("ANONYMIZATION_KEY", "ics499-demo-key"),
        help="Secret/deterministic key. Prefer the ANONYMIZATION_KEY environment variable.",
    )
    parser.add_argument("--locale", default="en_US", help="Faker locale (default: en_US)")
    args = parser.parse_args()

    sql = args.input.read_text(encoding="utf-8")
    anonymized, engine = anonymize_sql(sql, key=args.key, locale=args.locale)
    args.output.write_text(anonymized, encoding="utf-8")

    counts = {category: len(mapping) for category, mapping in engine.mappings.items()}
    print(f"Anonymized SQL written to: {args.output}")
    print("Unique values replaced:", counts)
    print("No reverse mapping file was created.")


if __name__ == "__main__":
    main()
