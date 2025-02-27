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
-- ✅ Normal Refunds (Ordered → Refunded After Few Days)
(101, 5001, 'damaged product', 120.00, 'approved', '2024-02-01', '2024-02-05'),
(102, 5002, 'wrong item', 85.50, 'approved', '2024-02-02', '2024-02-06'),
(103, 5003, 'payment failure', 45.75, 'approved', '2024-02-03', '2024-02-04'),

-- 🚨 Suspicious: Refund Requested on the Same Day as Order
(104, 5004, 'damaged product', 5000.00, 'manual_review', '2024-02-07', '2024-02-07'),
(105, 5005, 'wrong item', 7000.00, 'fraudulent', '2024-02-08', '2024-02-08'),

-- 🚨 High Refund Frequency (User 106 Requests Multiple Refunds)
(106, 5006, 'damaged product', 50.00, 'approved', '2024-02-01', '2024-02-02'),
(106, 5007, 'damaged product', 55.00, 'manual_review', '2024-02-02', '2024-02-03'),
(106, 5008, 'damaged product', 60.00, 'fraudulent', '2024-02-03', '2024-02-04'),

-- 🚨 Unusual Reasons (Manual Review & Fraudulent)
(107, 5009, 'refund requested for no reason', 250.00, 'manual_review', '2024-02-05', '2024-02-10'),
(108, 5010, 'claimed item never shipped but tracking shows delivered', 900.00, 'fraudulent', '2024-02-05', '2024-02-12');

-- SELECT * FROM refund_requests 
-- WHERE order_date = refund_date;

-- SELECT *, refund_date - order_date AS days_to_refund
-- FROM refund_requests
-- WHERE refund_date - order_date > INTERVAL '30 days';

CREATE TABLE refund_decisions (
    id SERIAL PRIMARY KEY,
    refund_request_id INT NOT NULL REFERENCES refund_requests(id) ON DELETE CASCADE,
    ai_prediction TEXT NOT NULL CHECK (ai_prediction IN ('approved', 'manual_review', 'fraudulent')),
    fraud_score DECIMAL(5,2) CHECK (fraud_score BETWEEN 0 AND 100),
    final_decision TEXT NOT NULL CHECK (final_decision IN ('approved', 'manual_review', 'rejected')),
    reviewed_by INT NULL, -- Admin/User ID if manually reviewed
    decision_date TIMESTAMP DEFAULT NOW()
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

-- SELECT * FROM refund_decisions WHERE fraud_score > 80;

-- SELECT * FROM refund_decisions 
-- WHERE ai_prediction != final_decision;

-- SELECT * FROM refund_decisions 
-- WHERE ai_prediction = 'manual_review' AND final_decision = 'approved';