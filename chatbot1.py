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
}
SKIP_PATTERNS = [r"cloudflare", r"access denied", r"captcha", r"404 error", r"subscribe", r"register", r"advertisement"]

def clean_text(text):
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return ""
    return text

def clean_answer_text(text):
    return re.sub(r'\s+', ' ', re.sub(r'\[[^\]]*\]', '', text)).strip()

def lemmatize_words(text, lemmatizer, stop_words):
    return set(lemmatizer.lemmatize(w) for w in word_tokenize(text.lower()) if w.isalpha() and w not in stop_words)

def is_meaningful_text(text, query_keywords, lemmatizer, stop_words):
    if len(text) < CONFIG['MIN_TEXT_LENGTH']: return False
    lemmas = lemmatize_words(text, lemmatizer, stop_words)
    overlap = query_keywords & lemmas
    alpha_ratio = sum(c.isalpha() for c in text) / max(len(text), 1)
    return len(overlap) / max(len(query_keywords), 1) >= CONFIG['MIN_KEYWORD_MATCH_RATIO'] and alpha_ratio > CONFIG['ALPHA_RATIO']

def is_definition_like(text, query):
    query = query.lower().strip().rstrip('?')
    terms = [query]
    if query.startswith(('what is ', 'who is ')):
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
    query = query.lower().strip().rstrip('?')
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
                except: pass
        q_key = question.strip().lower()
        found = False
        for qa in data["qas"]:
            if qa["question"].strip().lower() == q_key:
                found = True
                if isinstance(qa["answer"], str):
                    qa["answer"] = [qa["answer"]]
                if answer.strip() not in qa["answer"]:
                    qa["answer"].append(answer.strip())
                break
        if not found:
            data["qas"].append({"question": question.strip(), "answer": [answer.strip()]})
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_next_answer(self, query):
        query = query.strip().lower()
        query_keywords = lemmatize_words(query, self.lemmatizer, self.stop_words)
        if query not in self.query_data:
            urls = search_google_urls(query, self.driver)
            if not urls:
                answer = "[Error] Could not fetch search results."
                self.save_to_topic_json(query, answer)
                return answer
            self.query_data[query] = {'urls': urls, 'answers_per_url': {}, 'url_index': 0, 'answer_index': 0, 'failed_urls': set()}
        data = self.query_data[query]
        urls = data['urls']
        for _ in range(len(urls)):
            url = urls[data['url_index']]
            if url in data['failed_urls']:
                data['url_index'] = (data['url_index'] + 1) % len(urls)
                continue
            if url not in data['answers_per_url']:
                soup = self.fetch_with_selenium(url)
                if not soup:
                    data['failed_urls'].add(url)
                    data['url_index'] = (data['url_index'] + 1) % len(urls)
                    continue
                answers = extract_relevant_paragraphs(soup, query, self.lemmatizer, self.stop_words)
                if not answers:
                    data['failed_urls'].add(url)
                    data['url_index'] = (data['url_index'] + 1) % len(urls)
                    continue
                data['answers_per_url'][url] = answers
            answers = data['answers_per_url'][url]
            while data['answer_index'] < len(answers):
                ans = answers[data['answer_index']]
                data['answer_index'] += 1
                if ans not in SKIP_RESPONSES and clean_text(ans):
                    self.save_to_topic_json(query, ans)
                    return ans
            data['answer_index'] = 0
            data['url_index'] = (data['url_index'] + 1) % len(urls)
        if data['answers_per_url']:
            best = max(
                (para for paras in data['answers_per_url'].values() for para in paras),
                key=lambda p: len(set(word_tokenize(p.lower())) & query_keywords),
                default=None
            )
            if best:
                self.save_to_topic_json(query, best)
                return best
        fallback = "[Info] No accurate and relevant content found. Try rephrasing your question."
        self.save_to_topic_json(query, fallback)
        return fallback

    def chat(self):
        print("Welcome to the Smart ChatBot!\nType 'exit' to quit.")
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ['exit', 'quit']:
                print("AI Bot: Goodbye!")
                break
            response = self.get_next_answer(user_input)
            print(f"AI Bot: {response}")

if __name__ == "__main__":
    bot = DocChatBot()
    bot.chat()
