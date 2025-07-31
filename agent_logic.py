def assess_risk_explained(row):
    score = 0
    reasons = []

    if (row['sex'] == 'M' and row['age'] >= 55) or (row['sex'] == 'F' and row['age'] >= 65):
        score += 1
        reasons.append("Age ≥ threshold for sex (increased age risk)")

    if row['RestingBP'] >= 140:
        score += 2
        reasons.append("High resting BP ≥140 mm Hg")

    if row['Cholesterol'] >= 240:
        score += 2
        reasons.append("Cholesterol ≥240 mg/dL")
    elif row['Cholesterol'] >= 200:
        score += 1
        reasons.append("Borderline high cholesterol (200–239)")

    if row['FastingBS'] == 1:
        score += 1
        reasons.append("Elevated fasting blood sugar >120 mg/dL")

    if row['RestingECG'] in ['ST', 'LVH']:
        score += 1
        reasons.append("Abnormal resting ECG (ST-T changes or LVH)")

    if row['ChestPainType'] == 'TA':
        score += 2
        reasons.append("Typical angina")
    elif row['ChestPainType'] == 'ATA':
        score += 1
        reasons.append("Atypical angina")

    if row['ExerciseAngina'] == 'Y':
        score += 1
        reasons.append("Exercise-induced angina")

    expected_max_hr = (220 - row['age']) * 0.8
    if row['MaxHR'] < expected_max_hr:
        score += 1
        reasons.append(f"MaxHR {row['MaxHR']} below expected {expected_max_hr:.0f}")

    if row['Oldpeak'] >= 2.0:
        score += 2
        reasons.append("Oldpeak ≥2.0 (ST depression ≥2)")
    elif row['Oldpeak'] >= 1.0:
        score += 1
        reasons.append("Oldpeak 1.0–1.99 ST depression")

    if row['ST_Slope'] == 'Down':
        score += 2
        reasons.append("ST slope down")
    elif row['ST_Slope'] == 'Flat':
        score += 1
        reasons.append("ST slope flat")

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
    rec = {"medicine_classes": [], "preventions": [], "treatment_plan": None}
    if level == "High Risk":
        rec["medicine_classes"] = [
            "Statin therapy (if cholesterol high)",
            "Antihypertensive (ACE-I/ARB)",
            "Beta-blocker (if angina or ischemia)"
        ]
        rec["preventions"] = [
            "Mediterranean/plant-based diet (Life’s Essential 8)",
            "150 min moderate exercise/week",
            "Blood pressure <130/80, blood sugar & cholesterol control",
            "Smoking cessation",
            "Adequate sleep (7–9 h)"
        ]
        rec["treatment_plan"] = (
            "Refer to cardiologist; start guideline-directed medical therapy; "
            "close follow-up every 1–2 months; consider stress testing/ECHO"
        )
    elif level == "Moderate Risk":
        rec["medicine_classes"] = ["Lifestyle first; consider ACE-I if BP elevated"]
        rec["preventions"] = [
            "Heart-healthy lifestyle (diet, exercise)",
            "Monitor BP/sugar/cholesterol regularly",
            "Smoking cessation if applicable"
        ]
        rec["treatment_plan"] = (
            "Primary care follow-up every 3–6 months; consider statin "
            "if cholesterol rising; stress test if symptoms develop"
        )
    elif level == "Low Risk":
        rec["medicine_classes"] = ["None typically"]
        rec["preventions"] = [
            "Maintain healthy diet and exercise",
            "Annual screening of BP, sugar, cholesterol"
        ]
        rec["treatment_plan"] = "Annual wellness checks"
    else:
        rec["medicine_classes"] = ["None"]
        rec["preventions"] = [
            "Keep active, healthy diet, standard screenings"
        ]
        rec["treatment_plan"] = "Routine annual checkups"
    return rec

def generate_patient_report(patient_data):
    level, score, reasons = assess_risk_explained(patient_data)
    recs = get_recommendations_with_explanation(level)

    report = f"🧠 Risk Level: {level} (Score: {score})\n\n"
    report += "📌 Reasons:\n"
    for r in reasons:
        report += f" - {r}\n"

    report += "\n💊 Suggested Medicine Classes (for doctor consideration):\n"
    for med in recs['medicine_classes']:
        report += f" - {med}\n"

    report += "\n🛡 Prevention Recommendations:\n"
    for tip in recs['preventions']:
        report += f" - {tip}\n"

    report += f"\n📝 Treatment Plan:\n{recs['treatment_plan']}\n"

    return report
