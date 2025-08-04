def assess_risk_explained(row):
    score = 0
    reasons = []

    # Age-based risk threshold by sex
    if (row['sex'] == 'M' and row['age'] >= 55) or (row['sex'] == 'F' and row['age'] >= 65):
        score += 1
        reasons.append("Older age based on gender-specific threshold")

    # Resting Blood Pressure
    if row['RestingBP'] >= 140:
        score += 2
        reasons.append("High RestingBP (≥140 mmHg)")

    # Cholesterol Levels
    if row['Cholesterol'] >= 240:
        score += 2
        reasons.append("High Cholesterol (≥240 mg/dL)")
    elif row['Cholesterol'] >= 200:
        score += 1
        reasons.append("Borderline high Cholesterol (200–239 mg/dL)")

    # Fasting Blood Sugar
    if row['FastingBS'] == 1:
        score += 1
        reasons.append("Elevated Fasting Blood Sugar (>120 mg/dL)")

    # ECG Abnormalities
    if row['RestingECG'] in ['ST', 'LVH']:
        score += 1
        reasons.append(f"Abnormal ECG ({row['RestingECG']})")

    # Chest Pain Type
    chest_pain_score = {'TA': 2, 'ATA': 1, 'NAP': 0.5, 'ASY': 0}
    cp_score = chest_pain_score.get(row['ChestPainType'], 0)
    score += cp_score
    if cp_score:
        reasons.append(f"Chest Pain Type: {row['ChestPainType']}")

    # Exercise-Induced Angina
    if row['ExerciseAngina'] == 'Y':
        score += 1
        reasons.append("Exercise-induced angina")

    # Max Heart Rate
    expected_max_hr = (220 - row['age']) * 0.8
    if row['MaxHR'] < expected_max_hr:
        score += 1
        reasons.append(f"Low MaxHR ({row['MaxHR']} < expected {expected_max_hr:.0f})")

    # ST depression (Oldpeak)
    if row['Oldpeak'] >= 2.0:
        score += 2
        reasons.append("Significant ST depression (Oldpeak ≥ 2.0)")
    elif row['Oldpeak'] >= 1.0:
        score += 1
        reasons.append("Moderate ST depression (1.0–1.99)")

    # ST Slope
    st_slope_score = {'Down': 2, 'Flat': 1}
    slope_score = st_slope_score.get(row['ST_Slope'], 0)
    score += slope_score
    if slope_score:
        reasons.append(f"ST Slope: {row['ST_Slope']}")

    # Final risk level based on total score
    if score >= 7:
        level = "High Risk"
    elif score >= 4:
        level = "Moderate Risk"
    elif score >= 1:
        level = "Low Risk"
    else:
        level = "Minimal Risk"

    return level, score, reasons


def get_recommendations_with_explanation(level):
    rec = {"medicine_classes": [], "preventions": [], "treatment_plan": ""}

    if level == "High Risk":
        rec["medicine_classes"] = [
            "Statin (lipid-lowering)",
            "ACE inhibitors or ARBs (antihypertensive)",
            "Beta-blockers (if symptomatic)"
        ]
        rec["preventions"] = [
            "Adopt a heart-healthy diet (e.g., DASH/Mediterranean)",
            "Minimum 150 min moderate exercise/week",
            "Strict BP, sugar, and cholesterol control",
            "No smoking",
            "Sleep hygiene: 7–9 hours/night"
        ]
        rec["treatment_plan"] = (
            "Refer to cardiologist, initiate medication, consider ECHO or stress testing, "
            "follow-up every 1–2 months"
        )

    elif level == "Moderate Risk":
        rec["medicine_classes"] = [
            "Consider statin if borderline cholesterol",
            "ACE-I if BP elevated"
        ]
        rec["preventions"] = [
            "Lifestyle improvements (diet, activity)",
            "Monitor vitals quarterly",
            "Avoid smoking"
        ]
        rec["treatment_plan"] = (
            "Primary care review every 3–6 months; consider diagnostics if new symptoms"
        )

    elif level == "Low Risk":
        rec["medicine_classes"] = []
        rec["preventions"] = [
            "Maintain regular physical activity",
            "Balanced diet",
            "Annual screenings"
        ]
        rec["treatment_plan"] = "Routine checkup annually"

    else:
        rec["medicine_classes"] = []
        rec["preventions"] = [
            "General healthy living habits"
        ]
        rec["treatment_plan"] = "No specific intervention needed"

    return rec


def generate_patient_report(patient_data):
    level, score, reasons = assess_risk_explained(patient_data)
    recs = get_recommendations_with_explanation(level)

    report = f"🧠 Risk Level: {level} (Score: {score})\n\n📌 Reasons for Risk Score:\n"
    for reason in reasons:
        report += f" - {reason}\n"

    report += "\n💊 Recommended Medication Classes:\n"
    for med in recs["medicine_classes"]:
        report += f" - {med}\n"

    report += "\n🛡 Preventive Measures:\n"
    for tip in recs["preventions"]:
        report += f" - {tip}\n"

    report += f"\n📝 Treatment Plan:\n{recs['treatment_plan']}\n"
    return report
