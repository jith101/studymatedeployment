import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score
from transformers import pipeline

# Sample data
data = {
    'word': ['excellent', 'poor', 'fantastic', 'horrible', 'amazing', 'bad', 'wonderful', 'inadequate'],
    'label': ['positive', 'negative', 'positive', 'negative', 'positive', 'negative', 'positive', 'negative']
}

# Convert to DataFrame
df = pd.DataFrame(data)

# Prepare the input and labels
X = df['word'].values  # Features
y = df['label'].values  # Labels

# Train-test split
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# Initialize the sentiment analysis pipeline
sentiment_model = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

# Make sure X_test is a list of strings
if isinstance(X_test, np.ndarray):
    X_test_list = X_test.tolist()  # Convert to list if it's a numpy array
else:
    X_test_list = X_test  # Ensure it's already a list of strings

# Predicting with Hugging Face model
huggingface_preds = sentiment_model(X_test_list)  # Pass the list of strings

# Extracting labels from predictions
huggingface_labels = [pred['label'].lower() for pred in huggingface_preds]

# Convert Hugging Face labels to match your labels
huggingface_labels = ['positive' if label == 'POSITIVE' else 'negative' for label in huggingface_labels]

# Evaluate Hugging Face model
hf_accuracy = accuracy_score(y_test, huggingface_labels)
hf_precision = precision_score(y_test, huggingface_labels, pos_label='positive', average='binary')
hf_recall = recall_score(y_test, huggingface_labels, pos_label='positive', average='binary')

print(f'distilbert Model - Accuracy: {hf_accuracy}, Precision: {hf_precision}, Recall: {hf_recall}')
