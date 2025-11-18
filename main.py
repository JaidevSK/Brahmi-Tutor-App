from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sqlite3
from typing import List, Optional
import random
from datetime import datetime
import json
import subprocess
import markdown

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

DB_FILE = "progress.db"

# ---- Data Definitions ----

brahmi_letters = [
    {"brahmi": "𑀅", "devanagari": "अ", "sound": "a"},
    {"brahmi": "𑀆", "devanagari": "आ", "sound": "ā"},
    {"brahmi": "𑀇", "devanagari": "इ", "sound": "i"},
    {"brahmi": "𑀈", "devanagari": "ई", "sound": "ī"},
    {"brahmi": "𑀉", "devanagari": "उ", "sound": "u"},
    {"brahmi": "𑀊", "devanagari": "ऊ", "sound": "ū"},
    {"brahmi": "𑀋", "devanagari": "ऋ", "sound": "ṛ"},
    {"brahmi": "𑀏", "devanagari": "ए", "sound": "e"},
    {"brahmi": "𑀑", "devanagari": "ऐ", "sound": "ai"},
    {"brahmi": "𑀒", "devanagari": "ओ", "sound": "o"},
    {"brahmi": "𑀔", "devanagari": "औ", "sound": "au"},
    {"brahmi": "𑀓", "devanagari": "क", "sound": "ka"},
    {"brahmi": "𑀔", "devanagari": "ख", "sound": "kha"},
    {"brahmi": "𑀕", "devanagari": "ग", "sound": "ga"},
    {"brahmi": "𑀖", "devanagari": "घ", "sound": "gha"},
    {"brahmi": "𑀗", "devanagari": "ङ", "sound": "ṅa"},
    {"brahmi": "𑀘", "devanagari": "च", "sound": "ca"},
    {"brahmi": "𑀙", "devanagari": "छ", "sound": "cha"},
    {"brahmi": "𑀚", "devanagari": "ज", "sound": "ja"},
    {"brahmi": "𑀛", "devanagari": "झ", "sound": "jha"},
    {"brahmi": "𑀜", "devanagari": "ञ", "sound": "ña"},
    {"brahmi": "𑀝", "devanagari": "ट", "sound": "ṭa"},
    {"brahmi": "𑀞", "devanagari": "ठ", "sound": "ṭha"},
    {"brahmi": "𑀟", "devanagari": "ड", "sound": "ḍa"},
    {"brahmi": "𑀠", "devanagari": "ढ", "sound": "ḍha"},
    {"brahmi": "𑀡", "devanagari": "ण", "sound": "ṇa"},
    {"brahmi": "𑀢", "devanagari": "त", "sound": "ta"},
    {"brahmi": "𑀣", "devanagari": "थ", "sound": "tha"},
    {"brahmi": "𑀤", "devanagari": "द", "sound": "da"},
    {"brahmi": "𑀥", "devanagari": "ध", "sound": "dha"},
    {"brahmi": "𑀦", "devanagari": "न", "sound": "na"},
    {"brahmi": "𑀧", "devanagari": "प", "sound": "pa"},
    {"brahmi": "𑀨", "devanagari": "फ", "sound": "pha"},
    {"brahmi": "𑀩", "devanagari": "ब", "sound": "ba"},
    {"brahmi": "𑀪", "devanagari": "भ", "sound": "bha"},
    {"brahmi": "𑀫", "devanagari": "म", "sound": "ma"},
    {"brahmi": "𑀬", "devanagari": "य", "sound": "ya"},
    {"brahmi": "𑀭", "devanagari": "र", "sound": "ra"},
    {"brahmi": "𑀮", "devanagari": "ल", "sound": "la"},
    {"brahmi": "𑀯", "devanagari": "व", "sound": "va"},
    {"brahmi": "𑀰", "devanagari": "श", "sound": "śa"},
    {"brahmi": "𑀱", "devanagari": "ष", "sound": "ṣa"},
    {"brahmi": "𑀲", "devanagari": "स", "sound": "sa"},
    {"brahmi": "𑀳", "devanagari": "ह", "sound": "ha"},
    {"brahmi": "𑀴", "devanagari": "ळ", "sound": "ḷa"},
]

vocab_deva_brahmi = {
    "सेब": "𑀲𑁂𑀩",
    "आम": "𑀆𑀫",
    "केला": "𑀓𑁂𑀮𑀅",
    "आलू": "𑀆𑀮𑁂𑀉",
    "मटर": "𑀫𑀢𑀭",
    "दिल्ली": "𑀤𑀺𑀮𑀺",
    "मुम्बई": "𑀫𑀼𑀫𑁆𑀩𑀈",
    "कोलकाता": "𑀓𑁂𑀮𑀓𑀢",
    "चेन्नई": "𑀘𑁂𑀦𑀦𑀈",
    "गर्मी": "𑀕𑀭𑁆𑀫𑀺",
    "सर्दी": "𑀲𑀭𑁆𑀤𑀺",
    "बसंत": "𑀩𑀲𑀦𑀢",
    "पतझड़": "𑀧𑀢𑁆𑀚𑀡𑀽",
    "गुलाब": "𑀕𑀼𑀮𑀅𑀩",
    "कमल": "𑀓𑀫𑀮",
    "नीम": "𑀦𑀺𑀫",
    "बरगद": "𑀩𑀭𑀕𑀤",
    "रोटी": "𑀭𑁂𑀢𑀺",
    "चावल": "𑀘𑀯𑀮"
}

