from langchain_community.llms import OpenAI
from langchain.prompts import PromptTemplate
import os
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
openai_api_key = os.getenv("OPENAI_API_KEY")

# Function to analyze feedback using LangChain
def analyze_feedback_langchain(feedback, id):
    prompt_template = """
    A AluMind é uma startup que oferece um aplicativo focado em bem-estar e saúde mental, 
    proporcionando aos usuários acesso a meditações guiadas, sessões de terapia, e conteúdos educativos sobre saúde mental.

    Você é um especialista em análise de feedback da AluMind e deve analisar o feedback do usuário e retornar uma lista de funcionalidades que o usuário está solicitando.

    Analise o seguinte feedback do aplicativo AluMind: "{feedback}"
    
    Identifique o sentimento como "POSITIVO" ou "NEGATIVO" e extraia as funcionalidades solicitadas (caso existam), 
    retornando uma lista de objetos com "code" e "reason". Retorne a resposta no seguinte formato JSON:
    
    {{
      "id": "{id}",
      "sentiment": "<POSITIVO ou NEGATIVO>",
      "requested_features": [
        {{
          "code": "<Código>",
          "reason": "<Motivo>"
        }}
      ]
    }}
    Se não houver funcionalidades solicitadas, "requested_features" deve ser uma lista vazia.
    """
    prompt = PromptTemplate(template=prompt_template, input_variables=["feedback", "id"])
    
    llm = OpenAI(model_name="gpt-3.5-turbo", openai_api_key=openai_api_key)
    
    formatted_prompt = prompt.format(feedback=feedback, id=id)
    chain_result = llm(formatted_prompt)
    
    result = json.loads(chain_result)
    return result

# Function to filter spam feedback
def spam_filter(feedback: str) -> bool:
    prompt_template = """
    A AluMind é uma startup que oferece um aplicativo focado em bem-estar e saúde mental, 
    proporcionando aos usuários acesso a meditações guiadas, sessões de terapia, e conteúdos educativos sobre saúde mental.

    Você é um assistente de análise de feedbacks da AluMind. Sua tarefa é avaliar o seguinte feedback de usuário e determinar se ele é válido, ou seja, se é coerente, construtivo e relevante. 
    
    Se o feedback for válido, responda apenas com a letra "Y". 
    Se o feedback for considerado spam, irrelevante ou inválido, responda apenas com a letra "N".
    
    Feedback: "{feedback}"
    """
    prompt = PromptTemplate(template=prompt_template, input_variables=["feedback"])
    
    llm = OpenAI(model_name="gpt-3.5-turbo", openai_api_key=openai_api_key)
    
    result = llm(prompt.format(feedback=feedback)).strip()
    
    if result.upper() == "Y":
        return True
    else:
        return False
    
# Database connection    
def get_db_connection():
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432')
    )
    return conn

# Initialize the database
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # Create feedbacks table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS feedbacks (
        id TEXT PRIMARY KEY,
        feedback TEXT NOT NULL,
        sentiment TEXT CHECK (sentiment IN ('POSITIVO', 'NEGATIVO')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create requested_features table first (referenced by feedbacks)
    cur.execute('''
    CREATE TABLE IF NOT EXISTS requested_features (
        id SERIAL PRIMARY KEY,
        feedback_id TEXT,
        feature_code TEXT NOT NULL,
        reason TEXT NOT NULL,
        FOREIGN KEY (feedback_id) REFERENCES feedbacks(id)
    )
    ''')
    conn.commit()
    cur.close()
    conn.close()