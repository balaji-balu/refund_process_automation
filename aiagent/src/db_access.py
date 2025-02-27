import os
import psycopg2 
import numpy as np
from datetime import datetime
DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": "postgres",
    "port": 5432,
}
def fetch_refund_data():
    """Fetch historical refund data for anomaly detection."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        query = "SELECT user_id, amount FROM refund_requests;"
        cur.execute(query)
        data = cur.fetchall()
        cur.close()
        conn.close()
        
        if not data:
            return []
        
        return np.array(data)  # Returns list of [user_id, refund_amount]
    
    except Exception as e:
        print(f"Database Error: {e}")
        return []

def get_user_data(user_id):
    """Fetch user account details like age, purchase history, and previous refunds."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        query = """
        SELECT created_at, total_orders, total_refunds, flagged_for_fraud 
        FROM users WHERE user_id = %s;
        """
        cur.execute(query, (user_id,))
        user_data = cur.fetchone()
        cur.close()
        conn.close()

        if user_data:
            account_age = (datetime.now() - user_data[0]).days
            return {
                "account_age": account_age,
                "total_orders": user_data[1],
                "total_refunds": user_data[2],
                "suspicious_activity": bool(user_data[3])
            }
        return None
    except Exception as e:
        print(f"Database Error (Fetching User Data): {e}")
        return None

def get_item_details(user_id, order_id):
    """Fetch item details"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        query = """
        SELECT oi.order_id, i.item_id, i.name, oi.quantity, oi.price 
        FROM order_items oi
        JOIN items i ON oi.item_id = i.item_id
        WHERE oi.order_id = %s;
        SELECT created_at, total_orders, total_refunds, flagged_for_fraud 
        FROM users WHERE user_id = %s;
        """
        cur.execute(query, (order_id, user_id,))
        item_data = cur.fetchone()
        cur.close()
        conn.close()

        if item_data:
            account_age = (datetime.now() - user_data[0]).days
            return {
                "account_age": account_age,
                "total_orders": user_data[1],
                "total_refunds": user_data[2],
                "suspicious_activity": bool(user_data[3])
            }
        return None
    except Exception as e:
        print(f"Database Error (Fetching Item details): {e}")
        return None

def store_ai_decision(refund_id, ai_prediction, fraud_score, final_decision):
    """Store refund decision for AI learning."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        query = """
INSERT INTO refund_decisions (refund_request_id, ai_prediction, 
                              fraud_score, final_decision,
                              created_at)
VALUES (%s, %s, %s, %s, %s);
"""

        cur.execute(query, (refund_id, ai_prediction, fraud_score, 
                    final_decision, datetime.now()))

        
        conn.commit()
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Database Error (Storing Decision): {e}")