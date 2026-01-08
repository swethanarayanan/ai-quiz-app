import streamlit as st
import google.generativeai as genai
import json
import time
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="Gemini Quiz Master", page_icon="🧠")

# 1. SETUP GEMINI API
# Try getting key from secrets (cloud) or environment (local)
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
        # Note: If this model version is deprecated, use 'gemini-1.5-flash' or check available models
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
        # FIXED: Used triple quotes to allow multi-line strings safely
        msg = f"""✅ Correct! 
        
        {explanation}"""
        st.success(msg)
    else:
        # FIXED: Used triple quotes here as well
        msg = f"""❌ Wrong! The correct answer was: {correct_answer}
        
        💡 Reason: {explanation}"""
        st.error(msg)
    
    # Pause so user can read the explanation
    time.sleep(3.5) 
    st.session_state.current_question += 1
    st.rerun()

# --- UI LAYOUT ---
st.title("🧠 AI Quiz Master")

# A. START SCREEN
if not st.session_state.quiz_started:
    st.markdown("### Generate a quiz on any topic")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input("Enter Topic", placeholder="e.g. Black Holes, Ancient Rome, Python Coding")
    with col2:
        difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard", "Extreme"])
    
    if st.button("Generate Quiz", use_container_width=True):
        if topic:
            with st.spinner(f"Gemini is generating {difficulty} questions about {topic}..."):
                data = generate_questions_gemini(topic, difficulty)
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
    
    # Progress Bar
    total_q = len(st.session_state.quiz_data)
    st.progress((index) / total_q, text=f"Question {index+1} of {total_q}")
    
    # Dynamic Image
    keyword = q_data.get('image_keyword', 'abstract')
    st.image(f"[https://loremflickr.com/600/300/](https://loremflickr.com/600/300/){keyword}", use_container_width=True)
    
    st.subheader(q_data['question'])
    
    # Options Grid
    cols = st.columns(2)
    for i, opt in enumerate(q_data['options']):
        if cols[i % 2].button(opt, use_container_width=True):
            submit_answer(opt, q_data['answer'], q_data.get('explanation', ''))

# C. RESULTS SCREEN
else:
    st.balloons()
    score = st.session_state.score
    total = len(st.session_state.quiz_data)
    
    st.markdown(f"""
    <div style="text-align: center; padding: 30px; background-color: #f0f2f6; border-radius: 15px; margin-bottom: 20px;">
        <h2 style="color: #333;">Quiz Complete! 🎉</h2>
        <h1 style="font-size: 60px; color: #0068c9;">{score} / {total}</h1>
        <p style="font-size: 20px;">Topic: {st.session_state.topic}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Start New Quiz", use_container_width=True):
        restart_quiz()
