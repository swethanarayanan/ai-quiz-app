import streamlit as st
import google.generativeai as genai
import json
import time
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="Gemini Quiz Master", page_icon="🧠")

# 1. SETUP GEMINI API
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("⚠️ API Key not found! Please set 'GEMINI_API_KEY' in your secrets or environment.")
    st.stop()

genai.configure(api_key=API_KEY)

def generate_questions_gemini(topic, difficulty):
    """Generates questions with explanations using Google Gemini API."""
    try:
        # Using the newer model
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
        Create 5 {difficulty} multiple choice questions about '{topic}'.
        Return ONLY a raw JSON array. Do not use Markdown formatting (no ```json blocks).
        Structure:
        [
            {{
                "question": "Question text",
                "options": ["A", "B", "C", "D"],
                "answer": "Correct Option",
                "explanation": "A short sentence explaining why this answer is correct.",
                "image_keyword": "single_noun_visual"
            }}
        ]
        """
        
        response = model.generate_content(prompt)
        text_response = response.text
        
        # Clean up potential markdown formatting
        text_response = text_response.replace("```json", "").replace("```", "").strip()
        
        return json.loads(text_response)
    except Exception as e:
        st.error(f"Error generating quiz: {e}")
        return []

# --- APP LOGIC (State Management) ---
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = []
if 'quiz_started' not in st.session_state:
    st.session_state.quiz_started = False

def restart_quiz():
    st.session_state.score = 0
    st.session_state.current_question = 0
    st.session_state.quiz_started = False
    st.session_state.quiz_data = []
    st.rerun()

def submit_answer(option, correct_answer, explanation):
    if option == correct_answer:
        st.session_state.score += 1
        msg = f"✅ Correct! \n\n{explanation}"
        st.success(msg)
    else:
        msg = f"
