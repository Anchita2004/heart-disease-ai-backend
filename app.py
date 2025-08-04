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

# Enable frontend access (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the Random Forest model
rf_model = joblib.load("RandomForest_model.pkl")

@app.get("/")
def root():
    return {"message": "Heart Disease AI Backend is running."}

# ---- Generate report from manual JSON input ----
@app.post("/generate-report")
async def generate_single_report(patient_data: dict):
    report = generate_patient_report(patient_data)
    return {"report": report}

# ---- Generate reports from .csv file ----
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
        report = generate_patient_report(patient, rf_model)
        reports.append(report)

    return {"reports": reports}

# ---- Upload .csv / .pdf / .jpg/.png and extract patient data ----
@app.post("/upload-report")
async def upload_report(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()

    # CSV handling
    if ext == ".csv":
        df = pd.read_csv(file.file)
        row = df.iloc[0]

    # Image (jpg/png) handling
    elif ext in [".jpg", ".jpeg", ".png"]:
        image = Image.open(io.BytesIO(await file.read()))
        text = pytesseract.image_to_string(image)
        print("=== Extracted OCR text from image ===")
        print(text)
        row = parse_text_to_row(text)

    # PDF handling with OCR fallback
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

        print("=== Extracted text from PDF (OCR-aware) ===")
        print(text)
        row = parse_text_to_row(text)

    else:
        return {"error": "Unsupported file type. Please upload .csv, .jpg, .png, or .pdf"}

    try:
        patient_data = {
            "age": int(row['Age']),
            "sex": row['Sex'],
            "ChestPainType": row['ChestPainType'],
            "RestingBP": int(row['RestingBP']),
            "Cholesterol": int(row['Cholesterol']),
            "FastingBS": int(row['FastingBS']),
            "RestingECG": row['RestingECG'],
            "MaxHR": int(row['MaxHR']),
            "ExerciseAngina": row['ExerciseAngina'],
            "Oldpeak": float(row['Oldpeak']),
            "ST_Slope": row['ST_Slope']
        }
    except Exception as e:
        return {"error": f"Failed to parse fields: {str(e)}"}

    return {"patient_data": patient_data}

# ---- Flexible regex-based parser for text input from PDF or OCR ----
def parse_text_to_row(text):
    text = text.replace("=", ":").replace(" is ", ":").replace("-", ":").replace("–", ":")
    text = re.sub(r"[ \t]+", " ", text)
    text = text.replace("\n", " ")

    data = {}

    fields = {
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

    for key, pattern in fields.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data[key] = match.group(1).strip()
        else:
            data[key] = ""

    return data