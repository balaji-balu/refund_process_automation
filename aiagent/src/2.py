import os
import asyncio
import json

import numpy as np
import joblib
from nats.aio.client import Client as NATS
from scipy.stats import zscore
from sklearn.ensemble import IsolationForest
from openai import OpenAI
from db_access import fetch_refund_data,get_user_data, get_item_details, store_ai_decision 


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_PATH = "refund_model.pkl"
ml_model = joblib.load(MODEL_PATH)


def callOpenAPI(user_id, order_id, reason, amount, user_data):
    
    item_details = get_item_details(user_id, order_id)
      
    prompt = f"""
        A customer with user ID {user_id} has requested a refund for order {order_id}.
        Refund amount: ${amount}.
        Reason: {reason}.

        User Details:
        - Account Age: {user_data['account_age']} days
        - Total Orders: {user_data['total_orders']}
        - Previous Refunds: {user_data['total_refunds']}
        - Suspicious Activity: {user_data['suspicious_activity']}
        - Item Details: {item_details}  # Fetch item details from DB if available.

        Analyze if this request seems legitimate.
        Based on this information, should this refund be APPROVED, DENIED, or sent for MANUAL REVIEW?
    """
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are an expert fraud analyst."},
                  {"role": "user", "content": prompt}]
    )

    print("prompt:", prompt)
    print("response:", response)

    ai_decision_text = response.choices[0].message.content.lower()
    print("ai_decision_text:", ai_decision_text)
    decision = "deny"
    if "review" in ai_decision_text or "additional data" in ai_decision_text:
        decision = "manual_review"
    elif "approve" in ai_decision_text:
        decision = "approve"

    return decision

# Detect anomolies
#
#   Z-Score - to detect refund amounts significantly higher than usual
#   Isolation Forest - (to detect outliers in refund frequency)
#   Real-Time Alerting (via webhooks or a message queue)
#
def detect_anomalies(user_id, amount):
    """Detect if a refund request is an anomaly using Z-Score & Isolation Forest."""
    
    # Fetch historical refund data
    refund_data = fetch_refund_data()
    if len(refund_data) < 10:  # Not enough data to analyze
        return False, "Not enough data for anomaly detection."
    print("refund_data:", refund_data)

    # Z-Score for refund amounts
    refund_amounts = refund_data[:, 1].astype(float)
    z_scores = zscore(refund_amounts)
    latest_z_score = (amount - np.mean(refund_amounts)) / np.std(refund_amounts)
    
    # Isolation Forest for user behavior
    iso_forest = IsolationForest(contamination=0.02)  # Assume 2% fraud rate
    iso_forest.fit(refund_data)
    anomaly_score = iso_forest.predict([[user_id, amount]])[0]
    
    # Define threshold for fraud
    if latest_z_score > 3 or anomaly_score == -1:
        return True, f"Potential fraud detected! Z-Score: {latest_z_score}, Isolation Score: {anomaly_score}"
    
    return False, "Normal transaction."

def analyze_refund_request(user_id, order_id, reason, amount):
    """Analyze refund request using ML, AI, and real-time anomaly detection."""
    
    # Detect anomalies before AI analysis
    is_anomaly, alert_message = detect_anomalies(user_id, amount)
    
    if is_anomaly:
        # trigger_fraud_alert(user_id, order_id, amount, reason, alert_message)
        return "manual_review"

    # Encode reason as a numerical value (simple example, should be improved)
    reason_map = {"damaged product": 1, "wrong item": 2, "payment failure": 3, "other": 0}
    reason_encoded = reason_map.get(reason, 0)

    features = np.array([[user_id, order_id, reason_encoded, amount]])
    ml_decision = ml_model.predict(features)[0]
    
    print("before calling openai")
    user_data = get_user_data(user_id)
    if not user_data:
        print("no user data")
        return "manual_review"  # Fallback if user data is unavailable
    
    ai_decision_text = callOpenAPI(user_id, order_id, reason, amount, user_data)

    final_decision = "denied"
    if ml_decision == 1 and "approve" in ai_decision_text:
        final_decision = "approved"
    elif "manual_review" in ai_decision_text:
        final_decision = "manual_review"

    # TBD: FRAUD_SCORE, 
    # store_ai_decision(refund_id, ai_decision_text, fraud_score, final_decision)

    return final_decision

async def handle_refund(user_id, order_id, reason, amount):
    """Main function to handle refund requests with AI + ML + anomaly detection."""
    decision = analyze_refund_request(user_id, order_id, reason, amount)  

    if decision == "approved":
        return {"status": "Refund Approved"}
    elif decision == "manual_review":
        return {"status": "Manual Review Required"}
    else:
        return {"status": "Refund Denied"}

async def main():
    print("Starting agent....")
    nc = NATS()

    try:
        await nc.connect("nats://nats:4222")

        async def message_handler(msg):
            subject = msg.subject
            data = json.loads(msg.data.decode())
            print(f"Received message on [{subject}]: {data}")

            # Extract relevant fields and call handle_refund
            response = await handle_refund(
                data.get("user_id"),
                data.get("order_id"),
                data.get("reason"),
                data.get("amount"),
            )
            print(f"Refund decision: {response}")

        await nc.subscribe("refund_requests", cb=message_handler)

        # Wait indefinitely until shutdown signal
        stop_event = asyncio.Event()
        await stop_event.wait()

    except asyncio.CancelledError:
        print("Shutting down gracefully...")
    finally:
        print("Closing NATS connection...")
        await nc.close()

asyncio.run(main())