vocab_categories = {
    "fruits": ["सेब", "आम", "केला"],
    "vegetables": ["आलू", "मटर"],
    "cities": ["दिल्ली", "मुम्बई", "कोलकाता", "चेन्नई"],
    "seasons": ["गर्मी", "सर्दी", "बसंत", "पतझड़"],
    "flowers": ["गुलाब", "कमल"],
    "trees": ["नीम", "बरगद"],
    "food": ["रोटी", "चावल"]
}

# ---- Database Setup ----
def get_db():
    conn = sqlite3.connect(DB_FILE)
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_type TEXT,
            score INTEGER,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def store_score(quiz_type: str, score: int):
    conn = get_db()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO results (quiz_type, score, timestamp) VALUES (?, ?, ?)",
                   (quiz_type, score, timestamp))
    conn.commit()
    conn.close()

def get_latest_scores():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT quiz_type, MAX(timestamp), score FROM results GROUP BY quiz_type
    """)
    results = cursor.fetchall()
    conn.close()
    return results

# ---- Quiz Helper Functions ----

def generate_quiz(quiz_number):
    if quiz_number == 1:
        questions = random.sample(brahmi_letters, 10)
        quiz_type = "Brahmi to Devanagari"
        quiz_questions = [{
            "question": q["brahmi"],
            "options": [o["devanagari"] for o in random.sample(brahmi_letters, 4)],
            "answer": q["devanagari"]
        } for q in questions]
        for q in quiz_questions:
            if q["answer"] not in q["options"]:
                q["options"][random.randint(0, 3)] = q["answer"]
        return quiz_questions, quiz_type

    elif quiz_number == 2:
        questions = random.sample(brahmi_letters, 10)
        quiz_type = "Sound to Brahmi"
        quiz_questions = [{
            "question": q["sound"],
            "options": [o["brahmi"] for o in random.sample(brahmi_letters, 4)],
            "answer": q["brahmi"]
        } for q in questions]
        for q in quiz_questions:
            if q["answer"] not in q["options"]:
                q["options"][random.randint(0, 3)] = q["answer"]
        return quiz_questions, quiz_type

    else:
        all_words = sum(vocab_categories.values(), [])
        selected_words = random.sample(all_words, 10)
        quiz_type = "Devanagari Vocabulary to Brahmi"
        quiz_questions = []
        for w in selected_words:
            correct = vocab_deva_brahmi.get(w, "𑀅𑀅𑀅")
            options = random.sample(list(vocab_deva_brahmi.values()), 4)
            if correct not in options:
                options[random.randint(0, 3)] = correct
            quiz_questions.append({
                "question": w,
                "options": options,
                "answer": correct
            })
        return quiz_questions, quiz_type

# ---- Routes ----

@app.on_event("startup")
def startup():
    init_db()

@app.get("/", response_class="text/html")
def root():
    return RedirectResponse(url="/welcome")

@app.get("/welcome")
def welcome(request: Request):
    return templates.TemplateResponse("welcome.html", {"request": request, "brahmi_letters": brahmi_letters})

@app.get("/lesson")
def lesson(request: Request):
    return templates.TemplateResponse("lesson.html", {"request": request, "brahmi_letters": brahmi_letters})

@app.get("/progress")
def progress(request: Request):
    results = get_latest_scores()
    return templates.TemplateResponse("progress.html", {"request": request, "results": results})

@app.get("/quiz/{quiz_number}")
def quiz_start(request: Request, quiz_number: int):
    # Show quiz start page
    return templates.TemplateResponse("quiz_start.html", {"request": request, "quiz_number": quiz_number})

@app.post("/quiz/{quiz_number}/start")
def quiz_start_post(quiz_number: int):
    quiz_questions, quiz_type = generate_quiz(quiz_number)
    # Store questions and type in a simple session store or server-side storage
    # For simplicity, store in memory (not persistent between server restarts)
    app.state.quiz_questions = quiz_questions
    app.state.quiz_answers = [None] * len(quiz_questions)
    app.state.quiz_index = 0
    app.state.quiz_type = quiz_type
    app.state.quiz_number = quiz_number
    return RedirectResponse(url=f"/quiz/{quiz_number}/question/0", status_code=303)

@app.get("/quiz/{quiz_number}/question/{q_index}")
def quiz_question(request: Request, quiz_number: int, q_index: int):
    if not hasattr(app.state, "quiz_questions"):
        return RedirectResponse(url=f"/quiz/{quiz_number}", status_code=303)  # Restart quiz if no data

    questions = app.state.quiz_questions
    answers = app.state.quiz_answers
    if q_index < 0 or q_index >= len(questions):
        return RedirectResponse(url=f"/quiz/{quiz_number}/question/0", status_code=303)

    question = questions[q_index]
    selected = answers[q_index]
    return templates.TemplateResponse("quiz_question.html", {
        "request": request,
        "quiz_type": app.state.quiz_type,
        "quiz_number": quiz_number,
        "q_index": q_index,
        "q_count": len(questions),
        "question": question,
        "selected": selected
    })

@app.post("/quiz/{quiz_number}/question/{q_index}")
def quiz_question_post(quiz_number: int, q_index: int, answer: str = Form(...), action: str = Form(...)):
    app.state.quiz_answers[q_index] = answer
    if action == "next":
        q_next = q_index + 1
    elif action == "prev":
        q_next = q_index - 1
    else:
        q_next = q_index
    # If submit pressed, redirect to result
    if action == "submit":
        total = 0
        for ans, q in zip(app.state.quiz_answers, app.state.quiz_questions):
            if ans == q["answer"]:
                total += 1
        store_score(app.state.quiz_type, total)
        app.state.quiz_score = total
        return RedirectResponse(url=f"/quiz/{quiz_number}/result", status_code=303)
    else:
        if q_next < 0:
            q_next = 0
        elif q_next >= len(app.state.quiz_questions):
            q_next = len(app.state.quiz_questions) - 1
        return RedirectResponse(url=f"/quiz/{quiz_number}/question/{q_next}", status_code=303)

@app.get("/quiz/{quiz_number}/result")
def quiz_result(request: Request, quiz_number: int):
    score = getattr(app.state, "quiz_score", None)
    questions = getattr(app.state, "quiz_questions", [])
    answers = getattr(app.state, "quiz_answers", [])
    if score is None:
        return RedirectResponse(url=f"/quiz/{quiz_number}", status_code=303)

    # Create a list of dicts combining question and corresponding answer
    qa_pairs = []
    for q, a in zip(questions, answers):
        qa_pairs.append({"question": q["question"], "answer": q["answer"], "user_answer": a})

    return templates.TemplateResponse("quiz_result.html", {
        "request": request,
        "quiz_number": quiz_number,
        "score": score,
        "total": len(questions),
        "qa_pairs": qa_pairs,
    })


# Load sitemap JSON (You can also load from file if preferred)
sitemap_json = {
  "pages": [
    {"name": "Lesson", "link": "/lesson", "description": "Displays all Brahmi characters with their Devanagari counterparts and pronunciations to learn the script basics."},
    {"name": "Quiz 1", "link": "/quiz/1", "description": "Quiz converting displayed Brahmi characters to their correct Devanagari forms with multiple-choice options."},
    {"name": "Quiz 2", "link": "/quiz/2", "description": "Quiz converting phonetic sounds to Brahmi characters with multiple-choice options."},
    {"name": "Quiz 3", "link": "/quiz/3", "description": "Quiz matching Devanagari vocabulary words from categories like fruits, vegetables, and cities to their Brahmi script forms."},
    {"name": "Progress", "link": "/progress", "description": "Dashboard displaying the user's latest quiz scores and progress over time."},
    {"name": "LLM Helper", "link": "/llm_helper", "description": "Interactive AI assistant powered by Ollama gemma3:270m model which provides guided help, Brahmi history, and detailed script information referencing Wikipedia."}
  ]
}

def call_ollama_with_context(prompt: str, context_json: dict) -> str:
    """Call Ollama 'gemma3:270m' LLM with prompt and JSON context as input."""
    context_str = json.dumps(context_json)
    # full_prompt = f"Here is the site sitemap and page descriptions as JSON:\n{context_str}\nUser query: {prompt}\nAnswer in detail referencing Brahmi history and pages."
    full_prompt = f"{prompt}"
    
    result = subprocess.run(
        ["ollama", "run", "gemma3:270m", '"', full_prompt, '"'],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        return result.stdout.strip()
    else:
        return f"Error calling Ollama: {result.stderr}"

# Route to display the LLM Helper page and process queries
@app.get("/llm_helper")
def llm_helper_get(request: Request):
    return templates.TemplateResponse("llm_helper.html", {"request": request, "response": None})

@app.post("/llm_helper")
def llm_helper_post(request: Request, query: str = Form(...)):
    answer = call_ollama_with_context(query, sitemap_json)
    html_response = markdown.markdown(answer, extensions=['fenced_code', 'tables'])
    return templates.TemplateResponse("llm_helper.html", {"request": request, "response": html_response, "query": query})

@app.get("/brahmi_converter")
def brahmi_converter(request: Request):
    return templates.TemplateResponse("brahmi_converter.html", {"request": request})


