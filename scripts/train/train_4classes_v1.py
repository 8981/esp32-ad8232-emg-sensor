import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

CSV = "../data/emg_4classes_v1.csv"
MODEL_FILE = "../model/emg_4classes_model_v1.joblib"

feature_cols = [
    "m1", "s1", "a1", "p1",
    "m2", "s2", "a2", "p2",
    "m3", "s3", "a3", "p3"
]

class_labels = [0, 1, 2, 3]
class_names = ["REST", "FIST", "WRIST_UP", "WRIST_DOWN"]

df = pd.read_csv(CSV)

print("Loaded:", CSV)
print("Rows:", len(df))

print("\nLabel distribution:")
print(df["label"].value_counts().sort_index())

df = df[df["label"].isin(class_labels)].copy()

X = df[feature_cols].values
y = df["label"].values

if len(df) < 100:
    raise ValueError("Dataset is too small. Record more data first.")

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    random_state=42,
    stratify=y
)

model = make_pipeline(
    StandardScaler(),
    LogisticRegression(
        max_iter=5000,
        solver="lbfgs"
    )
)

model.fit(X_train, y_train)

pred = model.predict(X_test)

print("\nTest accuracy:", accuracy_score(y_test, pred))

print("\nClassification report:")
print(classification_report(
    y_test,
    pred,
    labels=class_labels,
    target_names=class_names
))

print("\nConfusion matrix:")
print(confusion_matrix(y_test, pred, labels=class_labels))

joblib.dump(model, MODEL_FILE)

print("\nSaved:", MODEL_FILE)