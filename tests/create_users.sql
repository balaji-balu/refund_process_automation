CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    created_at TIMESTAMP NOT NULL,
    total_orders INT NOT NULL,
    total_refunds INT NOT NULL,
    flagged_for_fraud BOOLEAN NOT NULL
); 
INSERT INTO users (user_id, created_at, total_orders, total_refunds, flagged_for_fraud) VALUES
(101, '2022-01-15', 50, 2, FALSE),  -- Long-time customer, few refunds, no fraud history
(102, '2023-06-20', 10, 1, FALSE),  -- Newer customer, occasional refund
(103, '2024-01-05', 5, 3, TRUE),    -- Recent customer, multiple refunds, flagged for fraud
(104, '2020-11-30', 100, 5, FALSE), -- Loyal customer, but has multiple refunds
(105, '2024-02-10', 2, 1, TRUE);    -- Very new customer, flagged for fraud

-- Low-risk customers
(201, '2021-05-10', 120, 3, FALSE),  -- Long-time customer, minimal refunds, no fraud
(202, '2022-08-15', 80, 2, FALSE),   -- Mid-term customer, low refund rate

-- Moderate-risk customers
(203, '2023-03-25', 15, 4, FALSE),   -- Recent user, higher refund ratio
(204, '2023-09-30', 20, 3, TRUE),    -- Newer user, refund issues, flagged once for fraud

-- High-risk customers
(205, '2024-01-01', 5, 3, TRUE),     -- Very new customer, high refund rate, flagged
(206, '2024-02-10', 2, 1, TRUE),     -- New user, flagged, limited purchase history

-- Edge cases
(207, '2019-11-01', 300, 20, FALSE), -- Extremely loyal customer, many refunds (needs review)
(208, '2024-03-01', 1, 1, TRUE);     -- One-time purchase, refunding immediately, likely fraud

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    order_date TIMESTAMP DEFAULT NOW(),
    total_price DECIMAL(10,2)
);

CREATE TABLE items (
    item_id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    description TEXT,
    price DECIMAL(10,2),
    stock_quantity INT
);

CREATE TABLE order_items (
    order_id INT REFERENCES orders(order_id) ON DELETE CASCADE,
    item_id INT REFERENCES items(item_id) ON DELETE CASCADE,
    quantity INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (order_id, item_id)
);

INSERT INTO items (item_id, name, description, price, stock_quantity) VALUES
(1, 'Laptop', 'High-performance laptop', 1200.00, 10),
(2, 'Mouse', 'Wireless mouse', 25.00, 50),
(3, 'Keyboard', 'Mechanical keyboard', 80.00, 30);

INSERT INTO orders (order_id, user_id, order_date, total_price) VALUES
(101, 1, '2024-02-25 14:30:00', 1305.00),
(102, 2, '2024-02-26 10:15:00', 80.00);

INSERT INTO order_items (order_id, item_id, quantity, price) VALUES
(101, 1, 1, 1200.00),  -- 1 Laptop
(101, 2, 2, 25.00),    -- 2 Mice
(102, 3, 1, 80.00);    -- 1 Keyboard