import nltk
import re
import time
import json
import os
from bs4 import BeautifulSoup
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk import pos_tag, word_tokenize, ne_chunk
from nltk.tree import Tree
import undetected_chromedriver as uc
from urllib.parse import quote_plus

for res in ['punkt', 'wordnet', 'stopwords', 'averaged_perceptron_tagger', 'maxent_ne_chunker', 'words']:
    nltk.download(res, quiet=True)

CONFIG = {
    'NUM_RESULTS': 100,
    'MAX_PARAS_PER_SITE': 2,
    'MIN_TEXT_LENGTH': 70,
    'ALPHA_RATIO': 0.7,
    'HEADLESS': False,
    'MIN_KEYWORD_MATCH_RATIO': 0.7
}

SKIP_RESPONSES = {
    "[Info] No relevant content found on this page.",
    "[Info] Failed to fetch or parse the page.",
    "[Info] No accurate and relevant content found. Try rephrasing your question."
}
SKIP_PATTERNS = [r"cloudflare", r"access denied", r"captcha", r"404 error", r"subscribe", r"register", r"advertisement"]

def clean_text(text):
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return ""
    return text

def clean_answer_text(text):
    return re.sub(r'\s+', ' ', re.sub(r'\[[^\]]*\]', '', text)).strip()

def normalize_question(question):
    """Normalize question by removing punctuation, extra spaces, and converting to lowercase."""
    question = re.sub(r'[^\w\s]', '', question)  # Remove punctuation
    question = re.sub(r'\s+', ' ', question.strip()).lower()  # Normalize spaces and case
    return question

def lemmatize_words(text, lemmatizer, stop_words):
    return set(lemmatizer.lemmatize(w) for w in word_tokenize(text.lower()) if w.isalpha() and w not in stop_words)

def is_meaningful_text(text, query_keywords, lemmatizer, stop_words):
    if len(text) < CONFIG['MIN_TEXT_LENGTH']: return False
    lemmas = lemmatize_words(text, lemmatizer, stop_words)
    overlap = query_keywords & lemmas
    alpha_ratio = sum(c.isalpha() for c in text) / max(len(text), 1)
    return len(overlap) / max(len(query_keywords), 1) >= CONFIG['MIN_KEYWORD_MATCH_RATIO'] and alpha_ratio > CONFIG['ALPHA_RATIO']

def is_definition_like(text, query):
    query = normalize_question(query)
    terms = [query]
    if query.startswith(('what is ', 'who is ', 'why ', 'how ')):
        terms.append(query.split(' ', 2)[-1])
    for term in terms:
        if re.match(rf"^{re.escape(term)}\s+(is|was|are|refers to|means|can be defined as|is known as)\b", text.lower()):
            return True
    return False

def extract_relevant_paragraphs(soup, query, lemmatizer, stop_words):
    query_keywords = lemmatize_words(query, lemmatizer, stop_words)
    candidates = []
    for para in soup.find_all('p'):
        text = clean_text(para.get_text(separator=' ', strip=True))
        if not text: continue
        text = clean_answer_text(text)
        if text in SKIP_RESPONSES or len(text.split()) < 10: continue
        lemmas = lemmatize_words(text, lemmatizer, stop_words)
        overlap = len(query_keywords & lemmas)
        is_def = is_definition_like(text, query)
        candidates.append((is_def, overlap, text))
    candidates.sort(key=lambda x: (not x[0], -x[1]))
    return [x[2] for x in candidates[:CONFIG['MAX_PARAS_PER_SITE']] if is_meaningful_text(x[2], query_keywords, lemmatizer, stop_words)]

def search_google_urls(query, driver):
    driver.get(f"https://www.bing.com/search?q={quote_plus(query)}")
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    return [a['href'] for a in soup.select('li.b_algo h2 a') if a.get('href', '').startswith('http')][:CONFIG['NUM_RESULTS']]

def extract_named_entities(query):
    chunked = ne_chunk(pos_tag(word_tokenize(query)))
    return [" ".join(leaf[0] for leaf in subtree.leaves()).lower() for subtree in chunked if isinstance(subtree, Tree)]

def normalize_topic_name(query, stop_words):
    query = normalize_question(query)
    lemmatizer = WordNetLemmatizer()
    entities = extract_named_entities(query)
    existing_topics = [f[:-5] for f in os.listdir('data') if f.endswith('.json')]

    for entity in entities:
        slug = entity.replace(' ', '_')
        for topic in existing_topics:
            if slug == topic or slug in topic or topic in slug:
                return topic
        return slug

    nouns = [w for w, pos in pos_tag(word_tokenize(query)) if pos.startswith('NN') and w not in stop_words]
    if nouns:
        base = '_'.join(sorted(set(lemmatizer.lemmatize(w) for w in nouns)))
        for topic in existing_topics:
            if base == topic or base in topic or topic in base:
                return topic
        return base

    fallback = [w for w in re.findall(r'\b[a-z]+\b', query) if w not in stop_words]
    slug = '_'.join(fallback[:3]) or 'general'
    for topic in existing_topics:
        if slug == topic or slug in topic or topic in slug:
            return topic
    return slug

