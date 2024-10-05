import streamlit as st
from groq import Groq
import random
import demjson3

# App configuration
st.set_page_config(page_title="Space Pe Charcha", page_icon="🚀", layout="wide")

# Directly use the API key from Streamlit secrets
groq_api_key = st.secrets["GROQ_API_KEY"]

if not groq_api_key:
    st.error("GROQ_API_KEY not found in Streamlit secrets. Please make sure it's correctly set in the app settings.")
    st.stop()

# Initialize Groq client
client = Groq(api_key=groq_api_key)

# Initialize session state
if "quiz_state" not in st.session_state:
    st.session_state.quiz_state = {
        "started": False,
        "difficulty": None,
        "questions": [],
        "current_question": 0,
        "score": 0,
        "topics_used": set(),
        "wrong_answers": []
    }

# ... (keep the existing helper functions: clean_json_string, generate_question)

def run_quiz():
    st.title("🚀 Space Quiz")
    st.write("---")
    
    if not st.session_state.quiz_state["started"]:
        st.write("Welcome to the Space Quiz! Choose your difficulty level:")
        col1, col2, col3 = st.columns(3)
        with col2:
            difficulty = st.radio("Select difficulty:", ["Easy", "Medium", "Hard"])
            if st.button("Start Quiz", use_container_width=True):
                st.session_state.quiz_state["started"] = True
                st.session_state.quiz_state["difficulty"] = difficulty
                st.session_state.quiz_state["questions"] = []
                st.session_state.quiz_state["current_question"] = 0
                st.session_state.quiz_state["score"] = 0
                st.session_state.quiz_state["topics_used"].clear()
                st.session_state.quiz_state["wrong_answers"] = []
                st.rerun()
    else:
        progress = st.progress(0)
        
        if st.session_state.quiz_state["current_question"] >= len(st.session_state.quiz_state["questions"]):
            new_question = generate_question(st.session_state.quiz_state["difficulty"])
            if new_question:
                st.session_state.quiz_state["questions"].append(new_question)
            else:
                st.error("Failed to generate a new question. The quiz will end here.")
                display_results()
                return
        
        if st.session_state.quiz_state["current_question"] < 10:
            question = st.session_state.quiz_state["questions"][st.session_state.quiz_state["current_question"]]
            st.subheader(f"Question {st.session_state.quiz_state['current_question'] + 1}:")
            st.write(question["question"])
            st.write("")
            answer = st.radio("Choose your answer:", question["options"], key=f"q{st.session_state.quiz_state['current_question']}")
            st.write("")
            
            col1, col2, col3 = st.columns(3)
            with col2:
                if st.button("Submit", use_container_width=True):
                    if answer == question["correct_answer"]:
                        st.session_state.quiz_state["score"] += 1
                        st.success("Correct!")
                    else:
                        st.error(f"Incorrect. The correct answer is: {question['correct_answer']}")
                        st.session_state.quiz_state["wrong_answers"].append(question)
                    
                    st.session_state.quiz_state["current_question"] += 1
                    st.rerun()
        else:
            display_results()
        
        # Update progress bar
        progress_value = min(st.session_state.quiz_state["current_question"] / 10, 1.0)
        progress.progress(progress_value)

def display_results():
    st.subheader(f"Quiz completed! Your score: {st.session_state.quiz_state['score']} out of 10")
    st.write("---")
    
    if st.session_state.quiz_state["wrong_answers"]:
        st.write("Here are the questions you got wrong, along with explanations and resources to learn more:")
        for question in st.session_state.quiz_state["wrong_answers"]:
            st.write(f"**Q: {question['question']}**")
            st.write(f"Correct answer: {question['correct_answer']}")
            st.write(f"Explanation: {question['explanation']}")
            st.write(f"Learn more: {question['resource']}")
            st.write("---")
    
    update_leaderboard(st.session_state.quiz_state['score'])
    display_leaderboard()
    
    col1, col2, col3 = st.columns(3)
    with col2:
        if st.button("Start New Quiz", use_container_width=True):
            st.session_state.quiz_state["started"] = False
            st.rerun()

# ... (keep the existing run_chat function)

