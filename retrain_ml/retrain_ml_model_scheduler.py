#
# Periodically call retrain_ml_model() (e.g., using a cron job or scheduler)
# 
import os
import joblib
import numpy as np
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Model Path
MODEL_PATH = "refund_model.pkl"

# Load or Train Initial Model
def load_ml_model():
    """Load existing ML model or train a new one if missing."""
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    else:
        return retrain_ml_model()

def retrain_ml_model_v2():
    """Retrain ML model based on past refund decisions."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        query = "SELECT user_id, order_id, reason, amount, final_decision FROM refund_decisions;"
        cur.execute(query)
        rows = cur.fetchall()
        
        cur.close()
        conn.close()
        
        if not rows:
            print("No data available for retraining.")
            return
        
        # Prepare data for ML training
        X = []
        y = []
        for row in rows:
            user_id, order_id, reason, amount, final_decision = row
            X.append([user_id, order_id, reason, amount])
            y.append(1 if final_decision == "approved" else 0)
        
        X = np.array(X)
        y = np.array(y)
        
        # Train and save new model
        from sklearn.ensemble import RandomForestClassifier
        new_model = RandomForestClassifier(n_estimators=100)
        new_model.fit(X, y)
        joblib.dump(new_model, MODEL_PATH)
        
        print("ML Model Retrained Successfully.")
    
    except Exception as e:
        print(f"Database Error (Retraining): {e}")

# Periodically Retrain Model
def retrain_ml_model():
    """Retrain ML model with new refund data."""
    print("🔄 Retraining ML Model...")

    # Load new refund data (replace with actual data source)
    data = pd.read_csv("refund_data.csv")  
    X = data[["user_id", "order_id", "reason_encoded", "amount"]]
    y = data["refund_outcome"]

    # Train new model
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Save model
    joblib.dump(model, MODEL_PATH)
    print("✅ ML Model Retrained & Saved!")

    return model

# Start the Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(retrain_ml_model, "cron", minute=5) #hour=0)  # Runs at midnight
scheduler.start()

# Load Model on Startup
ml_model = load_ml_model()

# Keep Script Running
if __name__ == "__main__":
    try:
        while True:
            pass  # Keeps the script running
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
