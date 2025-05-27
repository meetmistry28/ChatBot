import nltk
import re
import time
import json
import os
import shutil
import traceback
from bs4 import BeautifulSoup
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk import pos_tag, word_tokenize, ne_chunk
from nltk.tree import Tree
import undetected_chromedriver as uc
from urllib.parse import quote_plus
from selenium.common.exceptions import InvalidSessionIdException, WebDriverException

# Download required NLTK data
nltk.download('maxent_ne_chunker_tab')
nltk.download('words')
nltk.download('averaged_perceptron_tagger')
nltk.download('punkt')
nltk.download('stopwords')

# Configuration
CONFIG = {
    'NUM_RESULTS': 200,
    'MAX_PARAS_PER_SITE': 2,
    'MIN_TEXT_LENGTH': 70,
    'ALPHA_RATIO': 0.7,
    'HEADLESS': False,
    'MIN_KEYWORD_MATCH_RATIO': 0.7,
    'MAX_RETRIES': 3,
    'RETRY_DELAY': 2
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
    original_query = query
    for attempt in range(CONFIG['MAX_RETRIES']):
        try:
            print(f"[Info] Searching for query: {query} (attempt {attempt + 1}/{CONFIG['MAX_RETRIES']})")
            driver.get(f"https://www.bing.com/search?q={quote_plus(query)}")
            time.sleep(3)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            urls = [a['href'] for a in soup.select('li.b_algo h2 a') if a.get('href', '').startswith('http')][:CONFIG['NUM_RESULTS']]
            if urls:
                print(f"[Info] Found {len(urls)} URLs for query: {query}")
                return urls
            print(f"[Warning] No URLs found for query: {query}")
            if attempt == CONFIG['MAX_RETRIES'] - 1 and query == original_query:
                query = f"{original_query} site:*"
                print(f"[Info] Retrying with modified query: {query}")
        except (InvalidSessionIdException, WebDriverException) as e:
            print(f"[Error] Failed to fetch search results for '{query}' (attempt {attempt + 1}/{CONFIG['MAX_RETRIES']}): {str(e)}")
            if attempt < CONFIG['MAX_RETRIES'] - 1:
                time.sleep(CONFIG['RETRY_DELAY'])
            continue
    print(f"[Error] All attempts failed to fetch search results for '{original_query}'")
    return []

def extract_named_entities(query):
    chunked = ne_chunk(pos_tag(word_tokenize(query)))
    return [" ".join(leaf[0] for leaf in subtree.leaves()).lower() for subtree in chunked if isinstance(subtree, Tree)]

def normalize_topic_name(query, stop_words):
    query = query.lower().strip().rstrip('?')
    if not query:
        return "general"
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
        self.history = []
        self.question_history = {}
        self.temp_dir = None
        os.makedirs("data", exist_ok=True)
        self.driver = None
        self.initialize_driver()

    def initialize_driver(self):
        try:
            options = uc.ChromeOptions()
            if CONFIG['HEADLESS']:
                options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
            self.driver = uc.Chrome(options=options, version_main=136)
            print("[Info] WebDriver initialized successfully")
        except Exception as e:
            print(f"[Error] Failed to initialize WebDriver: {str(e)}")
            self.driver = None

    def fetch_with_selenium(self, url):
        if not self.driver:
            self.initialize_driver()
            if not self.driver:
                print(f"[Error] Failed to initialize WebDriver for URL: {url}")
                return None
        for attempt in range(CONFIG['MAX_RETRIES']):
            try:
                print(f"[Info] Fetching URL: {url} (attempt {attempt + 1}/{CONFIG['MAX_RETRIES']})")
                self.driver.get(url)
                time.sleep(3)
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                print(f"[Info] Successfully fetched URL: {url}")
                return soup
            except (InvalidSessionIdException, WebDriverException) as e:
                print(f"[Error] Failed to fetch {url} (attempt {attempt + 1}/{CONFIG['MAX_RETRIES']}): {str(e)}")
                self.initialize_driver()
                if attempt < CONFIG['MAX_RETRIES'] - 1:
                    time.sleep(CONFIG['RETRY_DELAY'])
                continue
        print(f"[Error] All attempts failed to fetch URL: {url}")
        return None

    def save_to_topic_json(self, question, answer, topic):
        path = os.path.join("data", f"{topic}.json")
        data = {"qas": []}
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                print(f"[Error] Failed to read {path}: {str(e)}")
        data["qas"].append({"question": question, "answer": answer})
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Error] Failed to save to {path}: {str(e)}")

    def __del__(self):
        try:
            if hasattr(self, 'driver') and self.driver:
                print(f"[Info] Closing WebDriver: {self.driver}")
                self.driver.quit()
                self.driver = None
            if hasattr(self, 'temp_dir') and self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            print(f"[Warning] Error during cleanup: {str(e)}")

    def get_next_answer(self, query, continue_topic=None):
        query = query.strip().lower()
        if not query:
            return "[Error] Empty query provided."
        
        topic = continue_topic if continue_topic else normalize_topic_name(query, self.stop_words)
        
        if topic not in self.history:
            self.history.append(topic)
            if len(self.history) > 2:
                self.history.pop(0)
        
        if topic not in self.question_history:
            self.question_history[topic] = []

        path = os.path.join("data", f"{topic}.json")
        query_keywords = lemmatize_words(query, self.lemmatizer, self.stop_words)
        
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data_json = json.load(f)
                    for qa in data_json["qas"]:
                        qa_key = qa["question"].strip().lower()
                        qa_keywords = lemmatize_words(qa_key, self.lemmatizer, self.stop_words)
                        if len(query_keywords & qa_keywords) / max(len(query_keywords), 1) >= CONFIG['MIN_KEYWORD_MATCH_RATIO']:
                            answers = qa["answer"] if isinstance(qa["answer"], list) else [qa["answer"]]
                            if query not in self.query_data:
                                self.query_data[query] = {'answers': answers, 'answer_index': 0}
                            data_query = self.query_data[query]
                            if data_query['answer_index'] < len(answers):
                                ans = answers[data_query['answer_index']]
                                data_query['answer_index'] += 1
                                if ans not in SKIP_RESPONSES and clean_text(ans):
                                    self.save_to_topic_json(query, ans, topic)
                                    return ans
                            data_query['answer_index'] = 0
            except Exception as e:
                print(f"[Error] Failed to read {path}: {str(e)}")

        self.query_data.pop(query, None)

        urls = search_google_urls(query, self.driver)
        if not urls:
            self.save_to_topic_json(query, "[Error] Could not fetch search results.", topic)
            self.question_history[topic].append({'question': query, 'last_answer_index': 0})
            return "[Error] Could not fetch search results."

        self.query_data[query] = {'urls': urls, 'answers_per_url': {}, 'url_index': 0, 'answer_index': 0, 'failed_urls': set()}
        data_query = self.query_data[query]

        attempt = 0
        max_attempts = 2
        while attempt < max_attempts:
            for _ in range(len(urls)):
                url = urls[data_query['url_index']]
                if url in data_query['failed_urls']:
                    data_query['url_index'] = (data_query['url_index'] + 1) % len(urls)
                    continue
                if url not in data_query['answers_per_url']:
                    soup = self.fetch_with_selenium(url)
                    if not soup:
                        data_query['failed_urls'].add(url)
                        data_query['url_index'] = (data_query['url_index'] + 1) % len(urls)
                        continue
                    answers = extract_relevant_paragraphs(soup, query, self.lemmatizer, self.stop_words)
                    if answers:
                        data_query['answers_per_url'][url] = answers
                    else:
                        data_query['failed_urls'].add(url)
                        data_query['url_index'] = (data_query['url_index'] + 1) % len(urls)
                        continue

                answers = data_query['answers_per_url'][url]
                while data_query['answer_index'] < len(answers):
                    ans = answers[data_query['answer_index']]
                    data_query['answer_index'] += 1
                    if ans not in SKIP_RESPONSES and clean_text(ans):
                        self.save_to_topic_json(query, ans, topic)
                        self.question_history[topic].append({'question': query, 'last_answer_index': data_query['answer_index'] - 1})
                        return ans

                data_query['answer_index'] = 0
                data_query['url_index'] = (data_query['url_index'] + 1) % len(urls)

            attempt += 1
            print(f"[Info] No answers found for '{query}' in attempt {attempt}. Retrying search...")
            urls = search_google_urls(query, self.driver)
            if not urls:
                self.save_to_topic_json(query, "[Error] Could not fetch search results after retries.", topic)
                self.question_history[topic].append({'question': query, 'last_answer_index': 0})
                return "[Error] Could not fetch search results after retries."
            self.query_data[query] = {'urls': urls, 'answers_per_url': {}, 'url_index': 0, 'answer_index': 0, 'failed_urls': set()}
            data_query = self.query_data[query]

        if data_query['answers_per_url']:
            best = max(
                (para for paras in data_query['answers_per_url'].values() for para in paras),
                key=lambda p: len(set(word_tokenize(p.lower())) & query_keywords),
                default=None
            )
            if best:
                self.save_to_topic_json(query, best, topic)
                self.question_history[topic].append({'question': query, 'last_answer_index': 0})
                return best

        self.save_to_topic_json(query, f"[Error] No relevant content found for '{query}'.", topic)
        self.question_history[topic].append({'question': query, 'last_answer_index': 0})
        return f"[Error] No relevant content found for '{query}'."

    def chat(self):
        print("Welcome to the Smart ChatBot!\nType 'exit' to quit.\nType 'continue' or 'last' to resume a recent topic.\nType 'reset search' to restart the search for the last question.")
        try:
            while True:
                user_input = input("You: ").strip()
                if user_input.lower() in ['exit', 'quit']:
                    print("AI Bot: Goodbye!")
                    break
                if not user_input:
                    print("AI Bot: Please enter a question or topic to continue.")
                    continue

                continue_topic = None
                if re.search(r'\bcontinue\s+last\s+question\b', user_input.lower()):
                    if self.history and self.question_history.get(self.history[-1]):
                        topic = self.history[-1]
                        last_q = self.question_history[topic][-1]['question']
                        print(f"[Info] Continuing from question '{last_q}' in topic '{topic}'")
                        response = self.get_next_answer(last_q, topic)
                        print(f"AI Bot: {response}")
                    else:
                        print("AI Bot: No previous question in this topic.")
                    continue
                elif user_input.lower() == 'reset search':
                    if self.history and self.question_history.get(self.history[-1]):
                        topic = self.history[-1]
                        last_q = self.question_history[topic][-1]['question']
                        self.query_data.pop(last_q, None)
                        print(f"[Info] Reset search for '{last_q}'")
                        response = self.get_next_answer(last_q, topic)
                        print(f"AI Bot: {response}")
                    else:
                        print("AI Bot: No previous question to reset.")
                    continue
                elif (re.search(r'\b(continue|last|previous|go back)\b', user_input.lower()) or
                      re.search(r'^\s*(what|when|where|why|how|who)\b', user_input.lower()) or
                      re.search(r'\b(he|him|his|she|her|it|its|this|that)\b', user_input.lower()) or
                      user_input.lower() == 'what is last topic'):
                    if self.history:
                        continue_topic = self.history[-1]
                        if self.question_history.get(continue_topic):
                            last_q = self.question_history[continue_topic][-1]['question']
                            is_person = re.search(r'\b(who\s+is|what\s+is\s+.*person)\b', last_q.lower()) or continue_topic.replace('_', ' ').title() in extract_named_entities(last_q)
                            topic_name = continue_topic.replace('_', ' ')
                            if user_input.lower() == 'what is last topic':
                                reformulated_query = last_q
                            elif re.search(r'\bwhen\s+(he|him|his|she|her)\s+born\b', user_input.lower()):
                                reformulated_query = f"when was {topic_name} born" if is_person else f"when was {topic_name} founded"
                            elif re.search(r'\bwhere\s+(he|him|his|she|her)\s+live(s)?\b', user_input.lower()):
                                reformulated_query = f"where does {topic_name} live" if is_person else f"where is {topic_name} headquartered"
                            elif re.search(r'\b(what|who)\s+is\s+(his|her)\s+(job|occupation|role)\b', user_input.lower()):
                                reformulated_query = f"what is {topic_name}'s job" if is_person else f"what is the role of {topic_name}"
                            elif re.search(r'\bhow\s+old\s+is\s+(he|him|his|she|her)\b', user_input.lower()):
                                reformulated_query = f"how old is {topic_name}" if is_person else f"how old is {topic_name} company"
                            elif re.search(r'\bwhy\s+(is\s+)?((he|him|his|she|her)\s+(famous|known)|it\s+(used|important))\b', user_input.lower()):
                                if is_person:
                                    reformulated_query = f"why is {topic_name} famous"
                                else:
                                    reformulated_query = f"what is {topic_name} used for" if "used" in user_input.lower() else f"why is {topic_name} important"
                            elif re.search(r'^\s*(what|when|where|why|how|who)\b', user_input.lower()):
                                user_input_clean = re.sub(r'\b(he|him|his|she|her|it|its|this|that)\b', topic_name, user_input.lower(), flags=re.IGNORECASE)
                                reformulated_query = f"{user_input_clean.strip()} {topic_name}"
                            else:
                                reformulated_query = f"{user_input.lower()} {continue_topic}"
                            print(f"[Info] Reformulated query: '{reformulated_query}' for topic '{continue_topic}'")
                            response = self.get_next_answer(reformulated_query, continue_topic)
                        else:
                            print(f"AI Bot: No questions found for topic '{continue_topic}'. Treating as new question.")
                            response = self.get_next_answer(user_input, None)
                    else:
                        print(f"[Info] No history found. Treating '{user_input}' as new question.")
                        response = self.get_next_answer(user_input, None)
                else:
                    print(f"[Info] Treating '{user_input}' as new question.")
                    response = self.get_next_answer(user_input, None)
                print(f"AI Bot: {response}")

        except KeyboardInterrupt:
            print("\nAI Bot: Interrupted by user. Exiting...")
        except Exception as e:
            print(f"[Error] An error occurred: {str(e)}")
            traceback.print_exc()
        finally:
            self.__del__()

if __name__ == "__main__":
    try:
        bot = DocChatBot()
        print(f"[Debug] Bot type: {type(bot)}")
        print(f"[Debug] Bot methods: {dir(bot)}")
        bot.chat()
    except Exception as e:
        print(f"[Error] Main error: {str(e)}")
        traceback.print_exc()
