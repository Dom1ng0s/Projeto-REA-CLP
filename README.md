# 🚀 Nexos REA - Grupo Epsilon

O **Nexos REA** é um Motor de Recomendação de Recursos Educacionais Abertos (REAs) projetado para combater a sobrecarga de informação e otimizar a curadoria de conteúdos educacionais. Através de uma abordagem inteligente, o sistema filtra, avalia e recomenda REAs de forma personalizada para os usuários.

⚠️ **Status do Projeto:** `Em desenvolvimento` (Sprint 2)

---

## 🏗️ Arquitetura e Stack Tecnológica

O ecossistema do back-end foi desenhado seguindo uma **Arquitetura em Camadas (Layered Architecture)**, garantindo a separação clara de responsabilidades, testabilidade e escalabilidade:

* **Apresentação / Rotas:** Responsável por expor os endpoints da API e tratar as requisições HTTP.
* **Aplicação / Serviços:** Onde reside a lógica de negócio e as regras de orquestração do sistema.
* **Domínio / Modelos:** Definição das entidades de negócio e mapeamento relacional.
* **Infraestrutura:** Camada de persistência de dados, configurações de segurança e integrações externas.

### 🛠️ Stacks Utilizadas
* **Linguagem:** Python 3.10+
* **Framework Principal:** Flask
* **ORM (Persistência):** Flask-SQLAlchemy
* **Autenticação:** Flask-JWT-Extended (Tokens JWT)
* **Banco de Dados:** PostgreSQL / MySQL (Suporte a ambos via adapters)
* **Evolução Futura:** O ecossistema está preparado para se integrar a um servidor dedicado de Machine Learning e cálculo preditivo para refinar os scores de recomendação.

---

## 📋 Pré-requisitos

