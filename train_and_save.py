import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

CSV = "emg_rest_fist_v2.csv"

df = pd.read_csv(CSV)

feature_cols = ["m1","s1","a1","p1",
                "m2","s2","a2","p2",
                "m3","s3","a3","p3"]

df = df[df["label"].isin([0, 1])].copy()

X = df[feature_cols].values
y = df["label"].values

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)

model = make_pipeline(
    StandardScaler(),
    LogisticRegression(max_iter=4000, solver="lbfgs")
)

model.fit(X_train, y_train)
pred = model.predict(X_test)

print("Test accuracy:", accuracy_score(y_test, pred))

joblib.dump(model, "rest_fist_model.joblib")
print("Saved: rest_fist_model.joblib")