from langchain_community.llms import OpenAI
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()
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