Antes de iniciar, certifique-se de ter instalado em sua máquina local:
* [Python 3.10 ou superior](https://www.python.org/downloads/)
* [Pip](https://pip.pypa.io/en/stable/installation/) (Gerenciador de pacotes do Python)
* Instância ativa do Banco de Dados (**PostgreSQL** ou **MySQL**)

---

## ⚙️ Configuração do Ambiente (Setup)

Siga os passos abaixo no seu terminal para clonar o repositório e preparar o ambiente de desenvolvimento local.

### 1. Clonar o Repositório

```

```text
File generated successfully.

```bash
git clone [https://github.com/grupo-epsilon/nexos-rea-backend.git](https://github.com/grupo-epsilon/nexos-rea-backend.git)
cd nexos-rea-backend

```

### 2. Criar e Ativar o Ambiente Virtual (venv)

No Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate

```

No Windows (Command Prompt):

```cmd
python -m venv venv
venv\Scripts\activate

```

### 3. Instalar as Dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt

```

### 4. Configurar as Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com base no arquivo de exemplo. Você precisará definir as credenciais do banco de dados local e a chave de criptografia do JWT.

```bash
cp .env.example .env

```

Exemplo de configuração interna do `.env`:

```env
FLASK_APP=src/app.py
FLASK_ENV=development
SECRET_KEY=sua_chave_secreta_aqui
JWT_SECRET_KEY=sua_chave_jwt_secreta_aqui
DATABASE_URL=postgresql://usuario:senha@localhost:5432/nexos_rea
# Caso use MySQL: mysql+pymysql://usuario:senha@localhost:3306/nexos_rea

```

---

## 🚀 Execução do Projeto

Com o ambiente devidamente configurado, execute os comandos a seguir para aplicar as migrações do banco de dados e iniciar o servidor Flask localmente.

### 1. Rodar as Migrações do Banco de Dados

```bash
flask db upgrade

```

### 2. Iniciar o Servidor Flask

```bash
flask run --host=0.0.0.0 --port=5000

```

O servidor estará disponível no endereço local: `http://localhost:5000`

---

## 📁 Estrutura de Pastas

A estrutura do projeto reflete rigorosamente a separação em camadas adotada pelo time de engenharia:

```text
nexos-rea-backend/
├── src/
│   ├── app.py                  # Ponto de entrada da aplicação (Factory Pattern)
│   ├── config.py               # Configurações globais de ambiente da aplicação
│   │
│   ├── presentation/           # Camada de Apresentação
│   │   └── routes/             # Blueprints do Flask e definições de Endpoints/Rotas
│   │
│   ├── application/            # Camada de Aplicação
│   │   └── services/           # Lógica de negócio pura e regras de uso do sistema
│   │
│   ├── domain/                 # Camada de Domínio
│   │   └── models/             # Entidades de dados mapeadas pelo SQLAlchemy
│   │
│   └── infrastructure/         # Camada de Infraestrutura
│       ├── database.py         # Inicialização do banco de dados e ORM
│       └── core/
│           └── auth/           # Configurações e interceptores do JWT-Extended
│
├── migrations/                 # Scripts de migração de banco de dados (Alembic)
├── .env.example                # Modelo de variáveis de ambiente obrigatórias
├── README.md                   # Documentação do projeto
└── requirements.txt            # Manifesto de dependências do Python

```

---

## 📑 Diretrizes de Integração (Para o Front-end)

* **URL Base:** Todas as requisições locais devem ser apontadas para `http://localhost:5000/api/v1`.
* **Autenticação:** Endpoints protegidos exigem o Header `Authorization: Bearer <seu_token_jwt>`. O token é obtido através da rota de login na camada de apresentação.
* **CORS:** O mecanismo de CORS está habilitado para permitir requisições vindas da origem padrão do React (`http://localhost:3000`).
"""

with open("README.md", "w", encoding="utf-8") as f:
f.write(readme_content)

print("File generated successfully.")

```
Your Markdown file is ready
[file-tag: code-generated-file-0-1779296593998723772]

```markdown
# 🚀 Nexos REA - Grupo Epsilon

O **Nexos REA** é um Motor de Recomendação de Recursos Educacionais Abertos (REAs) projetado para combater a sobrecarga de informação e otimizar a curadoria de conteúdos educacionais. Através de uma abordagem inteligente, o sistema filtra, avalia e recomenda REAs de forma personalizada para os usuários.

⚠️ **Status do Projeto:** `Em desenvolvimento` (Sprint 2)

---

## 🏗️ Arquitetura e Stack Tecnológica

O ecossistema do back-end foi desenhado seguindo uma **Arquitetura em Camadas (Layered Architecture)**, garantindo a separação clara de responsabilidades, testabilidade e escalabilidade:

* **Apresentação / Rotas:** Responsável por expor os endpoints da API e tratar as requisições HTTP.
* **Aplicação / Serviços:** Onde reside a lógica de negócio e as regras de orquestração do sistema.
* **Domínio / Modelos:** Definição das entidades de negócio e mapeamento relacional.
* **Infraestrutura:** Camada de persistência de dados, configurações de segurança e integrações externas.

### 🛠️ Stacks Utilizadas
* **Linguagem:** Python 3.10+
* **Framework Principal:** Flask
* **ORM (Persistência):** Flask-SQLAlchemy
* **Autenticação:** Flask-JWT-Extended (Tokens JWT)
* **Banco de Dados:** PostgreSQL / MySQL (Suporte a ambos via adapters)
* **Evolução Futura:** O ecossistema está preparado para se integrar a um servidor dedicado de Machine Learning e cálculo preditivo para refinar os scores de recomendação.

---

## 📋 Pré-requisitos

Antes de iniciar, certifique-se de ter instalado em sua máquina local:
* [Python 3.10 ou superior](https://www.python.org/downloads/)
* [Pip](https://pip.pypa.io/en/stable/installation/) (Gerenciador de pacotes do Python)
* Instância ativa do Banco de Dados (**PostgreSQL** ou **MySQL**)

---

## ⚙️ Configuração do Ambiente (Setup)

Siga os passos abaixo no seu terminal para clonar o repositório e preparar o ambiente de desenvolvimento local.

### 1. Clonar o Repositório
```bash
git clone [https://github.com/grupo-epsilon/nexos-rea-backend.git](https://github.com/grupo-epsilon/nexos-rea-backend.git)
cd nexos-rea-backend

```

### 2. Criar e Ativar o Ambiente Virtual (venv)

No Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate

```

No Windows (Command Prompt):

```cmd
python -m venv venv
venv\Scripts\activate

```

### 3. Instalar as Dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt

```

### 4. Configurar as Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com base no arquivo de exemplo. Você precisará definir as credenciais do banco de dados local e a chave de criptografia do JWT.

```bash
cp .env.example .env

```

Exemplo de configuração interna do `.env`:

```env
FLASK_APP=src/app.py
FLASK_ENV=development
SECRET_KEY=sua_chave_secreta_aqui
JWT_SECRET_KEY=sua_chave_jwt_secreta_aqui
DATABASE_URL=postgresql://usuario:senha@localhost:5432/nexos_rea
# Caso use MySQL: mysql+pymysql://usuario:senha@localhost:3306/nexos_rea

```

---

## 🚀 Execução do Projeto

Com o ambiente devidamente configurado, execute os comandos a seguir para aplicar as migrações do banco de dados e iniciar o servidor Flask localmente.

### 1. Rodar as Migrações do Banco de Dados

```bash
flask db upgrade

```

### 2. Iniciar o Servidor Flask

```bash
flask run --host=0.0.0.0 --port=5000

```

O servidor estará disponível no endereço local: `http://localhost:5000`

---

## 📁 Estrutura de Pastas

A estrutura do projeto reflete rigorosamente a separação em camadas adotada pelo time de engenharia:

```text
nexos-rea-backend/
├── src/
│   ├── app.py                  # Ponto de entrada da aplicação (Factory Pattern)
│   ├── config.py               # Configurações globais de ambiente da aplicação
│   │
│   ├── presentation/           # Camada de Apresentação
│   │   └── routes/             # Blueprints do Flask e definições de Endpoints/Rotas
│   │
│   ├── application/            # Camada de Aplicação
│   │   └── services/           # Lógica de negócio pura e regras de uso do sistema
│   │
│   ├── domain/                 # Camada de Domínio
│   │   └── models/             # Entidades de dados mapeadas pelo SQLAlchemy
│   │
│   └── infrastructure/         # Camada de Infraestrutura
│       ├── database.py         # Inicialização do banco de dados e ORM
│       └── core/
│           └── auth/           # Configurações e interceptores do JWT-Extended
│
├── migrations/                 # Scripts de migração de banco de dados (Alembic)
├── .env.example                # Modelo de variáveis de ambiente obrigatórias
├── README.md                   # Documentação do projeto
└── requirements.txt            # Manifesto de dependências do Python

```

---

## 📑 Diretrizes de Integração (Para o Front-end)

* **URL Base:** Todas as requisições locais devem ser apontadas para `http://localhost:5000/api/v1`.
* **Autenticação:** Endpoints protegidos exigem o Header `Authorization: Bearer <seu_token_jwt>`. O token é obtido através da rota de login na camada de apresentação.
* **CORS:** O mecanismo de CORS está habilitado para permitir requisições vindas da origem padrão do React (`http://localhost:3000`).
