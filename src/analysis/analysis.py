from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import json
from src.utils.config import get_openai_key, get_openai_model

# Function to analyze feedback using LangChain
def analyze_feedback_langchain(feedback, id):
    prompt_template = """
    A AluMind é uma startup que oferece um aplicativo focado em bem-estar e saúde mental, 
    proporcionando aos usuários acesso a meditações guiadas, sessões de terapia, e conteúdos educativos sobre saúde mental.

    Você é um especialista em análise de feedback da AluMind e deve analisar o feedback do usuário e retornar a funcionalidade mais importante que o usuário está solicitando.

    Analise o seguinte feedback do aplicativo AluMind: "{feedback}"
    
    Identifique o sentimento como "POSITIVO", "NEGATIVO" ou "INCONCLUSIVO" (quando não for possível determinar claramente) e extraia a funcionalidade mais importante solicitada (caso exista).
    "feature_code" consiste em um código de até duas palavras escrito em letras maiusculas, que representa o que o cliente mais deseja.
    "feature_reason" consiste em uma frase curta e direta explicando o que o cliente deseja no código associado.
    
    Retorne a resposta no seguinte formato JSON:
    
    {{
      "id": "{id}",
      "sentiment": "<POSITIVO, NEGATIVO ou INCONCLUSIVO>",
      "feature_code": "<Código ou null se não houver solicitação>",
      "feature_reason": "<Motivo ou null se não houver solicitação>"
    }}
    """
    prompt = PromptTemplate(template=prompt_template, input_variables=["feedback", "id"])
    
    llm = ChatOpenAI(
        model=get_openai_model(),
        api_key=get_openai_key()
    )
    
    formatted_prompt = prompt.format(feedback=feedback, id=id)
    chain_result = llm.invoke(formatted_prompt)
    
    # Extract content from AIMessage before parsing JSON
    result = json.loads(chain_result.content)
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
    
    llm = ChatOpenAI(
        model=get_openai_model(),
        api_key=get_openai_key()
    )
    
    result = llm.invoke(prompt.format(feedback=feedback))
    # Extract the content from the AIMessage object
    result_text = result.content.strip()
    
    if result_text.upper() == "Y":
        return True
    else:
        return False