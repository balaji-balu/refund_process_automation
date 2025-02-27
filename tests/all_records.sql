CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    created_at TIMESTAMP NOT NULL,
    total_orders INT NOT NULL,
    total_refunds INT NOT NULL,
    flagged_for_fraud BOOLEAN NOT NULL
); 

INSERT INTO users (created_at, total_orders, total_refunds, flagged_for_fraud) VALUES
-- ✅ Low-risk customers
('2021-05-10', 120, 3, FALSE),  -- Long-time customer, minimal refunds
('2022-08-15', 80, 2, FALSE),   -- Mid-term customer, low refund rate

-- ⚠️ Moderate-risk customers
('2023-03-25', 15, 4, FALSE),   -- Recent user, higher refund ratio
('2023-09-30', 20, 3, TRUE),    -- New user, refund issues, flagged once

-- 🚨 High-risk customers
('2024-01-01', 5, 3, TRUE),     -- Very new customer, high refund rate, flagged
('2024-02-10', 2, 1, TRUE),     -- New user, flagged, limited purchase history

-- 🚨 Edge Cases
('2019-11-01', 300, 20, FALSE), -- Extremely loyal, many refunds (needs review)
('2024-03-01', 1, 1, TRUE);     -- One-time purchase, refunding immediately, likely fraud

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    order_date TIMESTAMP DEFAULT NOW(),
    total_price DECIMAL(10,2)
);
INSERT INTO orders (user_id, order_date, total_price) VALUES
(1, '2024-02-25 14:30:00', 1305.00),  -- Large order
(2, '2024-02-26 10:15:00', 80.00),    -- Small order
(3, '2024-02-27 11:45:00', 5000.00),  -- High-value order (suspicious)
(4, '2024-02-28 18:00:00', 7000.00);  -- Extreme order, likely fraud

CREATE TABLE items (
    item_id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    description TEXT,
    price DECIMAL(10,2),
    stock_quantity INT
);
INSERT INTO items (name, description, price, stock_quantity) VALUES
('Laptop', 'High-performance laptop', 1200.00, 10),
('Mouse', 'Wireless mouse', 25.00, 50),
('Keyboard', 'Mechanical keyboard', 80.00, 30);

CREATE TABLE order_items (
    order_id INT REFERENCES orders(order_id) ON DELETE CASCADE,
    item_id INT REFERENCES items(item_id) ON DELETE CASCADE,
    quantity INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (order_id, item_id)
);
INSERT INTO order_items (order_id, item_id, quantity, price) VALUES
(1, 1, 1, 1200.00),  -- 1 Laptop
(1, 2, 2, 25.00),    -- 2 Mice
(2, 3, 1, 80.00),    -- 1 Keyboard
(3, 1, 3, 1200.00),  -- 3 Laptops (expensive purchase)
(4, 2, 10, 25.00);   -- 10 Mice (potential bulk fraud)

CREATE TABLE refund_requests (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    order_id INT NOT NULL,
    reason TEXT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    refund_outcome TEXT NOT NULL CHECK (refund_outcome IN ('approved', 'manual_review', 'fraudulent')),
    order_date TIMESTAMP NOT NULL,
    refund_date TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO refund_requests (user_id, order_id, reason, amount, refund_outcome, order_date, refund_date) VALUES
-- ✅ Normal Refunds
(1, 1, 'damaged product', 120.00, 'approved', '2024-02-01', '2024-02-05'),
(2, 2, 'wrong item', 85.50, 'approved', '2024-02-02', '2024-02-06'),

-- 🚨 Suspicious: Refund Requested on the Same Day
(3, 3, 'damaged product', 5000.00, 'manual_review', '2024-02-07', '2024-02-07'),
(4, 4, 'wrong item', 7000.00, 'fraudulent', '2024-02-08', '2024-02-08'),

-- 🚨 High Refund Frequency
(5, 3, 'damaged product', 50.00, 'approved', '2024-02-01', '2024-02-02'),
(5, 3, 'damaged product', 55.00, 'manual_review', '2024-02-02', '2024-02-03'),
(5, 3, 'damaged product', 60.00, 'fraudulent', '2024-02-03', '2024-02-04'),

-- 🚨 Unusual Reasons
(6, 4, 'refund requested for no reason', 250.00, 'manual_review', '2024-02-05', '2024-02-10'),
(7, 4, 'claimed item never shipped but tracking shows delivered', 900.00, 'fraudulent', '2024-02-05', '2024-02-12');

CREATE TABLE refund_decisions (
    id SERIAL PRIMARY KEY,         -- Unique identifier for each decision
    refund_request_id INT NOT NULL, -- Foreign key referencing refund_requests
    ai_prediction VARCHAR(20) CHECK (ai_prediction IN ('approved', 'manual_review', 'fraudulent')), 
    fraud_score DECIMAL(5,2) CHECK (fraud_score BETWEEN 0 AND 100), -- Fraud score (0-100 scale)
    final_decision VARCHAR(20) CHECK (final_decision IN ('approved', 'rejected', 'manual_review')),
    reviewed_by INT NULL,          -- Nullable, stores the admin ID if manually reviewed
    decision_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp of decision
    FOREIGN KEY (refund_request_id) REFERENCES refund_requests(id) ON DELETE CASCADE
);

INSERT INTO refund_decisions (refund_request_id, ai_prediction, fraud_score, final_decision, reviewed_by) VALUES
-- ✅ AI & Admin Agree on Approvals
(1, 'approved', 5.00, 'approved', NULL),
(2, 'approved', 10.00, 'approved', NULL),

-- 🚨 AI Flags for Review, Admin Approves
(3, 'manual_review', 45.00, 'approved', 201), 

-- 🚨 AI Flags as Fraudulent, Admin Confirms
(4, 'fraudulent', 90.00, 'rejected', 202),
(5, 'fraudulent', 85.00, 'rejected', 202),

-- 🚨 AI Suggests Review, Admin Rejects
(6, 'manual_review', 50.00, 'rejected', 203),
(7, 'manual_review', 60.00, 'rejected', 204);
