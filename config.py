import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@95.216.215.24:5432/condoflow_teste'
    SQLALCHEMY_TRACK_MODIFICATIONS = False