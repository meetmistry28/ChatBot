import nltk
import string
import re
import requests
from bs4 import BeautifulSoup
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords

# Download required NLTK resources
for res in ['punkt', 'wordnet', 'stopwords']:
    nltk.download(res, quiet=True)

CONFIG = {
    'NUM_RESULTS': 100,
    'MAX_PARAS_PER_SITE': 2,
    'MIN_TEXT_LENGTH': 80,
    'ALPHA_RATIO': 0.8,
    'REQUEST_TIMEOUT': 5,
    'HEADERS': {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/91.0.4472.124 Safari/537.36")
    }
}

def clean_text(text):
    """Remove irrelevant web UI content."""
    patterns = [
        r"(?i)new customers get.*free credits",
        r"(?i)subscribe.*newsletter",
        r"(?i)cookie[s]?",
        r"(?i)advertisement",
        r"(?i)accept.*cookie",
        r"(?i)sign up",
        r"(?i)buy now",
        r"(?i)learn more",
        r"\bterms\b.*\bprivacy\b",
        r"(?i)breaking news.*",
        r"(?i)choose your reason.*",
        r"(?i)read.*more.*on.*app"
    ]
    for pattern in patterns:
        if re.search(pattern, text):
            return ""
    return text

def clean_answer_text(text):
    """Remove citations and normalize whitespace."""
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
    if query.startswith('what is '):
        terms.append(query.replace('what is ', '').strip())
    for term in terms:
        if re.match(rf"{re.escape(term)}\s+(is|refers to|means|are)\b", text.lower()):
            return True
    return False

def extract_relevant_paragraphs(soup, query, max_paras=CONFIG['MAX_PARAS_PER_SITE']):
    """Extract meaningful paragraphs prioritizing definitions."""
    query_keywords = set(query.lower().split())
    paragraphs = []
    for para in soup.find_all('p'):
        raw_text = para.get_text(separator=' ', strip=True)
        raw_text = clean_text(raw_text)
        if not raw_text:
            continue
        if is_definition_like(raw_text, query) or is_meaningful_text(raw_text, query_keywords):
            cleaned = clean_answer_text(raw_text)
            paragraphs.append(cleaned)
        if len(paragraphs) >= max_paras:
            break
    return paragraphs

def search_google_urls(query, num_results=CONFIG['NUM_RESULTS']):
    try:
        from googlesearch import search
    except ImportError:
        return []
    try:
        urls = list(search(query, num_results=num_results))
        return urls
    except Exception:
        return []

class DocChatBot:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.query_data = {}
        # Structure:
        # query_data = {
        #   'query_text': {
        #       'urls': [...list_of_urls...],
        #       'answers_per_url': {url1: [...answers...], url2: [...answers...]},
        #       'url_index': 0,
        #       'answer_index': 0
        #   }
        # }

    def get_next_answer(self, query):
        query = query.strip().lower()
        if query not in self.query_data:
            # First time: get URLs
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
        if not urls:
            return "[Info] No search results found."

        # Cycle through URLs
        attempts = 0
        while attempts < len(urls):
            current_url = urls[data['url_index']]
            if current_url not in data['answers_per_url']:
                # Fetch and parse answers from this url
                try:
                    response = requests.get(current_url, headers=CONFIG['HEADERS'], timeout=CONFIG['REQUEST_TIMEOUT'])
                    soup = BeautifulSoup(response.content, 'html.parser')
                    answers = extract_relevant_paragraphs(soup, query)
                    if not answers:
                        answers = ["[Info] No relevant content found on this page."]
                except Exception:
                    answers = ["[Info] Failed to fetch or parse the page."]
                data['answers_per_url'][current_url] = answers

            answers = data['answers_per_url'][current_url]
            if not answers:
                # No answers here, move on
                data['url_index'] = (data['url_index'] + 1) % len(urls)
                data['answer_index'] = 0
                attempts += 1
                continue

            # Provide next answer from current url
            answer = answers[data['answer_index'] % len(answers)]
            data['answer_index'] += 1

            # If we exhausted answers on this url, move to next url for next time
            if data['answer_index'] >= len(answers):
                data['answer_index'] = 0
                data['url_index'] = (data['url_index'] + 1) % len(urls)

            return answer

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
