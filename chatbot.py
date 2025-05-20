import json
import nltk
import string
import re
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

for res in ['punkt', 'wordnet', 'stopwords']:
    nltk.download(res, quiet=True)

class DocChatBot:
    def __init__(self, file_paths):
        self.file_paths = file_paths
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.paragraph_data = self._read_json_files()
        self.query_memory = {}  
        self.vectorizer = TfidfVectorizer()
        self.processed_headers = [p['processed_bold'] for p in self.paragraph_data]
        self.header_vectors = self.vectorizer.fit_transform(self.processed_headers)
        self.header_map = {p['processed_bold']: p for p in self.paragraph_data}

    def _read_json_files(self):
        paragraph_data = []
        for file_path in self.file_paths:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            for header, content_dict in data.items():
                content = ''
                for key, value in content_dict.items():
                    if isinstance(value, str) and value.strip():
                        content = value
                        break
                    elif isinstance(value, list) or isinstance(value, dict):
                        content = str(value)
                        break

                if content:
                    processed_bold = self._preprocess_text(header)
                    paragraph_data.append({
                        'bold': header,
                        'content': content,
                        'processed_bold': processed_bold,
                        'source': file_path
                    })

        return paragraph_data

    def _normalize_abbreviations(self, text):
        text = text.lower()
        text = re.sub(r'\bsupport vector machine\b', 'svm', text)
        text = re.sub(r'\bartificial intelligence\b', 'ai', text)
        text = re.sub(r'\bneural network\b', 'neuralnetwork', text)
        return text

    def _preprocess_text(self, text):
        text = self._normalize_abbreviations(text)
        tokens = nltk.word_tokenize(text.lower())
        filtered = [
            self.lemmatizer.lemmatize(t)
            for t in tokens
            if t not in string.punctuation and t not in self.stop_words
        ]
        return ' '.join(filtered)

    def _correct_query(self, query):
        processed_query = self._preprocess_text(query)

        if processed_query in self.header_map:
            return self.header_map[processed_query]

        query_vec = self.vectorizer.transform([processed_query])
        sims = cosine_similarity(query_vec, self.header_vectors).flatten()
        best_index = sims.argmax()
        best_score = sims[best_index]

        if best_score < 0.1:
            return None
        return self.paragraph_data[best_index]

    def get_response(self, query):
        match = self._correct_query(query)
        if not match:
            return "Sorry, I couldn't find relevant information for your question."
        sentences = nltk.sent_tokenize(match['content'])
        if not sentences:
            return "No relevant sentences found in the matched section."
        key = match['content'].strip()
        self.query_memory.setdefault(key, 0)
        index = self.query_memory[key] % len(sentences)
        self.query_memory[key] += 1
        return sentences[index]

    def chat(self):
        print("Welcome to the ChatBot! Ask about Lana Del Rey or Vijay.")
        print("Type 'exit' or 'quit' to stop.")
        print("You: ", end="", flush=True)
        while True:
            user_input = input().strip()
            if user_input.lower() in ['exit', 'quit']:
                print("Bot: Goodbye!")
                break
            response = self.get_response(user_input)
            print(f"Bot: {response}")
            print("You: ", end="", flush=True)

if __name__ == "__main__":
    json_files = ["LanaDelRey2.json"]
    chatbot = DocChatBot(json_files)
    chatbot.chat()  