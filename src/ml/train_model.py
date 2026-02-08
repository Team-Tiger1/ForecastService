import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer
from sklearn.pipeline import Pipeline

df = pd.read_csv("dataset.csv")
categorical_columns = ['weather', 'category', 'day']
skewed_columns = ['lead_time', 'window_length']
numerical_columns = ['price', 'temperature', 'time_of_day']

categorical_pipeline = Pipeline([
    ('encoder', OneHotEncoder(sparse_output=False, handle_unknown='ignore'))
])

skewed_pipeline = Pipeline([
    ('log', FunctionTransformer(np.log1p, validate=False)),
    ('scaler', StandardScaler())
])

numerical_pipeline = Pipeline([
    ('scaler', StandardScaler())
])

preprocessor = ColumnTransformer(transformers=[
    ('categorical', categorical_pipeline, categorical_columns),
    ('skewed', skewed_pipeline, skewed_columns),
    ('numerical', numerical_pipeline, numerical_columns)
], remainder='drop')

def create_model_pipeline():
    return Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', GradientBoostingClassifier(n_estimators=300, learning_rate=0.05, max_depth=4, random_state=42))
    ])

X = df.drop(['is_collected', 'is_reserved'], axis=1)
y_reserved = df['is_reserved']
y_collected = df['is_collected']

pipeline_reservation = create_model_pipeline()
pipeline_reservation.fit(X, y_reserved)

pipeline_collection = create_model_pipeline()
pipeline_collection.fit(X, y_collected)

joblib.dump(pipeline_reservation, 'pipeline_reservation.pkl')
joblib.dump(pipeline_collection, 'pipeline_collection.pkl')
print("Pipelines saved as 'pipeline_reservation.pkl' and 'pipeline_collection.pkl'")
