import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords, wordnet
from nltk.stem import PorterStemmer, WordNetLemmatizer
from docx import Document

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('omw-1.4')  # Optional, for WordNet lemmatizer

def read_word_file(file_path):
    """Reads text from a .docx file."""
    doc = Document(file_path)
    full_text = " ".join([para.text for para in doc.paragraphs])
    return full_text.strip()

def tokenize_text(text):
    """Tokenizes, removes stopwords, stems, and lemmatizes the text."""
    print("\n🔹 Original Text:")
    print(text)

    # Tokenization
    word_tokens = word_tokenize(text)
    sentence_tokens = sent_tokenize(text)

    print("\n🔸 Word Tokens:")
    print(word_tokens)
    print("\n🔸 Sentence Tokens:")
    print(sentence_tokens)

    # Stopwords removal
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [word for word in word_tokens if word.lower() not in stop_words and word.isalpha()]
    print("\n🔸 After Removing Stopwords:")
    print(filtered_tokens)

    # Stemming
    stemmer = PorterStemmer()
    stemmed_tokens = [stemmer.stem(word) for word in filtered_tokens]
    print("\n🔸 Stemmed Tokens:")
    print(stemmed_tokens)

    # Lemmatization
    lemmatizer = WordNetLemmatizer()
    lemmatized_tokens = [lemmatizer.lemmatize(word) for word in filtered_tokens]
    print("\n🔸 Lemmatized Tokens:")
    print(lemmatized_tokens)

    return {
        "word_tokens": word_tokens,
        "sentence_tokens": sentence_tokens,
        "filtered_tokens": filtered_tokens,
        "stemmed_tokens": stemmed_tokens,
        "lemmatized_tokens": lemmatized_tokens
    }

# ✅ Change this to your actual .docx file path
file_path = 'wiki_output_clean1.docx'

# Read and process text
text = read_word_file(file_path)
tokenize_text(text)
