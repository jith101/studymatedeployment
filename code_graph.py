import matplotlib.pyplot as plt
from gensim.models import KeyedVectors
from sklearn.decomposition import PCA
import numpy as np

# Load the GloVe model (replace with the correct path to your model file)
glove_model = KeyedVectors.load("glove_wiki_gigaword_300.model")

# Define word lists
positive_words = [
    'excellent', 'outstanding', 'fantastic', 'great', 'wonderful', 'amazing', 'super', 'impressive', 
    'brilliant', 'skilled', 'knowledgeable', 'dedicated', 'helpful', 'supportive', 'encouraging', 
    'friendly', 'professional', 'engaging', 'motivating', 'remarkable', 'exceptional', 'awesome', 
    'reliable', 'trustworthy', 'innovative', 'enthusiastic', 'proficient', 'talented', 'competent', 
    'effective', 'efficient', 'passionate', 'creative', 'insightful', 'adaptable', 'organized', 
    'patient', 'resourceful', 'visionary', 'collaborative', 'appreciative', 'polished', 'positive'
]

negative_words = [
    'poor', 'bad', 'awful', 'horrible', 'inadequate', 'unsatisfactory', 'ineffective', 'unhelpful', 
    'disappointing', 'unprofessional', 'dull', 'boring', 'incompetent', 'rude', 'disorganized', 
    'unprepared', 'unresponsive', 'indifferent', 'slow', 'confusing', 'biased', 'unreliable', 
    'unpleasant', 'uncaring', 'unfriendly', 'unmotivated', 'undependable', 'untrustworthy', 
    'unproductive', 'unapproachable', 'unskilled', 'unqualified', 'unreceptive', 'unconcerned', 
    'unimpressive', 'underwhelming', 'uncooperative', 'unenthusiastic', 'unforgiving', 'uncertain',
    'dishonest', 'inefficient', 'inconsistent', 'impolite', 'disorganized', 'inconsiderate',
    'apathetic', 'hostile', 'negligent', 'disengaged', 'callous'
]

filler_words = [
    'like', 'uh', 'um', 'you','know', 'just', 'sort','of', 'kind', 'this', 'that', 'actually', 
    'basically', 'literally', 'seriously', 'not', 'want', 'I', 'he', 'she', 'him', 'her', 
    'they', 'them', 'there', 'if', 'that', 'thing', 'really', 'so', 'right', 'well', 'got', 
    'maybe', 'could', 'might', 'sort', 'gonna', 'kinda', 'pretty', 'look', 'see', 'feel', 
    'get', 'would', 'should', 'do', 'did', 'has', 'have', 'having', 'been', 'am', 'are', 
    'is', 'was', 'were'
]

# Filter words that are available in the GloVe model
positive_embeddings = [glove_model[word] for word in positive_words if word in glove_model]
negative_embeddings = [glove_model[word] for word in negative_words if word in glove_model]
filler_embeddings = [glove_model[word] for word in filler_words if word in glove_model]

# Combine embeddings and labels
embeddings = np.array(positive_embeddings + negative_embeddings + filler_embeddings)
labels = ['Positive'] * len(positive_embeddings) + ['Negative'] * len(negative_embeddings) + ['Filler'] * len(filler_embeddings)

# Reduce dimensions with PCA
pca = PCA(n_components=2)
reduced_embeddings = pca.fit_transform(embeddings)

# Plot
plt.figure(figsize=(12, 8))

# Scatter plot for each category
colors = {'Positive': 'green', 'Negative': 'red', 'Filler': 'blue'}
for label in set(labels):
    idxs = [i for i, l in enumerate(labels) if l == label]
    plt.scatter(reduced_embeddings[idxs, 0], reduced_embeddings[idxs, 1], c=colors[label], label=label, alpha=0.6, s=50)

# Add labels and title
plt.title("2D Visualization of Positive, Negative, and Filler Words")
plt.xlabel("PCA Component 1")
plt.ylabel("PCA Component 2")
plt.legend()
plt.show()
