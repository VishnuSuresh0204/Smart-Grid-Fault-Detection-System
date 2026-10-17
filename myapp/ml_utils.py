
import logging
import math

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


logger = logging.getLogger(__name__)

MODEL_NAME = "Demo Random Forest"
MODEL_VERSION = "1.1-demo"

FAULT_CLASSES = [
    "Normal",
    "Undervoltage",
    "Overvoltage",
    "Overcurrent",
    "Frequency Anomaly",
    "Combined Fault",
]

FEATURE_NAMES = [
    "voltage",
    "current",
    "frequency",
    "active_power",
    "reactive_power",
    "power_factor",
]

_model = None
_accuracy = None


# ---------------------------------------------------------
# 1. CREATE SYNTHETIC DATASET
# ---------------------------------------------------------

def create_demo_dataset(samples=10000):
    """
    Synthetic data for academic demonstrations only.
    It is not a substitute for real, labelled grid data.
    """

    rng = np.random.default_rng(42)

    voltage = rng.uniform(180, 260, samples)
    current = rng.uniform(1, 100, samples)
    frequency = rng.uniform(45, 55, samples)
    active_power = rng.uniform(0, 20000, samples)
    reactive_power = rng.uniform(0, 10000, samples)
    power_factor = rng.uniform(0.5, 1.0, samples)

    X = np.column_stack([
        voltage,
        current,
        frequency,
        active_power,
        reactive_power,
        power_factor,
    ])

    low_voltage = voltage < 210
    high_voltage = voltage > 245
    high_current = current > 80
    abnormal_frequency = (
        (frequency < 49) | (frequency > 51)
    )

    fault_count = (
        low_voltage.astype(int)
        + high_voltage.astype(int)
        + high_current.astype(int)
        + abnormal_frequency.astype(int)
    )

    y = np.full(samples, "Normal", dtype=object)

    combined = fault_count >= 2
    y[combined] = "Combined Fault"

    # Assign individual fault labels only when exactly
    # one configured abnormality exists.
    single_fault = fault_count == 1

    y[single_fault & low_voltage] = "Undervoltage"
    y[single_fault & high_voltage] = "Overvoltage"
    y[single_fault & high_current] = "Overcurrent"
    y[single_fault & abnormal_frequency] = "Frequency Anomaly"

    return X, y


# ---------------------------------------------------------
# 2. LOAD AND TRAIN MODEL
# ---------------------------------------------------------

def load_model():
    """
    Train the demonstration model once per Python process.
    """
    global _model, _accuracy

    if _model is not None:
        return _model

    X, y = create_demo_dataset()

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    model = RandomForestClassifier(
        n_estimators=150,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)

    _model = model
    _accuracy = float(accuracy)

    logger.info(
        "Synthetic demonstration model trained. "
        "Synthetic test accuracy: %.2f%%",
        _accuracy * 100,
    )

    return _model


# ---------------------------------------------------------
# 3. VALIDATE MEASUREMENTS
# ---------------------------------------------------------

def validate_measurement(measurement):
    """
    Validate numeric input before inference.
    """

    values = {}

    for field in FEATURE_NAMES:
        raw_value = getattr(measurement, field, None)

        # Missing power factor is handled as a neutral
        # demonstration value for compatibility.
        if field == "power_factor" and raw_value is None:
            raw_value = 1.0

        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            raise ValueError(
                f"Invalid measurement value: {field}"
            )

        if not math.isfinite(value):
            raise ValueError(
                f"{field} must be a finite number."
            )

        values[field] = value

    if values["voltage"] < 0:
        raise ValueError("Voltage cannot be negative.")

    if values["current"] < 0:
        raise ValueError("Current cannot be negative.")

    if values["frequency"] <= 0:
        raise ValueError("Frequency must be positive.")

    if not 0 <= values["power_factor"] <= 1:
        raise ValueError(
            "Power factor must be between 0 and 1."
        )

    return values


# ---------------------------------------------------------
# 4. GENERATE EXPLANATION
# ---------------------------------------------------------

def build_explanation(fault, values):
    explanations = {
        "Normal": (
            "The model classified the readings as Normal "
            "under the synthetic training rules. This does "
            "not establish that the grid is fault-free."
        ),
        "Undervoltage": (
            "The model classified the readings as Undervoltage. "
            "The synthetic training rule associates this class "
            "with voltage below 210 V."
        ),
        "Overvoltage": (
            "The model classified the readings as Overvoltage. "
            "The synthetic training rule associates this class "
            "with voltage above 245 V."
        ),
        "Overcurrent": (
            "The model classified the readings as Overcurrent. "
            "The synthetic training rule associates this class "
            "with current above 80 A."
        ),
        "Frequency Anomaly": (
            "The model classified the readings as a Frequency "
            "Anomaly. The synthetic training rule associates "
            "this class with frequency below 49 Hz or above 51 Hz."
        ),
        "Combined Fault": (
            "The model classified the readings as a Combined "
            "Fault. The synthetic training rules define this "
            "class when at least two configured abnormalities "
            "are present."
        ),
    }

    explanation = explanations.get(
        fault,
        "The model returned an unrecognized class.",
    )

    return (
        explanation
        + " Model inputs: "
        + ", ".join(
            f"{name}={values[name]:g}"
            for name in FEATURE_NAMES
        )
        + ". This is an academic demonstration using "
          "synthetic training data, not a validated "
          "real-world fault diagnosis."
    )


# ---------------------------------------------------------
# 5. PREDICT FAULT
# ---------------------------------------------------------

def predict_fault(measurement):
    """
    Accept an ElectricalMeasurement object and return
    the dictionary required by the existing Django view.
    """

    model = load_model()
    values = validate_measurement(measurement)

    features = np.array([[
        values[name] for name in FEATURE_NAMES
    ]], dtype=float)

    predicted_fault = str(model.predict(features)[0])

    probabilities = model.predict_proba(features)[0]
    confidence = float(np.max(probabilities)) * 100

    if predicted_fault == "Normal":
        severity = "Low"
    elif predicted_fault in [
        "Undervoltage",
        "Overvoltage",
        "Frequency Anomaly",
    ]:
        severity = "Medium"
    else:
        severity = "High"

    return {
        "predicted_fault": predicted_fault,
        "confidence_score": round(confidence, 2),
        "severity": severity,
        "is_fault": predicted_fault != "Normal",
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "accuracy": round(_accuracy * 100, 2),
        "explanation": build_explanation(
            predicted_fault,
            values,
        ),
    }
