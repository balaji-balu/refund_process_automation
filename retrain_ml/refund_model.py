import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Sample Data (User ID, Order ID, Reason Encoded, Amount, Label: 1=Approve, 0=Review)
data = np.array([
    [101, 2001, 1, 500, 1],  # Approved
    [102, 2002, 2, 1200, 0], # Manual review
    [103, 2003, 3, 300, 1],  # Approved
    [104, 2004, 0, 1500, 0], # Manual review
])

X = data[:, :-1]  # Features (User ID, Order ID, Reason Encoded, Amount)
y = data[:, -1]   # Labels (1=Approved, 0=Manual Review)

# Split Data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train Model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Save Model
joblib.dump(model, "refund_model.pkl")

print("Refund Model Saved!")
