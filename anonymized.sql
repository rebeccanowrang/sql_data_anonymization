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
(101, 'Wendy Wells', '590 Ward Garden Suite 090, North Brian, MO 12432', 'melanie64@example.com', '993-416-4005', 'Gold'),
(102, 'Alex Sanchez', '21136 Michael Inlet, Lake Jacob, KS 90865', 'xclark@example.com', '(994) 942-9244', 'Silver'),
(103, 'Laura Reed MD', '234 Gregory Station, New Erica, PA 54250', 'mccannjessica@example.com', '399.841.3815', 'Gold');

INSERT INTO orders
(order_id, customer_id, customer_name, email_address, phone, order_total, status)
VALUES
(5001, 101, 'Wendy Wells', 'melanie64@example.com', '993-416-4005', 149.95, 'PAID'),
(5002, 102, 'Alex Sanchez', 'xclark@example.com', '(994) 942-9244', 89.50, 'SHIPPED'),
(5003, 101, 'Wendy Wells', 'melanie64@example.com', '993-416-4005', 220.00, 'PROCESSING');

INSERT INTO shipping
(shipping_id, customer_id, contact_name, shipping_address, phone_number, delivery_method)
VALUES
(9001, 101, 'Wendy Wells', '590 Ward Garden Suite 090, North Brian, MO 12432', '993-416-4005', 'UPS Ground'),
(9002, 102, 'Alex Sanchez', '21136 Michael Inlet, Lake Jacob, KS 90865', '(994) 942-9244', 'USPS Priority'),
(9003, 103, 'Laura Reed MD', '234 Gregory Station, New Erica, PA 54250', '399.841.3815', 'FedEx');

-- Product names are deliberately non-sensitive and should not be changed.
INSERT INTO products VALUES
(1, 'Wireless Keyboard', 49.99),
(2, 'USB-C Dock', 119.00);
