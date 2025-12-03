import google.generativeai as genai

MODEL_NAME = "gemini-2.5-flash"

def get_gemini_model():
    return genai.GenerativeModel(MODEL_NAME)