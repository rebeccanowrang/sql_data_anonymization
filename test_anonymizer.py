import re
import unittest

from anonymizer import anonymize_sql


SAMPLE = """
CREATE TABLE customers (
    customer_id INT,
    name VARCHAR(100),
    address VARCHAR(200),
    email VARCHAR(100),
    phone VARCHAR(30),
    loyalty_level VARCHAR(20)
);

CREATE TABLE orders (
    order_id INT,
    customer_id INT,
    customer_name VARCHAR(100),
    email_address VARCHAR(100),
    phone VARCHAR(30),
    status VARCHAR(20)
);

CREATE TABLE products (
    product_id INT,
    name VARCHAR(100),
    price DECIMAL(10,2)
);

INSERT INTO customers VALUES
(101, 'John Smith', '123 Main Street, Minneapolis, MN 55401',
 'john.smith@gmail.com', '612-555-1234', 'Gold');

INSERT INTO orders
(order_id, customer_id, customer_name, email_address, phone, status)
VALUES
(5001, 101, 'John Smith', 'john.smith@gmail.com', '612-555-1234', 'PAID'),
(5002, 101, 'John Smith', 'john.smith@gmail.com', '612-555-1234', 'SHIPPED');

INSERT INTO products VALUES
(1, 'Wireless Keyboard', 49.99);
"""


class TestSQLAnonymizer(unittest.TestCase):
    def setUp(self):
        self.output, self.engine = anonymize_sql(SAMPLE, key="unit-test-key")

    def test_original_pii_removed(self):
        for value in [
            "John Smith",
            "123 Main Street, Minneapolis, MN 55401",
            "john.smith@gmail.com",
            "612-555-1234",
        ]:
            self.assertNotIn(value, self.output)

    def test_all_four_categories_anonymized(self):
        self.assertEqual(1, len(self.engine.mappings["name"]))
        self.assertEqual(1, len(self.engine.mappings["address"]))
        self.assertEqual(1, len(self.engine.mappings["email"]))
        self.assertEqual(1, len(self.engine.mappings["phone"]))

    def test_repeated_values_consistent_across_tables(self):
        new_name = self.engine.mappings["name"]["John Smith"]
        new_email = self.engine.mappings["email"]["john.smith@gmail.com"]
        new_phone = self.engine.mappings["phone"]["612-555-1234"]

        self.assertEqual(3, self.output.count("'" + new_name.replace("'", "''") + "'"))
        self.assertEqual(3, self.output.count("'" + new_email + "'"))
        self.assertEqual(3, self.output.count("'" + new_phone + "'"))

    def test_formats_are_reasonable(self):
        new_email = self.engine.mappings["email"]["john.smith@gmail.com"]
        new_phone = self.engine.mappings["phone"]["612-555-1234"]
        new_address = self.engine.mappings["address"]["123 Main Street, Minneapolis, MN 55401"]

        self.assertRegex(new_email, r"^[A-Za-z0-9._-]+@example\.com$")
        self.assertRegex(new_phone, r"^\d{3}-\d{3}-\d{4}$")
        self.assertRegex(new_address, r".+,\s*.+,\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?$")

    def test_non_sensitive_values_preserved(self):
        for value in ["101", "5001", "5002", "Gold", "PAID", "SHIPPED", "49.99", "Wireless Keyboard"]:
            self.assertIn(value, self.output)

    def test_create_table_structure_preserved(self):
        self.assertIn("CREATE TABLE customers", self.output)
        self.assertIn("CREATE TABLE orders", self.output)
        self.assertIn("CREATE TABLE products", self.output)

    def test_output_still_contains_insert_statements(self):
        self.assertEqual(3, len(re.findall(r"INSERT\s+INTO", self.output, flags=re.I)))

    def test_deterministic_with_same_key(self):
        output2, _ = anonymize_sql(SAMPLE, key="unit-test-key")
        self.assertEqual(self.output, output2)

    def test_different_key_changes_synthetic_values(self):
        output2, _ = anonymize_sql(SAMPLE, key="different-key")
        self.assertNotEqual(self.output, output2)


if __name__ == "__main__":
    unittest.main()
