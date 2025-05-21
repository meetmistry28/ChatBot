import nltk
import string
import re
import requests
from bs4 import BeautifulSoup
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Download required NLTK resources
for res in ['punkt', 'wordnet', 'stopwords']:
    nltk.download(res, quiet=True)

CONFIG = {
    'NUM_RESULTS': 1000,
    'MAX_PARAS_PER_SITE': 2,
    'MIN_TEXT_LENGTH': 70,
    'ALPHA_RATIO': 0.7,
    'REQUEST_TIMEOUT': 5,
    'HEADERS': {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/91.0.4472.124 Safari/537.36")
    }
}

SKIP_RESPONSES = {
    "[Info] No relevant content found on this page.",
    "[Info] Failed to fetch or parse the page.",
}

SKIP_PATTERNS = [
    r"our editors will review", r"click here", r"learn more", r"sign up", r"subscribe",
    r"this page is not available", r"this article is a stub", r"read more", r"cookies?",
    r"submit your feedback", r"thank you for your submission", r"privacy.*terms",
    r"read this article on", r"breaking news", r"advertisement"
]

def clean_text(text):
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return ""
    return text

def clean_answer_text(text):
    text = re.sub(r'\[[^\]]*\]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_meaningful_text(text, query_keywords):
    if not text or len(text) < CONFIG['MIN_TEXT_LENGTH']:
        return False
    if not any(word in text.lower() for word in query_keywords):
        return False
    alpha_ratio = sum(c.isalpha() for c in text) / max(len(text), 1)
    return alpha_ratio > CONFIG['ALPHA_RATIO']

def is_definition_like(text, query):
    query = query.lower().strip().rstrip('?')
    terms = [query]
    if query.startswith('what is ') or query.startswith('who is '):
        terms.append(re.sub(r'^(what|who) is ', '', query))
    for term in terms:
        if re.match(rf"{re.escape(term)}\s+(is|was|are|refers to|means)\b", text.lower()):
            return True
    return False

def extract_relevant_paragraphs(soup, query, max_paras=CONFIG['MAX_PARAS_PER_SITE']):
    query_keywords = set(query.lower().split())
    paragraphs = []
    for para in soup.find_all('p'):
        raw_text = para.get_text(separator=' ', strip=True)
        raw_text = clean_text(raw_text)
        if not raw_text:
            continue
        if is_definition_like(raw_text, query) or is_meaningful_text(raw_text, query_keywords):
            cleaned = clean_answer_text(raw_text)
            if cleaned not in SKIP_RESPONSES and len(cleaned.split()) >= 10:
                paragraphs.append(cleaned)
        if len(paragraphs) >= max_paras:
            break
    return paragraphs

def fetch_with_requests(url):
    try:
        response = requests.get(url, headers=CONFIG['HEADERS'], timeout=CONFIG['REQUEST_TIMEOUT'])
        return BeautifulSoup(response.content, 'html.parser')
    except Exception:
        return None

def fetch_with_selenium(url):
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        html = driver.page_source
        driver.quit()
        return BeautifulSoup(html, 'html.parser')
    except Exception:
        return None

def extract_answer_from_url(url, query):
    soup = fetch_with_requests(url)
    answers = extract_relevant_paragraphs(soup, query) if soup else []

    if not answers:  # Fall back to Selenium
        soup = fetch_with_selenium(url)
        answers = extract_relevant_paragraphs(soup, query) if soup else []

    return answers if answers else ["[Info] No relevant content found on this page."]

def search_google_urls(query, num_results=CONFIG['NUM_RESULTS']):
    try:
        from googlesearch import search
    except ImportError:
        return []
    try:
        return list(search(query, num_results=num_results))
    except Exception:
        return []

class DocChatBot:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.query_data = {}

    def get_next_answer(self, query):
        query = query.strip().lower()
        if query not in self.query_data:
            urls = search_google_urls(query)
            if not urls:
                return "[Error] Could not fetch search results. Check internet or install googlesearch-python."
            self.query_data[query] = {
                'urls': urls,
                'answers_per_url': {},
                'url_index': 0,
                'answer_index': 0,
            }

        data = self.query_data[query]
        urls = data['urls']
        total_attempts = 0
        max_attempts = len(urls) * 3

        while total_attempts < max_attempts:
            current_url = urls[data['url_index']]
            if current_url not in data['answers_per_url']:
                answers = extract_answer_from_url(current_url, query)
                data['answers_per_url'][current_url] = answers

            answers = data['answers_per_url'][current_url]
            while data['answer_index'] < len(answers):
                answer = answers[data['answer_index']]
                data['answer_index'] += 1
                total_attempts += 1
                if answer not in SKIP_RESPONSES:
                    return answer

            data['url_index'] = (data['url_index'] + 1) % len(urls)
            data['answer_index'] = 0

        return "[Info] No accurate and relevant content found. Try rephrasing your question."

    def chat(self):
        print("Welcome to the Smart ChatBot!")
        print("Type 'exit' or 'quit' to stop.")
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ['exit', 'quit']:
                print("AI Bot: Goodbye!")
                break
            response = self.get_next_answer(user_input)
            print(f"AI Bot: {response}")

if __name__ == "__main__":
    chatbot = DocChatBot()
    chatbot.chat()