class DocChatBot:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.query_data = {}
        os.makedirs("data", exist_ok=True)
        options = uc.ChromeOptions()
        if CONFIG['HEADLESS']: options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument("user-agent=Mozilla/5.0 ... Chrome/115.0.0.0 Safari/537.36")
        self.driver = uc.Chrome(options=options)

    def fetch_with_selenium(self, url):
        try:
            self.driver.get(url)
            time.sleep(3)
            return BeautifulSoup(self.driver.page_source, 'html.parser')
        except:
            return None

    def __del__(self):
        try: self.driver.quit()
        except: pass

    def save_to_topic_json(self, question, answer):
        topic = normalize_topic_name(question, self.stop_words)
        path = os.path.join("data", f"{topic}.json")
        data = {"topic": topic, "qas": []}
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if not isinstance(data.get("qas", []), list):
                        data["qas"] = []
                except:
                    data = {"topic": topic, "qas": []}
        q_key = normalize_question(question)
        found = False
        for qa in data["qas"]:
            if normalize_question(qa["question"]) == q_key:
                found = True
                if isinstance(qa["answer"], str):
                    qa["answer"] = [qa["answer"]]
                if answer.strip() and answer.strip() not in qa["answer"] and answer.strip() not in SKIP_RESPONSES:
                    qa["answer"].append(answer.strip())
                break
        if not found and answer.strip() and answer.strip() not in SKIP_RESPONSES:
            data["qas"].append({"question": question.strip(), "answer": [answer.strip()]})
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_from_json(self, question):
        topic = normalize_topic_name(question, self.stop_words)
        path = os.path.join("data", f"{topic}.json")
        if not os.path.exists(path):
            return None, None
        with open(path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if not isinstance(data.get("qas", []), list):
                    return None, topic
                for qa in data.get("qas", []):
                    if not isinstance(qa.get("answer"), list):
                        qa["answer"] = [qa["answer"]] if isinstance(qa.get("answer"), str) else []
                    if normalize_question(qa["question"]) == normalize_question(question):
                        return [ans for ans in qa["answer"] if ans and ans not in SKIP_RESPONSES], topic
                return None, topic
            except:
                return None, topic

    def suggest_related_questions(self, query, topic):
        suggestions = []
        query_keywords = lemmatize_words(query, self.lemmatizer, self.stop_words)
        
        # Check current topic's JSON
        if topic:
            path = os.path.join("data", f"{topic}.json")
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                    except:
                        data = {"qas": []}
                for qa in data.get("qas", []):
                    if normalize_question(qa["question"]) != normalize_question(query):
                        q_keywords = lemmatize_words(qa["question"], self.lemmatizer, self.stop_words)
                        overlap = len(query_keywords & q_keywords) / max(len(query_keywords), 1)
                        if overlap > 0.5:  # Threshold for relevance
                            suggestions.append(qa["question"])

        # If fewer than 2 suggestions, search all other JSON files
        if len(suggestions) < 2:
            for json_file in os.listdir('data'):
                if json_file.endswith('.json') and json_file[:-5] != topic:
                    with open(os.path.join("data", json_file), 'r', encoding='utf-8') as f:
                        try:
                            data = json.load(f)
                        except:
                            continue
                        for qa in data.get("qas", []):
                            q_keywords = lemmatize_words(qa["question"], self.lemmatizer, self.stop_words)
                            overlap = len(query_keywords & q_keywords) / max(len(query_keywords), 1)
                            if overlap > 0.5 and qa["question"] not in suggestions:
                                suggestions.append(qa["question"])
                            if len(suggestions) >= 2:  # Aim for at least 2 suggestions
                                break
                if len(suggestions) >= 2:
                    break

        return suggestions[:3]  # Return up to 3 related questions

    def get_next_answer(self, query):
        stored_answers, topic = self.get_from_json(query)
        if stored_answers:
            used = self.query_data.get(normalize_question(query), {}).get("used_answers", set())
            for ans in stored_answers:
                if ans and ans not in used and ans not in SKIP_RESPONSES:
                    self.query_data.setdefault(normalize_question(query), {"used_answers": set()})["used_answers"].add(ans)
                    return ans, topic

        query_keywords = lemmatize_words(query, self.lemmatizer, self.stop_words)
        urls = search_google_urls(query, self.driver)
        for url in urls:
            soup = self.fetch_with_selenium(url)
            if not soup:
                continue
            answers = extract_relevant_paragraphs(soup, query, self.lemmatizer, self.stop_words)
            for ans in answers:
                if (not stored_answers or ans not in stored_answers) and ans not in SKIP_RESPONSES and clean_text(ans):
                    self.save_to_topic_json(query, ans)
                    self.query_data.setdefault(normalize_question(query), {"used_answers": set()})["used_answers"].add(ans)
                    return ans, topic

        fallback = "[Info] No accurate and relevant content found. Try rephrasing your question."
        self.save_to_topic_json(query, fallback)
        return fallback, topic

    def chat(self):
        print("Welcome to the Smart ChatBot!\nType 'exit' to quit.")
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ['exit', 'quit']:
                print("AI Bot: Goodbye!")
                break
            response, topic = self.get_next_answer(user_input)
            print(f"AI Bot: {response}")
            suggestions = self.suggest_related_questions(user_input, topic)
            if suggestions:
                print("\nRelated questions you might be interested in:")
                for i, q in enumerate(suggestions, 1):
                    print(f"{i}. {q}")
            print()

if __name__ == "__main__":
    bot = DocChatBot()
    bot.chat()
