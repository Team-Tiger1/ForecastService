import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer
from sklearn.pipeline import Pipeline

# Load the training dataset
df = pd.read_csv("dataset.csv")

# Split the columns into 3 categories based on the data within them
categorical_columns = ['weather', 'category', 'day']
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

def create_model_pipeline():
    """
    Creates an ML pipeline combining preprocessing with the classifier.
    :return: A scikit-learn Pipeline object that can be used by the forecast service endpoint to predict reservation and collection outcomes.
    """

    return Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', GradientBoostingClassifier(n_estimators=300, learning_rate=0.05, max_depth=4, random_state=42))
    ])

# Removes the targets from the input features
X = df.drop(['is_collected', 'is_reserved'], axis=1)

# Target variables
y_reserved = df['is_reserved']
y_collected = df['is_collected']

pipeline_reservation = create_model_pipeline()
pipeline_reservation.fit(X, y_reserved)

pipeline_collection = create_model_pipeline()
pipeline_collection.fit(X, y_collected)

# Saves the entire ML pipeline to a single file
joblib.dump(pipeline_reservation, 'pipeline_reservation.pkl')
joblib.dump(pipeline_collection, 'pipeline_collection.pkl')
print("Pipelines saved as 'pipeline_reservation.pkl' and 'pipeline_collection.pkl'")
