from dotenv import load_dotenv
load_dotenv()
import os
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from services.gemini_client import get_gemini_model
from services.analysis_prompt import build_analysis_prompt, build_chat_prompt
from utils.json_parse import try_parse_structured_response

app = Flask(__name__)
CORS(app, origins=os.getenv("CORS_ORIGINS", "*"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

SUPPORTED_LANGUAGES = [
    "English","हिंदी (Hindi)","ಕನ್ನಡ (Kannada)","தமிழ் (Tamil)","తెలుగు (Telugu)",
    "मराठी (Marathi)","বাংলা (Bengali)","ગુજરાતી (Gujarati)","ਪੰਜਾਬੀ (Punjabi)",
    "മലയാളം (Malayalam)","ଓଡ଼ିଆ (Odia)","Hinglish (Hindi + English)","Kanglish (Kannada + English)"
]

def extract_image_bytes(data_url: str) -> bytes:
    if "," not in data_url:
        raise ValueError("Invalid data URL")
    header, b64 = data_url.split(",", 1)
    return base64.b64decode(b64)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/languages", methods=["GET"])
def languages():
    return jsonify({"languages": SUPPORTED_LANGUAGES})

@app.route("/analyze", methods=["POST"])
def analyze():
    payload = request.get_json(force=True)
    data_url = payload.get("image")
    target_lang = payload.get("language", "English")
    if not data_url:
        return jsonify({"error": "image (data URL) required"}), 400
    if target_lang not in SUPPORTED_LANGUAGES:
        target_lang = "English"

    try:
        image_bytes = extract_image_bytes(data_url)
    except Exception as e:
        return jsonify({"error": f"Failed to decode image: {e}"}), 400

    vision_model = get_gemini_model()
    # Step 1: Extract math text & user work
    vision_prompt = [
        "Extract ALL math text and working steps from this image. Return ONLY raw text, no commentary.",
        {"mime_type": "image/jpeg", "data": image_bytes}
    ]
    vision_resp = vision_model.generate_content(vision_prompt)
    raw_math_text = (vision_resp.text or "").strip()

    # Step 2: Structured analysis in requested language
    analysis_prompt = build_analysis_prompt(raw_math_text, target_lang)
    analysis_resp = vision_model.generate_content(analysis_prompt)
    raw_analysis = (analysis_resp.text or "").strip()

    structured = try_parse_structured_response(raw_analysis)
    if not structured:
        # Fallback: simple unstructured explanation
        structured = {
            "title": f"Analysis ({target_lang})",
            "steps": [{"status": "info", "text": raw_analysis}],
            "correction": "No structured correction available.",
            "extracted_text": raw_math_text
        }

    return jsonify(structured)

@app.route("/chat", methods=["POST"])
def chat():
    payload = request.get_json(force=True)
    question = payload.get("question")
    language = payload.get("language", "English")
    prior_steps = payload.get("steps", [])
    if not question:
        return jsonify({"error": "question required"}), 400
    model = get_gemini_model()
    chat_prompt = build_chat_prompt(question, prior_steps, language)
    resp = model.generate_content(chat_prompt)
    return jsonify({"answer": (resp.text or "").strip()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))