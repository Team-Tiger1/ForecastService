import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer
from sklearn.pipeline import Pipeline

# Load the training dataset
df = pd.read_csv("dataset.csv")

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

X = df.drop(['is_collected', 'is_reserved'], axis=1)
X_processed = preprocessor.fit_transform(X)
smote = SMOTE(random_state=42)

def create_model_pipeline(X_balanced, y_balanced):
    """
    Creates an ML pipeline combining preprocessing with the classifier.
    :param X_balanced: Balanced input variables X.
    :param y_balanced: Balanced target variable y.
    :return: Pipeline object.
    """

    classifier = RandomForestClassifier(
        max_depth=None,
        max_features='log2',
        min_samples_split=2,
        n_estimators=300,
        random_state=42
    )
    classifier.fit(X_balanced, y_balanced)

    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', classifier)
    ])

    return pipeline

# Balances the dataset
X_reservation_balanced, y_reservation_balanced = smote.fit_resample(X_processed, df['is_reserved'])
X_collection_balanced, y_collection_balanced = smote.fit_resample(X_processed, df['is_collected'])

# Create and train the models
pipeline_reservation = create_model_pipeline(X_reservation_balanced, y_reservation_balanced)
pipeline_collection = create_model_pipeline(X_collection_balanced, y_collection_balanced)

# Saves the models to .pkl files
joblib.dump(pipeline_reservation, 'pipeline_reservation.pkl')
joblib.dump(pipeline_collection, 'pipeline_collection.pkl')