def run_did_you_know():
    st.title("🌠 Cosmic Facts Explorer")
    st.write("---")
    
    if "did_you_know_state" not in st.session_state:
        st.session_state.did_you_know_state = {
            "current_fact": "Click 'Explore New Fact' to start your cosmic journey!",
            "fact_history": []
        }

    st.markdown(
        f"""
        <div style="
            background-color: #1E1E1E;
            color: #00FFFF;
            padding: 20px;
            border-radius: 10px;
            border: 2px solid #00FFFF;
            font-size: 18px;
            min-height: 150px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
        ">
            {st.session_state.did_you_know_state["current_fact"]}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")
    col1, col2, col3 = st.columns(3)
    with col2:
        if st.button("🚀 Explore New Fact", use_container_width=True):
            with st.spinner("Traversing the cosmos..."):
                response = client.chat.completions.create(
                    model="llama-3.1-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a knowledgeable assistant specializing in space and astronomy. Generate a brief, interesting, and accurate fact about space, astronomy, or cosmic phenomena."},
                        {"role": "user", "content": "Tell me an interesting fact about space."}
                    ]
                )
                new_fact = response.choices[0].message.content
                st.session_state.did_you_know_state["current_fact"] = new_fact
                st.session_state.did_you_know_state["fact_history"].append(new_fact)
            st.rerun()

    st.write("---")
    if st.session_state.did_you_know_state["fact_history"]:
        st.subheader("📚 Your Cosmic Fact Journey")
        for i, fact in enumerate(reversed(st.session_state.did_you_know_state["fact_history"]), 1):
            st.info(f"Fact #{i}: {fact}")

    st.write("---")
    st.subheader("🌟 Share Your Cosmic Knowledge")
    user_fact = st.text_area("Do you know a fascinating space fact? Share it with us!")
    if st.button("Submit Fact"):
        if user_fact:
            st.success("Thank you for sharing your cosmic wisdom! Our team of astronomers will review it.")
        else:
            st.warning("Please enter a fact before submitting.")

    st.write("---")
    st.subheader("🔭 Space Trivia Corner")
    trivia = [
        "The largest known star, UY Scuti, is about 1,700 times larger than the Sun.",
        "A day on Venus is longer than its year.",
        "The Great Red Spot on Jupiter has been raging for over 400 years.",
        "There's a planet made almost entirely of diamond.",
        "The footprints on the Moon will be there for 100 million years."
    ]
    st.info(random.choice(trivia))

def welcome_screen():
    st.title("🌟 Welcome to Space Pe Charcha! 🚀")
    st.write("Explore the wonders of space through chat, quizzes, and fascinating facts!")
    
    st.write("")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Start Chatting 💬", use_container_width=True):
            st.session_state.page = "Chat"
            st.rerun()
    with col2:
        if st.button("Take a Quiz 📝", use_container_width=True):
            st.session_state.page = "Quiz"
            st.rerun()
    with col3:
        if st.button("Explore Facts 🌠", use_container_width=True):
            st.session_state.page = "Did You Know"
            st.rerun()
    
    st.write("")
    st.markdown(
        """
        <style>
        .stAnimation {
            animation: float 6s ease-in-out infinite;
        }
        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
            100% { transform: translateY(0px); }
        }
        </style>
        <div class="stAnimation">
            <h1 style="text-align: center; font-size: 5em;">🌎 🌓 🪐</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

# ... (keep the existing leaderboard functions)

# Main app logic
if "page" not in st.session_state:
    st.session_state.page = "Welcome"

if st.session_state.page == "Welcome":
    welcome_screen()
elif st.session_state.page == "Chat":
    run_chat()
elif st.session_state.page == "Quiz":
    run_quiz()
elif st.session_state.page == "Did You Know":
    run_did_you_know()

# Sidebar navigation
with st.sidebar:
    st.title("Navigation")
    if st.button("Home 🏠", use_container_width=True):
        st.session_state.page = "Welcome"
        st.rerun()
    if st.button("Chat 💬", use_container_width=True):
        st.session_state.page = "Chat"
        st.rerun()
    if st.button("Quiz 📝", use_container_width=True):
        st.session_state.page = "Quiz"
        st.rerun()
    if st.button("Did You Know? 🌠", use_container_width=True):
        st.session_state.page = "Did You Know"
        st.rerun()
