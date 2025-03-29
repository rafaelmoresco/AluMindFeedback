from langchain_community.llms import OpenAI
from langchain.prompts import PromptTemplate
import os
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule
import time

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

# Function to generate e-mail weekly report
def generate_weekly_report():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    
    # Get data from the last 7 days
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    # Get sentiment summary
    cur.execute("""
        SELECT sentiment, COUNT(*) as count 
        FROM feedbacks 
        WHERE created_at >= %s 
        GROUP BY sentiment
    """, (seven_days_ago,))
    sentiment_data = cur.fetchall()
    
    # Get feature requests summary
    cur.execute("""
        SELECT rf.feature_code, COUNT(*) as count 
        FROM requested_features rf
        JOIN feedbacks f ON rf.feedback_id = f.id 
        WHERE f.created_at >= %s 
        GROUP BY rf.feature_code 
        ORDER BY count DESC
    """, (seven_days_ago,))
    feature_data = cur.fetchall()
    
    # Get total feedback count
    cur.execute("""
        SELECT COUNT(*) as total
        FROM feedbacks
        WHERE created_at >= %s
    """, (seven_days_ago,))
    total_feedbacks = cur.fetchone()['total']
    
    # Prepare data for LLM
    report_data = {
        'start_date': seven_days_ago.date().isoformat(),
        'end_date': datetime.now().date().isoformat(),
        'total_feedbacks': total_feedbacks,
        'sentiment_summary': [dict(row) for row in sentiment_data],
        'feature_requests': [dict(row) for row in feature_data]
    }
    
    cur.close()
    conn.close()
    
    prompt_template = """
    Você é um analista especializado em feedback de usuários da AluMind, uma startup que oferece um aplicativo focado em bem-estar e saúde mental.
    
    Gere um relatório semanal em formato HTML baseado nos seguintes dados:
    
    Período: {start_date} até {end_date}
    Total de feedbacks: {total_feedbacks}
    
    Resumo de sentimentos:
    {sentiment_summary}
    
    Funcionalidades mais solicitadas:
    {feature_requests}
    
    Por favor, gere um relatório profissional que inclua:
    1. Uma análise geral do período
    2. Insights sobre os sentimentos dos usuários
    3. Recomendações baseadas nas funcionalidades mais solicitadas
    4. Conclusões e sugestões de ações
    
    O relatório deve ser formatado em HTML com estilos CSS embutidos para uma boa apresentação no email.
    Use cores apropriadas para destacar pontos positivos (verde) e negativos (vermelho).
    Inclua gráficos textuais (ASCII/Unicode) se apropriado.
    """
    
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["start_date", "end_date", "total_feedbacks", "sentiment_summary", "feature_requests"]
    )
    
    llm = OpenAI(
        model_name="gpt-3.5-turbo",
        openai_api_key=openai_api_key,
        temperature=0.7  # Add some creativity to the report
    )
    
    formatted_prompt = prompt.format(
        start_date=report_data['start_date'],
        end_date=report_data['end_date'],
        total_feedbacks=report_data['total_feedbacks'],
        sentiment_summary=json.dumps(report_data['sentiment_summary'], indent=2, ensure_ascii=False),
        feature_requests=json.dumps(report_data['feature_requests'], indent=2, ensure_ascii=False)
    )
    
    report_html = llm(formatted_prompt)
    
    return report_html

# Function to send the report
def send_email_report(report_html):
    sender_email = os.getenv('EMAIL_SENDER')
    sender_password = os.getenv('EMAIL_PASSWORD')
    receiver_email = os.getenv('SUPPORT_EMAIL')
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'Weekly Feedback Report - {datetime.now().date()}'
    msg['From'] = sender_email
    msg['To'] = receiver_email
    
    msg.attach(MIMEText(report_html, 'html'))
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("Weekly report sent successfully")
    except Exception as e:
        print(f"Error sending email: {str(e)}")

# Scheduler function
def schedule_weekly_report():
    def send_report():
        report_html = generate_weekly_report()
        send_email_report(report_html)
    
    # Schedule the report to run every Monday at 9:00 AM
    schedule.every().monday.at("09:00").do(send_report)
    
    while True:
        schedule.run_pending()
        time.sleep(60)