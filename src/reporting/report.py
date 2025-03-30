from datetime import datetime, timedelta
from src.database.database import get_db_connection
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from src.utils.config import get_openai_key, get_openai_model
from psycopg2.extras import DictCursor
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import schedule
import time
import os
import smtplib

# Function to generate e-mail weekly report
def generate_weekly_report():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    
    # Get data from the last 7 days
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    # Get sentiment summary
    cur.execute("""
        WITH sentiment_counts AS (
            SELECT COUNT(*) as total_decisive
            FROM feedbacks 
            WHERE created_at >= %s
            AND sentiment IN ('POSITIVO', 'NEGATIVO')
        )
        SELECT 
            sentiment, 
            COUNT(*) as count,
            CASE 
                WHEN sentiment IN ('POSITIVO', 'NEGATIVO') THEN
                    CAST((COUNT(*)::float * 100 / NULLIF((SELECT total_decisive FROM sentiment_counts), 0)) AS DECIMAL(5,1))
                ELSE NULL
            END as percentage
        FROM feedbacks 
        WHERE created_at >= %s
        GROUP BY sentiment
    """, (seven_days_ago, seven_days_ago))
    sentiment_data = cur.fetchall()
    
    # Get feature requests summary
    cur.execute("""
        SELECT feature_code, COUNT(*) as count 
        FROM feedbacks 
        WHERE created_at >= %s 
            AND feature_code IS NOT NULL 
        GROUP BY feature_code 
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
    sentiment_data_serializable = []
    for row in sentiment_data:
        row_dict = dict(row)
        # Convert Decimal to float for the percentage and count
        if 'percentage' in row_dict and row_dict['percentage'] is not None:
            row_dict['percentage'] = float(row_dict['percentage'])
        if 'count' in row_dict:
            row_dict['count'] = float(row_dict['count'])
        sentiment_data_serializable.append(row_dict)
    
    feature_data_serializable = []
    for row in feature_data:
        row_dict = dict(row)
        # Convert count to float
        if 'count' in row_dict:
            row_dict['count'] = float(row_dict['count'])
        feature_data_serializable.append(row_dict)
    
    # Prepare data for LLM with serializable values
    report_data = {
        'start_date': seven_days_ago.date().isoformat(),
        'end_date': datetime.now().date().isoformat(),
        'total_feedbacks': float(total_feedbacks),  # Convert to float
        'sentiment_summary': sentiment_data_serializable,
        'feature_requests': feature_data_serializable
    }
    
    cur.close()
    conn.close()
    
    prompt_template = """
    Você é um analista especializado em feedback de usuários da AluMind, uma startup que oferece um aplicativo focado em bem-estar e saúde mental.
    
    Analise os seguintes dados e preencha o template HTML abaixo com suas análises:
    
    Período: {start_date} até {end_date}
    Total de feedbacks: {total_feedbacks}
    
    Resumo de sentimentos:
    {sentiment_summary}
    
    Funcionalidades solicitadas:
    {feature_requests}
    
    Por favor, preencha o template HTML abaixo, seguindo estas diretrizes específicas:
    1. Na análise geral, inclua OBRIGATORIAMENTE:
       - O número total de feedbacks
       - A porcentagem exata de cada tipo de sentimento (Positivo, Negativo e Inconclusivo)
       - Uma análise da proporção entre feedbacks positivos e negativos
    2. Na análise de sentimentos, destaque:
       - Se houver feedbacks inconclusivos, analise possíveis razões para a ambiguidade
       - Como a distribuição dos sentimentos pode impactar as decisões do produto
    
    <html>
    <head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .positive {{
            color: #28a745;
        }}
        .negative {{
            color: #dc3545;
        }}
        .neutral {{
            color: #6c757d;
        }}
        .highlight {{
            background-color: #fff3cd;
            padding: 10px;
            border-radius: 5px;
        }}
        .metric {{
            font-size: 1.2em;
            font-weight: bold;
        }}
    </style>
    </head>
    <body>
    <div class="container">
        <div class="header">
            <h1>Relatório Semanal de Feedback - AluMind</h1>
            <p>Período: {start_date} a {end_date}</p>
            <p class="metric">Total de Feedbacks: {total_feedbacks}</p>
        </div>
        
        <div class="section">
            <h2>Análise Geral do Período</h2>
            <p>[Insira aqui um parágrafo detalhado com as porcentagens exatas de cada tipo de sentimento e a análise das proporções]</p>
        </div>
        
        <div class="section">
            <h2>Análise de Sentimentos</h2>
            <div class="highlight">
                [Insira aqui a análise detalhada dos sentimentos, usando as classes 'positive', 'negative' e 'neutral' para destacar os pontos relevantes. Inclua análise dos feedbacks inconclusivos.]
            </div>
        </div>
        
        <div class="section">
            <h2>Funcionalidades Mais Solicitadas</h2>
            <ul>
                [Insira aqui uma lista das funcionalidades mais solicitadas, com breve análise de cada uma. Use os dados de feature_code e suas contagens.]
            </ul>
        </div>
        
        <div class="section">
            <h2>Recomendações</h2>
            <ol>
                [Insira aqui 3-5 recomendações baseadas na análise dos dados, focando nas funcionalidades mais solicitadas e nos insights dos feedbacks inconclusivos]
            </ol>
        </div>
        
        <div class="section">
            <h2>Conclusão</h2>
            <p>[Insira aqui um parágrafo de conclusão com as principais ações sugeridas]</p>
        </div>
    </div>
    </body>
    </html>
    """
    
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["start_date", "end_date", "total_feedbacks", "sentiment_summary", "feature_requests"]
    )
    
    llm = ChatOpenAI(
        model=get_openai_model(),
        api_key=get_openai_key(),
        temperature=0.7
    )
    
    formatted_prompt = prompt.format(
        start_date=report_data['start_date'],
        end_date=report_data['end_date'],
        total_feedbacks=report_data['total_feedbacks'],
        sentiment_summary=json.dumps(report_data['sentiment_summary'], indent=2, ensure_ascii=False),
        feature_requests=json.dumps(report_data['feature_requests'], indent=2, ensure_ascii=False)
    )
    
    # Extract content from AIMessage
    report_html = llm.invoke(formatted_prompt).content
    
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