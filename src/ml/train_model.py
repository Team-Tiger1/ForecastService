import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from sentence_transformers import SentenceTransformer
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer
from sklearn.pipeline import Pipeline

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


def create_model_pipeline(preprocessor, X, y):
    """
    Creates pipeline by combining preprocessing with the trained classifier.
    :param preprocessor: Preprocessor object.
    :param X: Input variables.
    :param y: The target variable.
    :return: The pipeline object.
    """
    classifier = RandomForestClassifier(
        max_depth=None,
        max_features='log2',
        min_samples_split=2,
        n_estimators=300,
        random_state=42
    )

    classifier.fit(X, y)

    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', classifier)
    ])

    return pipeline


if __name__ == "__main__":
    print("Loading data")
    df = pd.read_csv('dataset.csv')

    # Split the columns into 4 categories based on the data within them
    weather_column = ['weather']
    categorical_columns = ['category', 'day', 'vendor_id']
    skewed_columns = ['lead_time', 'window_length']
    numerical_columns = ['discount', 'price', 'temperature', 'time_of_day']

    print("Building preprocessing pipelines")
    # embed_weather to convert weather into numerical vectors
    weather_pipeline = Pipeline([('embeder', FunctionTransformer(embed_weather, validate=False))])

    # OneHotEncoder to convert categorical data into binary vectors
    categorical_pipeline = Pipeline([('encoder', OneHotEncoder(sparse_output=False, handle_unknown='ignore'))])

    # Log transformation to compress the outliers
    skewed_pipeline = Pipeline([('log', FunctionTransformer(np.log1p, validate=False)), ('scaler', StandardScaler())])

    # Standard Scaler used for normal numerical inputs
    numerical_pipeline = Pipeline([('scaler', StandardScaler())])
    # Applies the specific pipelines to each category of data and then combines them into a single matrix
    preprocessor = ColumnTransformer(transformers=[
        ('weather', weather_pipeline, weather_column),
        ('categorical', categorical_pipeline, categorical_columns),
        ('skewed', skewed_pipeline, skewed_columns),
        ('numerical', numerical_pipeline, numerical_columns)
    ], remainder='drop')

    print("Preprocessing data")
    X = df.drop(['is_collected', 'is_reserved'], axis=1)

    X_processed = preprocessor.fit_transform(X)

    print("Balancing data")
    smote = SMOTE(random_state=42)
    X_reservation_balanced, y_reservation_balanced = smote.fit_resample(X_processed, df['is_reserved'])
    X_collection_balanced, y_collection_balanced = smote.fit_resample(X_processed, df['is_collected'])

    print("Training models")
    pipeline_reservation = create_model_pipeline(preprocessor, X_reservation_balanced, y_reservation_balanced)
    pipeline_collection = create_model_pipeline(preprocessor, X_collection_balanced, y_collection_balanced)

    print("Saving models")
    # Models must be compressed due to their large size
    joblib.dump(pipeline_reservation, 'pipeline_reservation.pkl', compress=3)
    joblib.dump(pipeline_collection, 'pipeline_collection.pkl', compress=3)

    print("Models trained and saved")
