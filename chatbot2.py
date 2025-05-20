import requests
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import sent_tokenize
import json
import uuid
from googlesearch import search

nltk.download('punkt')

def get_search_urls(query, num_results=5):
    try:
        urls = []
        for url in search(query, num_results=num_results, lang="en"):
            urls.append(url)
        return urls
    except Exception as e:
        print(f"Error fetching search URLs: {e}")
        return []

def extract_sentences_from_url(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        # Extract text from paragraphs, list items, and divs (optional)
        texts = []
        for tag in ['p', 'li', 'div']:
            elements = soup.find_all(tag)
            for el in elements:
                text = el.get_text(separator=' ', strip=True)
                if len(text.split()) > 5:
                    texts.append(text)

        full_text = " ".join(texts)
        sentences = sent_tokenize(full_text)
        return sentences[:7]  # Return first 7 sentences to increase info
    except Exception as e:
        print(f"Error extracting from {url}: {e}")
        return []

def save_to_json(question, answers, filename="answers.json"):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    topic = "General"

    if topic not in data:
        data[topic] = []

    data[topic].append({
        "id": str(uuid.uuid4()),
        "question": question,
        "answers": answers
    })

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def chatbot():
    print("Welcome to the chatbot! Type 'exit' or 'quit' to stop.")
    while True:
        question = input("\nAsk a question: ").strip()
        if question.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break
        if not question:
            print("Please enter a question.")
            continue

        urls = get_search_urls(question)
        print("Fetched URLs:", urls)

        all_answers = []
        for url in urls:
            answers = extract_sentences_from_url(url)
            all_answers.extend(answers)

        unique_answers = list(dict.fromkeys(all_answers))[:5]

        if unique_answers:
            print("\nAnswers from Search Results:")
            for i, ans in enumerate(unique_answers, 1):
                print(f"{i}. {ans}")
            save_to_json(question, unique_answers)
        else:
            print("Sorry, no good answer found.")

if __name__ == "__main__":
    chatbot()
