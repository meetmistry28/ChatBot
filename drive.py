import nltk
import string
import re
import requests
from bs4 import BeautifulSoup
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords

for res in ['punkt', 'wordnet', 'stopwords']:
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
        r"(?i)cookie[s]?",
        r"(?i)advertisement",
        r"(?i)accept.*cookie",
        r"(?i)sign up",
        r"(?i)buy now",
        r"(?i)learn more",
        r"\bterms\b.*\bprivacy\b",
        r"(?i)read.*more.*on.*app",
        r"(?i)breaking news.*",
        r"(?i)latest updates.*",
        r"(?i)catch all the.*",
        r"(?i)choose your reason.*",
        r"(?i)settingssearch settings.*",
        r"(?i)english edition.*",
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
    raw_keywords = set(query.lower().split())

    for url in urls:
        try:
            response = requests.get(url, headers=HEADERS, timeout=5)
            soup = BeautifulSoup(response.content, 'html.parser')

            paragraphs = soup.find_all('p')

            for p in paragraphs:
                raw_text = p.get_text().strip()
                raw_text = clean_text(raw_text)
                if raw_text and raw_text not in seen_texts and is_meaningful_text(raw_text, raw_keywords):
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

class DocChatBot:
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
        return [self.lemmatizer.lemmatize(t) for t in tokens if t not in string.punctuation and t not in self.stop_words]

    def _scrape_web_data(self, query):
        return fetch_google_summary(query, num_results=10, max_answers=10)

    def get_response(self, query):
        query = query.strip()
        if not query:
            return "(Error) Please enter a valid question."

        if query not in self.web_memory:
            self.web_memory[query] = self._scrape_web_data(query)

        answers = self.web_memory[query]
        idx = self.query_memory.get(query, 0) % len(answers)
        self.query_memory[query] = idx + 1

        return f"(From Web) {answers[idx]}"

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

if __name__ == "__main__":
    chatbot = DocChatBot()
    chatbot.chat()