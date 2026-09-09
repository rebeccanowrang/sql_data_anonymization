# Research Notes: Data Anonymization

## Goal

The assignment requires realistic, consistent, one-way synthetic replacement of names, addresses, email addresses, and phone numbers in a MySQL SQL export.

## Techniques Considered

### Data Masking
Masking hides all or part of a value, such as replacing a phone number with `XXX-XXX-1234`. It is useful in some contexts but does not meet this project's goal of realistic synthetic test data by itself.

### Anonymization / De-identification
NIST describes de-identification as reducing or removing the association between identifying data and the subject. The project's goal is aligned with this idea at a classroom scale: direct identifiers are replaced before the SQL file is shared for development/testing.

### Pseudonymization
Pseudonymization replaces identifiers with substitutes while preserving useful relationships. Because this program deliberately gives repeated inputs repeated synthetic outputs, it has pseudonymization-like behavior. No recovery table is created.

### Synthetic Data
Synthetic data is the best match for this assignment because test records remain realistic. Faker is used for names and addresses; deterministic synthetic values are also generated for email and phone fields.

### Hashing
Directly writing hashes into database fields would preserve consistency but produce unrealistic names/emails/addresses. Therefore, hashing is used only internally to derive deterministic random seeds.

### Tokenization
Tokenization commonly depends on a token-to-original mapping or token vault. This project does not need reversible tokens and does not create a mapping file, so tokenization was not selected.

## Selected Approach

The project combines:

1. **schema-aware field identification** using CREATE TABLE and INSERT metadata;
2. **deterministic HMAC-SHA256 seeding** for repeatable substitutions;
3. **Faker synthetic generation** for realistic data;
4. **format-preserving phone replacement**;
5. **SQL-safe string escaping**;
6. **whole-file processing** so repeated values remain consistent across tables.

## Privacy Note

This project satisfies the course requirements but should not be interpreted as a formal privacy guarantee. NIST guidance emphasizes that de-identification should be evaluated in relation to disclosure/re-identification risk. A production solution would need broader PII discovery, key management, access controls, risk assessment, and potentially stronger privacy techniques.

## Sources

- NIST SP 800-188, *De-Identifying Government Datasets: Techniques and Governance*: https://csrc.nist.gov/pubs/sp/800/188/final
- NISTIR 8053, *De-Identification of Personal Information*: https://www.nist.gov/publications/de-identification-personal-information
- Faker documentation: https://faker.readthedocs.io/
