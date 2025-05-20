import json
import nltk
import string
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords

# Download required resources
for res in ['punkt', 'wordnet', 'stopwords']:
    nltk.download(res, quiet=True)

class DocChatBot:
    def __init__(self, file_paths):
        self.file_paths = file_paths
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.paragraph_data = self._read_json_files()
        self.query_memory = {}
        self.main_keywords = ['vijay', 'akshay', 'lana', 'ai']  # Add more if needed

    def _read_json_files(self):
        paragraph_data = []
        for file_path in self.file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
            except FileNotFoundError:
                print(f"Warning: File {file_path} not found.")
                continue

            for header, content_dict in data.items():
                content = ''
                for key, value in content_dict.items():
                    if isinstance(value, str) and value.strip():
                        content = value
                        break
                    elif isinstance(value, (list, dict)):
                        content = str(value)
                        break

                if content:
                    paragraph_data.append({
                        'bold': header,
                        'content': content,
                        'source': file_path
                    })

        return paragraph_data

    def _preprocess_text(self, text):
        tokens = nltk.word_tokenize(text.lower())
        return [
            self.lemmatizer.lemmatize(t)
            for t in tokens
            if t not in string.punctuation and t not in self.stop_words
        ]

    def _find_main_topic(self, query):
        query_tokens = self._preprocess_text(query)
        keyword_scores = {kw: 0 for kw in self.main_keywords}

        # Count keyword matches in query
        for token in query_tokens:
            for kw in self.main_keywords:
                if kw in token or token in kw:
                    keyword_scores[kw] += 1

        # Find paragraphs matching keywords
        best_keyword = None
        max_score = -1
        for kw, score in keyword_scores.items():
            if score > 0:
                for p in self.paragraph_data:
                    if kw in p['bold'].lower():
                        if score > max_score:
                            max_score = score
                            best_keyword = kw
                        break

        return best_keyword

    def get_response(self, query):
        main_keyword = self._find_main_topic(query)
        if not main_keyword:
            return "Sorry, I couldn't identify the main topic. Please include a name like 'Vijay', 'Akshay', 'Lana', or 'AI'."

        # Find paragraph related to main keyword
        matched_paragraph = None
        for p in self.paragraph_data:
            if main_keyword in p['bold'].lower():
                matched_paragraph = p
                break

        if not matched_paragraph:
            return f"Sorry, no information found for '{main_keyword}'."

        sentences = nltk.sent_tokenize(matched_paragraph['content'])
        if not sentences:
            return "No content found under that topic."

        # Create memory key for topic
        key = matched_paragraph['bold']

        # Setup memory if first time
        if key not in self.query_memory:
            self.query_memory[key] = {
                'sentences': sentences,
                'index': 0,
                'last_query': None
            }

        mem = self.query_memory[key]

        # Check if the query is the same as the last one for this topic
        query_tokens = self._preprocess_text(query)
        same_query = mem['last_query'] and set(query_tokens).intersection(set(self._preprocess_text(mem['last_query'])))
        
        # Update last query
        mem['last_query'] = query

        # Try to return relevant sentence based on query keywords
        query_keywords = ['salary', 'income', 'earn', 'payment', 'money']
        if not same_query:  # For new queries, try to match specific content
            for sent in sentences:
                sent_tokens = self._preprocess_text(sent)
                if any(word in sent_tokens for word in query_keywords + query_tokens):
                    mem['index'] = (mem['sentences'].index(sent) + 1) % len(mem['sentences'])
                    return sent

        # For same query or no specific match, return next sentence in sequence
        response = mem['sentences'][mem['index']]
        mem['index'] = (mem['index'] + 1) % len(mem['sentences'])  # Loop back to start if end is reached
        return response

    def chat(self):
        print("Welcome to the ChatBot! Ask about Vijay, Akshay, Lana, or AI.")
        print("Type 'exit' or 'quit' to stop.")
        print("You: ", end="", flush=True)
        while True:
            user_input = input().strip()
            if user_input.lower() in ['exit', 'quit']:
                print("AI Bot: Goodbye!")
                break
            response = self.get_response(user_input)
            print(f"chatBot: {response}")
            print("You: ", end="", flush=True)

if __name__ == "__main__":
    json_files = ["vijay_4.json", "lana_2.json"]
    chatbot = DocChatBot(json_files)
    chatbot.chat()