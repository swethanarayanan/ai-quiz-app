import streamlit as st
import google.generativeai as genai
import json
import time
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="Gemini Quiz App", page_icon="🧠")

# 1. SETUP GEMINI API
# We try to get the key from Streamlit Secrets (for deployment) 
# or environment variables (for local testing).
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    # If running locally without secrets.toml, you can hardcode it temporarily 
    # OR set it in your terminal: export GEMINI_API_KEY="your_key"
    API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("⚠️ API Key not found! Please set 'GEMINI_API_KEY' in your secrets or environment.")
    st.stop()

genai.configure(api_key=API_KEY)

def generate_questions_gemini(topic):
    """Generates questions using Google Gemini API."""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
        Create 5 multiple choice questions about '{topic}'.
        Return ONLY a raw JSON array. Do not use Markdown formatting (no ```json blocks).
        Structure:
        [
            {{"question": "Question text", "options": ["A", "B", "C", "D"], "answer": "Correct Option", "image_keyword": "single_noun_visual"}}
        ]
        """
        
        response = model.generate_content(prompt)
        text_response = response.text
        
        # Clean up potential markdown formatting if Gemini adds it
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

def submit_answer(option, correct_answer):
    if option == correct_answer:
        st.session_state.score += 1
        st.toast("✅ Correct!", icon="🎉")
    else:
        st.toast(f"❌ Wrong! Answer: {correct_answer}", icon="⚠️")
    
    time.sleep(1)
    st.session_state.current_question += 1
    st.rerun()

# --- UI LAYOUT ---
st.title("🧠 Gemini Quiz Generator")

# A. START SCREEN
if not st.session_state.quiz_started:
    st.markdown("Type a topic, and Gemini will generate a quiz for you.")
    topic = st.text_input("Enter Topic", placeholder="e.g. Cyberpunk, Photosynthesis, Batman")
    
    if st.button("Generate Quiz"):
        if topic:
            with st.spinner(f"Gemini is thinking about {topic}..."):
                data = generate_questions_gemini(topic)
                if data:
                    st.session_state.quiz_data = data
                    st.session_state.topic = topic
                    st.session_state.quiz_started = True
                    st.rerun()
        else:
            st.warning("Please enter a topic.")

# B. QUIZ SCREEN
elif st.session_state.current_question < len(st.session_state.quiz_data):
    index = st.session_state.current_question
    q_data = st.session_state.quiz_data[index]
    
    # Progress
    st.progress((index) / len(st.session_state.quiz_data), text=f"Question {index+1}")
    
    # Dynamic Image from LoremFlickr
    keyword = q_data.get('image_keyword', 'abstract')
    st.image(f"[https://loremflickr.com/600/300/](https://loremflickr.com/600/300/){keyword}", use_container_width=True)
    
    st.subheader(q_data['question'])
    
    # Options Grid
    cols = st.columns(2)
    for i, opt in enumerate(q_data['options']):
        if cols[i % 2].button(opt, use_container_width=True):
            submit_answer(opt, q_data['answer'])

# C. RESULTS SCREEN
else:
    st.balloons()
    score = st.session_state.score
    total = len(st.session_state.quiz_data)
    
    st.markdown(f"""
    <div style="text-align: center; padding: 20px; border: 2px solid #ddd; border-radius: 10px;">
        <h1>Score: {score} / {total}</h1>
        <p>{'🌟 Amazing!' if score == total else '👍 Good Job!'}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Start New Quiz", use_container_width=True):
        restart_quiz()
