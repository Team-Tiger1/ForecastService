import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from matplotlib import pyplot as plt
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, ConfusionMatrixDisplay
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer
from sklearn.pipeline import Pipeline

from src.ml.train_model import y_reservation_balanced, y_collection_balanced

# Load the training dataset
df = pd.read_csv("dataset.csv")

# Splits the dataset into input variables and targets
X = df.drop(['is_collected', 'is_reserved'], axis=1)
y_reserved = df['is_reserved']
y_collected = df['is_collected']

# Splits the data into Training and Testing sets
X_train, X_test, y_reservation_train, y_reservation_test, y_collection_train, y_collection_test = train_test_split(X, y_reserved, y_collected, test_size=0.2, random_state=42)

# Split the columns into 3 categories based on the data within them
categorical_columns = ['weather', 'category', 'day', 'vendor_id']
skewed_columns = ['lead_time', 'window_length']
numerical_columns = ['price', 'temperature', 'time_of_day']

# OneHotEncoder to convert categorical data into binary vectors
categorical_pipeline = Pipeline([
    ('encoder', OneHotEncoder(sparse_output=False, handle_unknown='ignore'))
])

# Log transformation to compress the outliers
skewed_pipeline = Pipeline([
    ('log', FunctionTransformer(np.log1p, validate=False)),
    ('scaler', StandardScaler())
])

# Standard Scaler used for normal numerical inputs
numerical_pipeline = Pipeline([
    ('scaler', StandardScaler())
])

# Applies the specific pipelines to each category of data and then combines them into a single matrix
preprocessor = ColumnTransformer(transformers=[
    ('categorical', categorical_pipeline, categorical_columns),
    ('skewed', skewed_pipeline, skewed_columns),
    ('numerical', numerical_pipeline, numerical_columns)
], remainder='drop')

X_train_processed = preprocessor.fit_transform(X_train)
X_test_processed = preprocessor.transform(X_test)

smote = SMOTE(random_state=42)

def evaluate_model(X_train_processed, y_train, X_test_processed, y_test, model_name):
    """
    Evaluates model performance showing the accuracy and the Confusion Matrix of the model
    :param X_train_processed: Processed training data
    :param y_train: Target value
    :param X_test_processed: Processed testing data
    :param y_test: Target value
    :param model_name: Name of the model
    """
    print(f"Evaluating {model_name} Model")

    X_train_balanced, y_train_balanced = smote.fit_resample(X_train_processed, y_train)

    classifier = RandomForestClassifier(
        max_depth=None,
        max_features='log2',
        min_samples_split=2,
        n_estimators=300,
        random_state=42
    )
    classifier.fit(X_train_balanced, y_train_balanced)

    predictions = classifier.predict(X_test_processed)

    print(f"Accuracy: {accuracy_score(y_test, predictions):.4f}")

    cm = confusion_matrix(y_test, predictions)
    display = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['False', 'True'])
    display.plot(cmap=plt.cm.Blues)
    plt.title(f"Confusion Matrix: {model_name} Model")
    plt.show()

evaluate_model(X_train_processed, y_reservation_train, X_test_processed, y_reservation_test, "Reservation")
evaluate_model(X_train_processed, y_collection_train, X_test_processed, y_collection_test, "Collected")