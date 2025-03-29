from datetime import datetime, timedelta
from src.database.database import get_db_connection
from langchain_community.llms import OpenAI
from langchain.prompts import PromptTemplate
from src.utils.config import get_openai_key
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
        openai_api_key=get_openai_key(),
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