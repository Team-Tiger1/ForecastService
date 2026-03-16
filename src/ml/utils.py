import numpy as np
from sentence_transformers import SentenceTransformer

embed_model = None


def embed_weather(X):
    """
    Converts a column of weather data to numeric vectors.
    :param X: Column of weather data.
    :return: Converted numeric vectors.
    """
    global embed_model

    # Only load the model once
    if embed_model is None:
        embed_model = SentenceTransformer('all-MiniLM-L6-v2')

    # Flatten input and convert to a list of strings
    weather_texts = np.ravel(X).tolist()
    return embed_model.encode(weather_texts)
