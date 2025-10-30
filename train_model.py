# train_model.py
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

texts = [
    "feliz alegre motivado", "contento emocionado", "triste cansado deprimido", 
    "estresado agobiado preocupado", "neutral tranquilo"
]
labels = ["positivo","positivo","negativo","negativo","neutro"]

vec = TfidfVectorizer()
X = vec.fit_transform(texts)
model = LogisticRegression(max_iter=1000)
model.fit(X, labels)

import os
os.makedirs("models", exist_ok=True)
pickle.dump(model, open("models/modelo_logistico.pkl", "wb"))
pickle.dump(vec, open("models/vectorizador.pkl", "wb"))
print("✅ Modelo creado correctamente")
