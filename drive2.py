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

for res in ['punkt', 'wordnet', 'stopwords', 'averaged_perceptron_tagger', 'maxent_ne_chunker', 'words']:       
    nltk.download(res, quiet=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/91.0.4472.124 Safari/537.36"
}

def clean_text(text):
    patterns_to_remove = [
        r"(?i)new customers get.*free credits",
        r"(?i)subscribe.*newsletter",
        r"(?i)cookie[s]?", r"(?i)advertisement",
        r"(?i)accept.*cookie", r"(?i)sign up",
        r"(?i)buy now", r"(?i)learn more",
        r"\bterms\b.*\bprivacy\b", r"(?i)read.*more.*on.*app",
        r"(?i)breaking news.*", r"(?i)latest updates.*",
        r"(?i)catch all the.*", r"(?i)choose your reason.*",
        r"(?i)settingssearch settings.*", r"(?i)english edition.*", 
    ]
    for pattern in patterns_to_remove:
        if re.search(pattern, text):
            return ""
    return text

def clean_answer_text(text):
    text = re.sub(r'\[[^\]]*\]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_meaningful_text(text, query_keywords):
    if not text or len(text) < 60:
        return False
    if not any(word in text.lower() for word in query_keywords):
        return False
    alpha_ratio = sum(c.isalpha() for c in text) / max(len(text), 1)
    return alpha_ratio > 0.6

def fetch_google_summary(query, num_results=5, max_answers=5):
    try:
        from googlesearch import search
    except ImportError:
        return ["[Error] Install googlesearch-python: pip install googlesearch-python"]

    try:
        urls = list(search(query, num_results=num_results))
    except Exception as e:
        return [f"[Error] Google search failed: {e}"]

    summaries = []
    seen_texts = set()
    query_keywords = set(query.lower().split())

    for url in urls:
        try:
            response = requests.get(url, headers=HEADERS, timeout=5)
            soup = BeautifulSoup(response.content, 'html.parser')
            paragraphs = soup.find_all('p')

            for p in paragraphs:
                raw_text = p.get_text().strip()
                raw_text = clean_text(raw_text)
                if raw_text and raw_text not in seen_texts and is_meaningful_text(raw_text, query_keywords):
                    cleaned = clean_answer_text(raw_text)
                    if cleaned not in seen_texts:
                        seen_texts.add(cleaned)
                        summaries.append(cleaned)
                        if len(summaries) >= max_answers:
                            break
        except Exception:
            continue
        if len(summaries) >= max_answers:
            break

    return summaries if summaries else ["[Info] No accurate and relevant content found. Try rephrasing your question."]

class BaseChatBot:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.query_memory = {}
        self.web_memory = {}

    def _normalize_abbreviations(self, text):
        text = text.lower()
        text = re.sub(r'\bsupport vector machine\b', 'svm', text)
        text = re.sub(r'\bartificial intelligence\b', 'ai', text)
        return text

    def _preprocess_text(self, text):
        text = self._normalize_abbreviations(text)
        tokens = nltk.word_tokenize(text)
        return ' '.join(self.lemmatizer.lemmatize(t) for t in tokens if t not in string.punctuation and t not in self.stop_words)

    def _scrape_web_data(self, query):
        return fetch_google_summary(query, num_results=10, max_answers=10)

class DocChatBot(BaseChatBot):
    def __init__(self):
        super().__init__()
        self.known_topics = [
            "artificial intelligence", "ai", "svm", "support vector machine",
            "machine learning", "ml", "deep learning", "dl", "nlp",
            "neural network", "chatbot", "language model"
        ]

    def get_response(self, query):
        filename = self.get_topic_filename(query)
        existing_data = []

        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = []

        question_data = None
        for entry in existing_data:
            if entry["question"].strip().lower() == query.strip().lower():
                question_data = entry
                break

        if question_data:
            if len(question_data["answer"]) < 10:
                new_answers = self._scrape_web_data(query)
                for ans in new_answers:
                    cleaned = clean_answer_text(ans)
                    if cleaned not in question_data["answer"]:
                        question_data["answer"].append(cleaned)
                        self.save_qa_to_file(query, cleaned, filename)
                        return cleaned
            return random.choice(question_data["answer"])

        if query not in self.web_memory:
            self.web_memory[query] = self._scrape_web_data(query)

        answers = self.web_memory[query]
        if not answers:
            return "I'm sorry, I couldn't find anything right now."

        answer = random.choice(answers)
        self.save_qa_to_file(query, answer, filename)
        return answer

    def _normalize_abbreviations(self, text):
        text = text.lower()
        text = re.sub(r'\bsupport vector machine\b', 'svm', text)
        text = re.sub(r'\bartificial intelligence\b', 'ai', text)
        return text

    def _preprocess_text(self, text):
        text = self._normalize_abbreviations(text)
        tokens = nltk.word_tokenize(text)
        return ' '.join(self.lemmatizer.lemmatize(t) for t in tokens if t not in string.punctuation and t not in self.stop_words)

    def _scrape_web_data(self, query):
        return fetch_google_summary(query, num_results=10, max_answers=10)

    def detect_topic(self, query):
        query = query.lower()
        for topic in self.known_topics:
            if topic in query:
                return re.sub(r'\s+', '_', topic)  # "deep learning" → "deep_learning"
        return "misc"

    def get_topic_filename(self, query):
        topic = self.detect_topic(query)
        folder = "topics"
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, f"{topic}.json")
    
    def chat(self):
        print("Welcome to the ChatBot with Google Web Fallback!")
        print("Type 'exit' or 'quit' to stop.")
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ['exit', 'quit']:
                print("AI Bot: Goodbye!")
                break
            response = self.get_response(user_input)
            print(f"AI Bot: {response}")

    def save_qa_to_file(self, question, answer, filename):
        data = []
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []

        question_found = False
        for entry in data:
            if entry["question"].strip().lower() == question.strip().lower():
                question_found = True
                if isinstance(entry["answer"], list):
                    if answer not in entry["answer"]:
                        entry["answer"].append(answer)
                else:
                    if answer != entry["answer"]:
                        entry["answer"] = [entry["answer"], answer]
                break

        if not question_found:
            data.append({
                "question": question,
                "answer": [answer]
            })

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    chatbot = DocChatBot()
    chatbot.chat()