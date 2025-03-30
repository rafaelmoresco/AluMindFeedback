# AluMindFeedback

## Sobre o Projeto

A AluMind é uma startup que oferece um aplicativo focado em bem-estar e saúde mental, proporcionando aos usuários acesso a meditações guiadas, sessões de terapia e conteúdos educativos sobre saúde mental. Este projeto é um protótipo de uma aplicação web que analisa feedbacks de usuários, classifica-os por sentimento e elenca possíveis melhorias.

## Funcionalidades

### Requisitos Funcionais

1. **Classificação de Feedbacks**:
   - Endpoint para receber feedbacks e classificá-los como "POSITIVO", "NEGATIVO" ou "INCONCLUSIVO".
   - Cada feedback deve incluir um identificador único e um texto.
   - Resposta deve incluir o sentimento e funcionalidades sugeridas com códigos e razões.

2. **Relatório de Feedbacks**:
   - Página web que fornece um relatório dos feedbacks recebidos.
   - Exibir porcentagem de feedbacks positivos em relação aos demais.
   - Listar as funcionalidades mais pedidas.

3. **Resumo Semanal**:
   - Envio de um email semanal com um resumo dos feedbacks.
   - Incluir porcentagens de feedbacks positivos e negativos, além das principais funcionalidades pedidas.

4. **Sistema de Filtragem (Bônus)**:
   - Implementação de um sistema que assegure que apenas feedbacks legítimos sejam processados.

### Requisitos Não Funcionais

- **Tecnologias**:
  - Python
  - Flask
  - PostgreSQL
  - LangChain OpenAI
  - Git & GitHub

- **Desempenho**:
  - A aplicação deve ser capaz de processar feedbacks em tempo real.
  - O relatório deve ser gerado e enviado semanalmente sem atrasos significativos.

- **Usabilidade**:
  - A interface deve ser intuitiva e fácil de usar, permitindo que os usuários visualizem feedbacks e relatórios de forma clara.

- **Segurança**:
  - Embora a autenticação não seja uma prioridade, a aplicação deve garantir que apenas feedbacks válidos sejam processados.

## Endpoints da API

### 1. Criar Feedback

- **Endpoint**: `/feedbacks`
- **Método**: `POST`
- **Descrição**: Recebe um feedback e classifica-o.
- **Requisição**:
  ```json
  {
    "id": "4042f20a-45f4-4647-8050-139ac16f610b",
    "feedback": "Gosto muito de usar o Alumind! Está me ajudando bastante em relação a alguns problemas que tenho. Só queria que houvesse uma forma mais fácil de eu mesmo realizar a edição do meu perfil dentro da minha conta."
  }
  ```
- **Resposta**:
  ```json
  {
    "id": "4042f20a-45f4-4647-8050-139ac16f610b",
    "sentiment": "POSITIVO",
    "requested_features": [
      {
        "code": "EDITAR_PERFIL",
        "reason": "O usuário gostaria de realizar a edição do próprio perfil"
      }
    ]
  }
  ```

### 2. Verificar Saúde da API

- **Endpoint**: `/health`
- **Método**: `GET`
- **Descrição**: Verifica se a API está funcionando.
- **Resposta**:
  ```json
  {
    "status": "ok"
  }
  ```

### 3. Dashboard

- **Endpoint**: `/dashboard`
- **Método**: `GET`
- **Descrição**: Retorna um relatório dos feedbacks recebidos, incluindo contagem total, distribuição de sentimentos e funcionalidades mais pedidas.
- **Resposta**: Renderiza a página HTML com os dados do dashboard.

### 4. Página de Submissão de Feedback

- **Endpoint**: `/submit`
- **Método**: `GET`
- **Descrição**: Renderiza a página para submissão de novos feedbacks.

## Detalhes da Implementação

### Configuração do Banco de Dados

A aplicação utiliza o PostgreSQL como sistema de gerenciamento de banco de dados. A tabela `feedbacks` é configurada com as seguintes colunas:

- **id**: Identificador único do feedback (tipo TEXT, chave primária).
- **feedback**: Texto do feedback fornecido pelo usuário (tipo TEXT, não nulo).
- **sentiment**: Resultado da análise de sentimento, que pode ser "POSITIVO", "NEGATIVO" ou "INCONCLUSIVO" (tipo TEXT, com restrição CHECK).
- **feature_code**: Código que representa a funcionalidade solicitada (tipo TEXT, opcional).
- **feature_reason**: Descrição da razão pela qual a funcionalidade é importante (tipo TEXT, opcional).
- **created_at**: Timestamp que registra quando o feedback foi criado (tipo TIMESTAMP, padrão para o horário atual).

A tabela é criada com a seguinte instrução SQL:

```sql
CREATE TABLE IF NOT EXISTS feedbacks (
    id TEXT PRIMARY KEY,
    feedback TEXT NOT NULL,
    sentiment TEXT CHECK (sentiment IN ('POSITIVO', 'NEGATIVO', 'INCONCLUSIVO')),
    feature_code TEXT,
    feature_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Estrutura do Código

- **api.py**: Contém a lógica principal da aplicação, incluindo a definição dos endpoints e a manipulação de feedbacks.
- **database.py**: Centraliza todas as operações de acesso ao banco de dados, facilitando a manutenção e a escalabilidade.
- **report.py**: Gera relatórios semanais com base nos feedbacks recebidos e envia por e-mail para os stakeholders.
- **analysis.py**: Implementa a lógica de análise de feedbacks utilizando modelos de linguagem (LLMs).
- **config.py**: Extrai as variaveis de ambiente para a aplicação.

## Instalação

Para instalar e executar a aplicação, siga os passos abaixo:

1. **Clone o repositório**:
   ```bash
   git clone https://github.com/rafaelmoresco/AluMindFeedback.git
   cd AluMindFeedback
   ```

2. **Crie um ambiente virtual** (opcional, mas recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Para Linux/Mac
   venv\Scripts\activate  # Para Windows
   ```

3. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as variáveis de ambiente**:
   Crie um arquivo `.env` na raiz do projeto e adicione as seguintes variáveis:
   ```plaintext
   DB_NAME=alumind
   DB_USER=admin
   DB_PASSWORD=temp123
   DB_HOST=localhost
   DB_PORT=5432
   OPENAI_API_KEY=sua_chave
   OPENAI_MODEL=modelo_desejado
   EMAIL_SENDER=seu_email@gmail.com
   EMAIL_PASSWORD=sua_senha
   SUPPORT_EMAIL=email_destinatario@gmail.com
   ```

5. **Configure o banco de dados**:
   Execute o script SQL para criar o banco de dados e a tabela de feedbacks:
   ```bash
   psql -U admin -h localhost -f sql_scripts/setup_database.sql
   ```
   Caso deseje popular o banco de dados com alguns exemplos, execute o seguinte script:
   ```bash
   psql -U admin -h localhost -f sql_scripts/populate.sql
   ```

6. **Execute a aplicação**:
   ```bash
   python api.py
   ```

7. **Acesse a aplicação**:
   Abra seu navegador e vá para `http://127.0.0.1:5000/dashboard`.
