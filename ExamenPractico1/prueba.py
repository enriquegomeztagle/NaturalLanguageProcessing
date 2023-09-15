# Importar las librerías necesarias
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import spacy
import random
import nltk
from nltk.corpus import wordnet
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score

# Cargar el modelo de lenguaje español de SpaCy para la lematización
nlp = spacy.load('es_core_news_sm')

# Función para lematizar el texto
def lemmatize_text(text):
    doc = nlp(text)
    return " ".join([token.lemma_ for token in doc])

# Función para contar signos de puntuación
def count_punctuation(text):
    return sum(1 for char in text if char in '.,;:!?')

# Data Augmentation
nltk.download('wordnet')

def synonym_replacement(words):
    new_words = words.copy()
    random_word_list = list(set([word for word in words if word not in ['news', 'clickbait']]))
    random.shuffle(random_word_list)
    num_replaced = 0
    for random_word in random_word_list:
        synonyms = get_synonyms(random_word)
        if len(synonyms) >= 1:
            synonym = random.choice(list(synonyms))
            new_words = [synonym if word == random_word else word for word in new_words]
            num_replaced += 1
    if num_replaced >= 1:
        sentence = ' '.join(new_words)
        return sentence
    else:
        return None

def get_synonyms(word):
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonym = lemma.name().replace("_", " ").replace("-", " ").lower()
            synonym = "".join([char for char in synonym if char in ' qwertyuiopasdfghjklzxcvbnm'])
            synonyms.add(synonym)
    if word in synonyms:
        synonyms.remove(word)
    return list(synonyms)

# Paso 01 - Lectura del conjunto de información
df2 = pd.read_csv('DataSet para entrenamiento del modelo.csv')
df2.index = np.arange(1, len(df2) + 1)
print(df2.head(20))

# Paso 02 - Verificación y validación de la información
print("Tamaño del data frame: " + str(len(df2)))
print("Cantidad de filas vacías:")
print(df2.isnull().sum())
df2 = df2.dropna()
print("\nTamaño del data frame sin vacíos: " + str(len(df2)))
print("\nClases que tenemos en el DataSet:")
print(df2['label'].unique())
print("\nCantidad de ejemplos que tenemos por clase:")
print(df2['label'].value_counts())
Totales = df2['label'].value_counts()
plt.bar(['news', 'clickbait'], Totales)
plt.xticks(rotation = 45)
plt.title('Cantidad de ejemplos de cada clase')
plt.show()

# Feature Engineering
df2['title'] = df2['title'].apply(lemmatize_text)  # Lematización
df2['title_length'] = df2['title'].apply(len)
df2['word_count'] = df2['title'].apply(lambda x: len(x.split()))
df2['punctuation_count'] = df2['title'].apply(count_punctuation)  # Contar signos de puntuación

# Paso 05 - Construcción del modelo de NLP
X = df2['title']
Y = df2['label']
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size = 0.2)
clasificador_Texto = Pipeline([('tfidf', TfidfVectorizer()),('clf', LinearSVC())])
print(clasificador_Texto.get_params().keys())
clasificador_Texto.set_params(tfidf__lowercase=True, tfidf__stop_words=['de', 'para'], tfidf__max_features=None)

# Optimización del Modelo
param_grid = {
    'tfidf__max_df': [0.85, 0.9, 0.95],
    'tfidf__ngram_range': [(1, 1), (1, 2)],
    'clf__C': [0.1, 1, 10]
}
grid_search = GridSearchCV(clasificador_Texto, param_grid, cv=5)
grid_search.fit(X_train, Y_train)
best_clf = grid_search.best_estimator_
Predicciones = best_clf.predict(X_test)

# Matriz de confusión
print("Matriz de confusión:")
print(confusion_matrix(Y_test, Predicciones))
print("\nAccuracy del modelo: ")
print(accuracy_score(Y_test, Predicciones))
print("\nMétricas de evaluación:")
print(classification_report(Y_test, Predicciones, target_names=['news', 'clickbait']))
