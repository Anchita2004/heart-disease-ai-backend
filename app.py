from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from agent_logic import generate_patient_report
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
import io
import os
import re
import joblib

app = FastAPI()

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model
rf_model = joblib.load("RandomForest_model.pkl")

@app.get("/")
def root():
    return {"message": "Heart Disease AI Backend is running."}

# Manual JSON input
@app.post("/generate-report")
async def generate_single_report(patient_data: dict):
    report = generate_patient_report(patient_data)
    return {"report": report}

# CSV batch report
@app.post("/generate-batch-report")
async def generate_batch_report(file: UploadFile = File(...)):
    df = pd.read_csv(file.file)
    reports = []

    for _, row in df.iterrows():
        patient = {
            'age': row['Age'],
            'sex': row['Sex'],
            'ChestPainType': row['ChestPainType'],
            'RestingBP': row['RestingBP'],
            'Cholesterol': row['Cholesterol'],
            'FastingBS': row['FastingBS'],
            'RestingECG': row['RestingECG'],
            'MaxHR': row['MaxHR'],
            'ExerciseAngina': row['ExerciseAngina'],
            'Oldpeak': row['Oldpeak'],
            'ST_Slope': row['ST_Slope']
        }
        report = generate_patient_report(patient)
        reports.append(report)

    return {"reports": reports}

# PDF/CSV/Image input
@app.post("/upload-report")
async def upload_report(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()

    try:
        # ---- CSV ----
        if ext == ".csv":
            df = pd.read_csv(file.file)
            row = df.iloc[0]

        # ---- Image ----
        elif ext in [".jpg", ".jpeg", ".png"]:
            image = Image.open(io.BytesIO(await file.read()))
            text = pytesseract.image_to_string(image)
            print("🧠 OCR Text (Image):", text)
            row = parse_text_to_row(text)

        # ---- PDF ----
        elif ext == ".pdf":
            text = ""
            with pdfplumber.open(io.BytesIO(await file.read())) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    else:
                        image = page.to_image(resolution=300).original
                        text += pytesseract.image_to_string(image) + "\n"
            print("📄 OCR Text (PDF):", text)
            row = parse_text_to_row(text)

        else:
            return {"error": "❌ Unsupported file type. Use .csv, .pdf, .jpg, or .png"}

        # Map fields
        patient_data = {
            "age": int(row.get('Age', 0)),
            "sex": row.get('Sex', 'M'),
            "ChestPainType": row.get('ChestPainType', 'ATA'),
            "RestingBP": int(row.get('RestingBP', 120)),
            "Cholesterol": int(row.get('Cholesterol', 200)),
            "FastingBS": int(row.get('FastingBS', 0)),
            "RestingECG": row.get('RestingECG', 'Normal'),
            "MaxHR": int(row.get('MaxHR', 150)),
            "ExerciseAngina": row.get('ExerciseAngina', 'N'),
            "Oldpeak": float(row.get('Oldpeak', 0.0)),
            "ST_Slope": row.get('ST_Slope', 'Up')
        }

        return {"patient_data": patient_data}

    except Exception as e:
        return {"error": f"❌ Failed to extract patient data: {str(e)}"}

# ---- OCR parser ----
def parse_text_to_row(text):
    text = text.replace("=", ":").replace(" is ", ":").replace("-", ":").replace("–", ":")
    text = re.sub(r"[ \t]+", " ", text).replace("\n", " ")
    data = {}

    patterns = {
        'Age': r"Age[:\-]?\s*(\d+)",
        'Sex': r"Sex[:\-]?\s*([MF])",
        'ChestPainType': r"Chest ?Pain ?Type[:\-]?\s*(ATA|NAP|ASY|TA)",
        'RestingBP': r"(?:RestingBP|BP)[:\-]?\s*(\d+)",
        'Cholesterol': r"Cholesterol[:\-]?\s*(\d+)",
        'FastingBS': r"FastingBS[:\-]?\s*(0|1)",
        'RestingECG': r"RestingECG[:\-]?\s*(Normal|ST|LVH)",
        'MaxHR': r"MaxHR[:\-]?\s*(\d+)",
        'ExerciseAngina': r"Exercise ?Angina[:\-]?\s*([YN])",
        'Oldpeak': r"Oldpeak[:\-]?\s*(\d+\.?\d*)",
        'ST_Slope': r"(?:ST[_ ]Slope|ST Slope)[:\-]?\s*(Up|Flat|Down)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data[key] = match.group(1).strip()
        else:
            print(f"⚠️ Could not find {key} in OCR text.")
            data[key] = ""

    return data
