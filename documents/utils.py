import os
import re
from collections import Counter
import PyPDF2

# Stop words to ignore during keyword extraction
STOP_WORDS = {
    'the', 'and', 'is', 'in', 'to', 'of', 'it', 'for', 'a', 'on', 'with', 'as', 'by', 'that', 'this', 
    'are', 'was', 'be', 'an', 'or', 'at', 'from', 'which', 'not', 'have', 'has', 'we', 'they', 'but',
    'all', 'any', 'their', 'our', 'can', 'will', 'would', 'should', 'could', 'if', 'then', 'than'
}

def extract_text_from_file(file_path):
    """
    Extracts raw text from a given file path.
    Supports PDF and basic TXT. Returns empty string for unsupported formats.
    """
    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    
    try:
        if ext == '.pdf':
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        elif ext in ['.txt', '.csv']:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
    except Exception as e:
        print(f"Error extracting text from {file_path}: {e}")
        
    return text.strip()

def generate_keywords(text, num_keywords=5):
    """
    Analyzes text frequency and returns the top N most common meaningful words.
    """
    if not text:
        return []
        
    # Clean text: lowercase, remove non-alphanumeric, split into words
    clean_text = re.sub(r'[^a-zA-Z\s]', '', text).lower()
    words = clean_text.split()
    
    # Filter out short words and stop words
    valid_words = [w for w in words if len(w) > 3 and w not in STOP_WORDS]
    
    # Count frequencies
    word_counts = Counter(valid_words)
    
    # Return top N keywords
    return [word for word, count in word_counts.most_common(num_keywords)]

def generate_abstract(text):
    """
    Generates a basic abstract by extracting the first 3 meaningful sentences.
    """
    if not text:
        return "No extractable text found in this document."
        
    # Clean up excess whitespace
    clean_text = re.sub(r'\s+', ' ', text)
    
    # Split by periods to get sentences
    sentences = [s.strip() for s in clean_text.split('.') if len(s.strip()) > 20]
    
    if not sentences:
        return "Document contains text, but no clear sentences could be extracted for a summary."
        
    # Take first 3 sentences
    abstract = '. '.join(sentences[:3]) + '.'
    return abstract
