from dotenv import load_dotenv
import os
import hashlib
import time

# Load environment from .env and check for secret key
load_dotenv()
if not os.getenv('SECRET_KEY'):
    current_time = str(time.time()) + str(time.time_ns())
    secret_key = hashlib.sha256(current_time.encode()).hexdigest()
    with open('.env', 'a') as env_file:
        env_file.write(f"\nSECRET_KEY={secret_key}")


class Config:   # Configure database with app
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')
    SECRET_KEY = os.getenv('SECRET_KEY')
