import nltk
import string
import re
import requests
from bs4 import BeautifulSoup
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import os
import json
import random

nltk.download('punkt', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('stopwords', quiet=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def fetch_google_summary(query, num_results=5, max_answers=5):
    from googlesearch import search
    urls = list(search(query, num_results=num_results))
    summaries = []
    seen = set()
    for url in urls:
        try:
            res = requests.get(url, headers=HEADERS, timeout=5)
            soup = BeautifulSoup(res.content, 'html.parser')
            for p in soup.find_all('p'):
                text = p.get_text().strip()
                if len(text) > 60 and text not in seen:
                    seen.add(text)
                    summaries.append(text)
                    if len(summaries) >= max_answers:
                        break
        except:
            continue
    return summaries or ["I couldn't find much on that. Want to rephrase or try a new angle?"]

class StoryBot:
    def __init__(self):
        self.memory_file = "conversation_memory.json"
        self.session_history = []
        self._load_history()

    def _save_to_file(self):
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.session_history, f, indent=4, ensure_ascii=False)

    def _load_history(self):
        if os.path.exists(self.memory_file):
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                self.session_history = json.load(f)

    def add_to_history(self, question, answer):
        self.session_history.append({'question': question, 'answer': answer})
        self._save_to_file()

    def get_context(self):
        # Pull last 2 answers for background (invisible to user)
        return ' '.join(entry['answer'] for entry in self.session_history[-2:])

    def suggest_followups(self, last_question):
        suggestions_map = {
            "ai": [
                "What are ethical concerns with AI?",
                "Can AI develop emotions?",
                "How is AI trained?"
            ],
            "health": [
                "How does AI help in mental health?",
                "Can AI detect diseases early?",
                "Is AI used in surgery?"
            ],
            "film": [
                "Are any films written by AI?",
                "How is AI used in animation?",
                "Can AI review movies?"
            ],
            "education": [
                "How does AI personalize learning?",
                "Can AI replace teachers?",
                "Is AI helpful in online learning?"
            ]
        }

        keywords = list(suggestions_map.keys())
        for key in keywords:
            if key in last_question.lower():
                return random.sample(suggestions_map[key], 3)

        # fallback
        return random.sample([
            "Want to dive into real-life use cases?",
            "Curious about how this affects daily life?",
            "Want to know its impact on the future?",
            "What industries are using this the most?",
            "Should we be worried about it?"
        ], 3)

    def generate_human_response(self, question, answer, context):
        intro_phrases = [
            "Great question!",
            "Interesting thought!",
            "Here's something you might find useful.",
            "Let's unpack that a bit."
        ]

        transition_phrases = [
            "Building on what we talked about earlier,",
            "Continuing our story,",
            "Just like we saw earlier,",
            "To add another piece to the puzzle,"
        ]

        use_context = bool(context.strip())

        intro = random.choice(intro_phrases)
        transition = random.choice(transition_phrases)

        if use_context:
            return f"{intro} {transition} {answer}"
        else:
            return f"{intro} {answer}"

    def get_response(self, question):
        summaries = fetch_google_summary(question)
        picked_answer = random.choice(summaries)
        context = self.get_context()
        human_answer = self.generate_human_response(question, picked_answer, context)
        self.add_to_history(question, picked_answer)

        followups = self.suggest_followups(question)
        suggestions_text = "\n💬 You could also ask:\n" + '\n'.join(f"👉 {q}" for q in followups)

        return f"{human_answer}\n{suggestions_text}"

    def chat(self):
        print("🤖 StoryBot (Enhanced): Let’s build a smart story-like conversation!")
        print("Type 'exit' or 'quit' to stop.")
        while True:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ['exit', 'quit']:
                print("StoryBot: Thanks for the chat! Come back to continue the story. 👋")
                break
            reply = self.get_response(user_input)
            print(f"\nStoryBot: {reply}")

if __name__ == "__main__":
    bot = StoryBot()
    bot.chat()
