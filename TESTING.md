# Testing Evidence

## Test Environment

The program was tested with Python using the included `original.sql` sample and the automated `unittest` test suite.

## Generation Command

```bash
python3 anonymizer.py original.sql anonymized.sql --key "ics499-assignment-key"
```

Observed program output:

```text
Anonymized SQL written to: anonymized.sql
Unique values replaced: {'name': 3, 'address': 3, 'email': 3, 'phone': 3}
No reverse mapping file was created.
```

## Automated Test Command

```bash
python3 -m unittest -v test_anonymizer.py
```

Observed result:

```text
test_all_four_categories_anonymized ... ok
test_create_table_structure_preserved ... ok
test_deterministic_with_same_key ... ok
test_different_key_changes_synthetic_values ... ok
test_formats_are_reasonable ... ok
test_non_sensitive_values_preserved ... ok
test_original_pii_removed ... ok
test_output_still_contains_insert_statements ... ok
test_repeated_values_consistent_across_tables ... ok

----------------------------------------------------------------------
Ran 9 tests

OK
```

## Requirement-by-Requirement Evidence

| Assignment Requirement | Evidence |
|---|---|
| Names anonymized | `John Smith`, `Maria Garcia`, and `Patrick O'Neil` are absent from `anonymized.sql` and replaced with synthetic names |
| Addresses anonymized | All three original street addresses are absent and replaced with Faker-generated addresses |
| Emails anonymized | Original email values are absent; generated values use the syntactically valid `example.com` domain |
| Phone numbers anonymized | Original numbers are absent; punctuation patterns are preserved |
| Repeated-value consistency | John Smith's synthetic name/email/phone are identical in `customers`, `orders`, and `shipping` |
| Cross-table consistency | Repeated customer PII receives the same synthetic replacement in all three tables |
| SQL structure preserved | `CREATE TABLE` and `INSERT INTO` statements remain in the output |
| Non-sensitive values preserved | Customer IDs, order IDs, totals, statuses, loyalty levels, delivery methods, product names, and prices remain |
| One-way workflow | No reverse mapping file is generated |
| Realistic formats | Synthetic names/addresses are Faker-generated; email and phone tests validate expected formats |

## Before/After Example From the Test File

The original test record:

```text
John Smith
123 Main Street, Minneapolis, MN 55401
john.smith@gmail.com
612-555-1234
```

was transformed by the included demonstration run into:

```text
Wendy Wells
590 Ward Garden Suite 090, North Brian, MO 12432
melanie64@example.com
993-416-4005
```

The same synthetic name, email, phone, and address are reused wherever the same original value appears in the test SQL.

## Non-Sensitive Data Check

The input contains a `products` table with a generic `name` column:

```sql
(1, 'Wireless Keyboard', 49.99)
```

The output preserves `Wireless Keyboard` and `49.99`. This demonstrates the table-aware rule that avoids automatically treating every generic `name` column as a person's name.

## SQL String Escaping Check

The original data includes:

```text
Patrick O'Neil
```

represented in SQL as:

```sql
'Patrick O''Neil'
```

The parser correctly reads SQL's doubled-apostrophe escape. Synthetic replacement values are also escaped before writing, helping preserve usable SQL strings.

## Conclusion

All nine automated tests passed. The test evidence demonstrates the required four PII replacements, repeated-value consistency, cross-table consistency, format preservation, SQL preservation, and non-sensitive-data preservation.
