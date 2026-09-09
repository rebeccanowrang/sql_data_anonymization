-- ICS 499 sample input for SQL Data Anonymization
-- The records below are fictional test data created for this assignment.

CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    name VARCHAR(100),
    address VARCHAR(200),
    email VARCHAR(100),
    phone VARCHAR(30),
    loyalty_level VARCHAR(20)
);

CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT,
    customer_name VARCHAR(100),
    email_address VARCHAR(100),
    phone VARCHAR(30),
    order_total DECIMAL(10,2),
    status VARCHAR(20)
);

CREATE TABLE shipping (
    shipping_id INT PRIMARY KEY,
    customer_id INT,
    contact_name VARCHAR(100),
    shipping_address VARCHAR(200),
    phone_number VARCHAR(30),
    delivery_method VARCHAR(30)
);

CREATE TABLE products (
    product_id INT PRIMARY KEY,
    name VARCHAR(100),
    price DECIMAL(10,2)
);

INSERT INTO customers VALUES
(101, 'John Smith', '123 Main Street, Minneapolis, MN 55401', 'john.smith@gmail.com', '612-555-1234', 'Gold'),
(102, 'Maria Garcia', '455 Lake Avenue, St. Paul, MN 55104', 'maria.garcia@yahoo.com', '(651) 555-8822', 'Silver'),
(103, 'Patrick O''Neil', '88 Cedar Road, Duluth, MN 55802', 'patrick.oneil@example.net', '218.555.0198', 'Gold');

INSERT INTO orders
(order_id, customer_id, customer_name, email_address, phone, order_total, status)
VALUES
(5001, 101, 'John Smith', 'john.smith@gmail.com', '612-555-1234', 149.95, 'PAID'),
(5002, 102, 'Maria Garcia', 'maria.garcia@yahoo.com', '(651) 555-8822', 89.50, 'SHIPPED'),
(5003, 101, 'John Smith', 'john.smith@gmail.com', '612-555-1234', 220.00, 'PROCESSING');

INSERT INTO shipping
(shipping_id, customer_id, contact_name, shipping_address, phone_number, delivery_method)
VALUES
(9001, 101, 'John Smith', '123 Main Street, Minneapolis, MN 55401', '612-555-1234', 'UPS Ground'),
(9002, 102, 'Maria Garcia', '455 Lake Avenue, St. Paul, MN 55104', '(651) 555-8822', 'USPS Priority'),
(9003, 103, 'Patrick O''Neil', '88 Cedar Road, Duluth, MN 55802', '218.555.0198', 'FedEx');

-- Product names are deliberately non-sensitive and should not be changed.
INSERT INTO products VALUES
(1, 'Wireless Keyboard', 49.99),
(2, 'USB-C Dock', 119.00);
