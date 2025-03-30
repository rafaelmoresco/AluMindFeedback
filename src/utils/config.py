import os
from dotenv import load_dotenv

def load_config():
    load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

def get_openai_key():
    return os.getenv("OPENAI_API_KEY")

def get_openai_model():
    return os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-0125")