import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from matplotlib import pyplot as plt
from sklearn.compose import ColumnTransformer
from sklearn.metrics import accuracy_score, confusion_matrix, ConfusionMatrixDisplay
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer
from sklearn.pipeline import Pipeline

from src.ml.train_model import create_model_pipeline
from src.ml.utils import embed_weather


def evaluate_model(pipeline, X_test, y_test, model_name):
    """
    Evaluates model performance showing the accuracy and the Confusion Matrix of the model.
    :param pipeline: The model pipeline.
    :param X_test: Test input variables.
    :param y_test: Test target variables.
    :param model_name: Name of the model.
    """
    print(f"Evaluating {model_name} Model")

    predictions = pipeline.predict(X_test)

    print(f"Accuracy: {accuracy_score(y_test, predictions):.4f}")

    cm = confusion_matrix(y_test, predictions)
    display = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['False', 'True'])
    display.plot(cmap=plt.cm.Blues)
    plt.title(f"Confusion Matrix: {model_name} Model")
    plt.show()


def evaluate_models():
    print("Loading data")
    df = pd.read_csv('dataset.csv')

    # Splits the dataset into input variables and targets
    X = df.drop(['is_collected', 'is_reserved'], axis=1)
    y_reserved = df['is_reserved']
    y_collected = df['is_collected']

    # Splits the data into Training and Testing sets
    X_train, X_test, y_reservation_train, y_reservation_test, y_collection_train, y_collection_test = train_test_split(
        X, y_reserved, y_collected, test_size=0.2, random_state=42
    )

    # Split the columns into 4 categories based on the data within them
    weather_column = ['weather']
    categorical_columns = ['category', 'day', 'vendor_id']
    skewed_columns = ['lead_time', 'window_length']
    numerical_columns = ['discount', 'price', 'temperature', 'time_of_day']

    print("Building preprocessing pipelines")
    weather_pipeline = Pipeline([('embeder', FunctionTransformer(embed_weather, validate=False))])
    categorical_pipeline = Pipeline([('encoder', OneHotEncoder(sparse_output=False, handle_unknown='ignore'))])
    skewed_pipeline = Pipeline([('log', FunctionTransformer(np.log1p, validate=False)), ('scaler', StandardScaler())])
    numerical_pipeline = Pipeline([('scaler', StandardScaler())])

    preprocessor = ColumnTransformer(transformers=[
        ('weather', weather_pipeline, weather_column),
        ('categorical', categorical_pipeline, categorical_columns),
        ('skewed', skewed_pipeline, skewed_columns),
        ('numerical', numerical_pipeline, numerical_columns)
    ], remainder='drop')

    print("Preprocessing training data")
    X_train_processed = preprocessor.fit_transform(X_train)

    print("Balancing training data")
    smote = SMOTE(random_state=42)
    X_reservation_balanced, y_reservation_train_balanced = smote.fit_resample(X_train_processed, y_reservation_train)
    X_collection_balanced, y_collection_train_balanced = smote.fit_resample(X_train_processed, y_collection_train)

    print("Training models")
    pipeline_reservation = create_model_pipeline(preprocessor, X_reservation_balanced, y_reservation_train_balanced)
    pipeline_collection = create_model_pipeline(preprocessor, X_collection_balanced, y_collection_train_balanced)

    print("Running evaluations")
    evaluate_model(pipeline_reservation, X_test, y_reservation_test, "Reservation")
    evaluate_model(pipeline_collection, X_test, y_collection_test, "Collection")


# if __name__ == "__main__":
#     evaluate_models()