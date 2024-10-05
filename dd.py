import os
import json
import streamlit as st
from groq import Groq
import random
import re
import demjson3

# App configuration
st.set_page_config(page_title="Space Pe Charcha", page_icon="🚀", layout="wide")

# Read the API key from Streamlit secrets
try:
    groq_api_key = st.secrets["GROQ_API_KEY"]

    if not groq_api_key:
        st.error("GROQ_API_KEY not found in Streamlit secrets. Please make sure it's correctly set in the app settings.")
        st.stop()

except Exception as e:
    st.error(f"Error accessing GROQ_API_KEY: {str(e)}")
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

def clean_json_string(json_string):
    json_string = json_string.strip()
    json_string = re.sub(r'^```json\s*|\s*```$', '', json_string, flags=re.MULTILINE)
    json_string = re.sub(r"(?<!\w)'|'(?!\w)", '"', json_string)
    json_string = ''.join(char for char in json_string if ord(char) >= 32)
    return json_string

def generate_question(difficulty):
    topics = [
        "planets", "stars", "galaxies", "space exploration", "astronauts",
        "space technology", "comets and asteroids", "black holes",
        "space agencies", "space missions"
    ]
    available_topics = [t for t in topics if t not in st.session_state.quiz_state["topics_used"]]
    
    if not available_topics:
        st.session_state.quiz_state["topics_used"].clear()
        available_topics = topics
    
    topic = random.choice(available_topics)
    st.session_state.quiz_state["topics_used"].add(topic)

    prompt = f"""Generate a {difficulty}-level multiple-choice question about {topic} in space science. 
    The question should have 4 options.
    Format the response as a JSON object with the following structure:
    {{
        "question": "The question text",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": "The correct option",
        "explanation": "A brief explanation of the correct answer",
        "resource": "A relevant URL for further reading (preferably Wikipedia or a reputable space science website)"
    }}
    Ensure the question is suitable for a general audience interested in space.
    Provide ONLY the JSON object in your response, with no additional text.
    """

    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            response = client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates space-related quiz questions."},
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.choices[0].message.content
            question_data = demjson3.decode(content)
            
            required_keys = ["question", "options", "correct_answer", "explanation", "resource"]
            if all(key in question_data for key in required_keys) and len(question_data["options"]) == 4:
                return question_data
            else:
                raise ValueError("Invalid question structure")
        
        except demjson3.JSONDecodeError as e:
            st.error(f"Failed to parse JSON (Attempt {attempt + 1}/{max_attempts}): {str(e)}")
            st.error(f"Raw content: {content}")
        except Exception as e:
            st.error(f"Error generating question (Attempt {attempt + 1}/{max_attempts}): {str(e)}")
        
        if attempt == max_attempts - 1:
            st.error(f"Failed to generate a valid question after {max_attempts} attempts.")
            return None

    return None

def run_quiz():
    st.title("🚀 Space Quiz")
    
    if not st.session_state.quiz_state["started"]:
        st.write("Welcome to the Space Quiz! Choose your difficulty level:")
        difficulty = st.radio("Select difficulty:", ["Easy", "Medium", "Hard"])
        if st.button("Start Quiz"):
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
            st.write(f"Question {st.session_state.quiz_state['current_question'] + 1}:")
            st.write(question["question"])
            answer = st.radio("Choose your answer:", question["options"], key=f"q{st.session_state.quiz_state['current_question']}")
            
            if st.button("Submit"):
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
    st.write(f"Quiz completed! Your score: {st.session_state.quiz_state['score']} out of 10")
    
    if st.session_state.quiz_state["wrong_answers"]:
        st.write("Here are the questions you got wrong, along with explanations and resources to learn more:")
        for question in st.session_state.quiz_state["wrong_answers"]:
            st.write(f"- {question['question']}")
            st.write(f"  Correct answer: {question['correct_answer']}")
            st.write(f"  Explanation: {question['explanation']}")
            st.write(f"  Learn more: {question['resource']}")
    
    update_leaderboard(st.session_state.quiz_state['score'])
    display_leaderboard()
    
    if st.button("Start New Quiz"):
        st.session_state.quiz_state["started"] = False
        st.rerun()

def run_chat():
    st.title("🚀 Space Pe Charcha")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask me about space..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful assistant specializing in space and astronomy."},
                {"role": "user", "content": prompt}
            ]
        )
        
        with st.chat_message("assistant"):
            st.markdown(response.choices[0].message.content)
        st.session_state.messages.append({"role": "assistant", "content": response.choices[0].message.content})

def run_did_you_know():
    st.title("🌠 Cosmic Facts Explorer")
    
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

    if st.button("🚀 Explore New Fact"):
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

    if st.session_state.did_you_know_state["fact_history"]:
        st.write("### 📚 Your Cosmic Fact Journey")
        for i, fact in enumerate(reversed(st.session_state.did_you_know_state["fact_history"]), 1):
            st.info(f"Fact #{i}: {fact}")

    st.write("### 🌟 Share Your Cosmic Knowledge")
    user_fact = st.text_area("Do you know a fascinating space fact? Share it with us!")
    if st.button("Submit Fact"):
        if user_fact:
            st.success("Thank you for sharing your cosmic wisdom! Our team of astronomers will review it.")
        else:
            st.warning("Please enter a fact before submitting.")

    st.write("### 🔭 Space Trivia Corner")
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
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Start Chatting 💬"):
            st.session_state.page = "Chat"
            st.rerun()
    with col2:
        if st.button("Take a Quiz 📝"):
            st.session_state.page = "Quiz"
            st.rerun()
    with col3:
        if st.button("Explore Facts 🌠"):
            st.session_state.page = "Did You Know"
            st.rerun()
    
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

if "leaderboard" not in st.session_state:
    st.session_state.leaderboard = []

def update_leaderboard(score):
    name = st.text_input("Enter your name for the leaderboard:")
    if name:
        st.session_state.leaderboard.append((name, score))
        st.session_state.leaderboard.sort(key=lambda x: x[1], reverse=True)
        st.session_state.leaderboard = st.session_state.leaderboard[:10]  # Keep top 10

def display_leaderboard():
    st.write("### 🏆 Leaderboard")
    for i, (name, score) in enumerate(st.session_state.leaderboard, 1):
        st.write(f"{i}. {name}: {score}")

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
    if st.button("Home 🏠"):
        st.session_state.page = "Welcome"
        st.rerun()
    if st.button("Chat 💬"):
        st.session_state.page = "Chat"
        st.rerun()
    if st.button("Quiz 📝"):
        st.session_state.page = "Quiz"
        st.rerun()
    if st.button("Did You Know? 🌠"):
        st.session_state.page = "Did You Know"
        st.rerun()
