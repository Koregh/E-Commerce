# Mini Loja - Projeto acadêmico (A3)

**E-commerce com autenticação segura, verificação em duas etapas e arquitetura em camadas.**

> Este é um projeto simples de estudo e não foi desenvolvido para uso em produção. Alguns aspectos que seriam necessários em um sistema real não estão totalmente implementados.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Redis](https://img.shields.io/badge/Redis-7.0+-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

---

## Funcionalidades

- Cadastro e login com hash de senha via **bcrypt**
- **Verificação em duas etapas (2FA)** por e-mail com código de 6 dígitos
- **Rate limiting** com backoff exponencial por e-mail — proteção contra brute force
- CRUD de produtos com ownership validation — só o dono edita/deleta
- Upload seguro de imagens com validação de extensão, tamanho e nome UUID
- Sessões persistidas no **Redis**
- Arquitetura em camadas com **SOLID** e injeção de dependência

---

## Instalação

**1. Clone o repositório**
```bash
git clone https://github.com/Koregh/E-Commerce.git
cd mini-loja
```

**2. Instale as dependências**
```bash
pip install -r requirements.txt
```

**3. Configure as variáveis de ambiente**
```bash
copy .env.example .env
```
Edite o `.env` com seus valores reais. Veja a seção [Configuração](#configuração).

**4. Inicie o Redis**
```bash
docker run -d -p 6379:6379 redis
```

**5. Inicialize o banco de dados**
```bash
python init_db.py
```

**6. Rode a aplicação**
```bash
python app.py
```

Acesse em `http://localhost:5000`

---

## Configuração

Copie `.env.example` para `.env` e preencha:

```dotenv
SECRET_KEY=          # gere com: python -c "import secrets; print(secrets.token_hex(32))"
DEBUG=false
ENV=production

DATABASE_URL=database.db

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

UPLOAD_FOLDER=static/images
MAX_UPLOAD_MB=5

# SMTP para envio do código 2FA
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=          # Senha de App — veja abaixo
SMTP_USE_TLS=true
```

> [!NOTE]
> Para Gmail, crie uma **Senha de App** em [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords). A verificação em duas etapas da conta precisa estar ativada.

---

## Arquitetura

```
mini-loja/
├── config/
│   └── settings.py          # Configurações centralizadas via env vars
├── core/
│   ├── database/
│   │   └── connection.py    # Context manager com commit/rollback automático
│   ├── exceptions/
│   │   └── domain.py        # Exceções tipadas (NotFoundError, ForbiddenError...)
│   └── security/
│       ├── password.py      # Interface + implementação bcrypt
│       └── upload.py        # Upload seguro com UUID e validação
├── models/
│   └── entities.py          # Dataclasses tipadas (Usuario, Produto)
├── repositories/            # Acesso ao banco — interfaces + SQLite
├── services/                # Regras de negócio com injeção de dependência
├── routes/                  # Blueprints Flask (auth, dashboard)
├── utils/
│   ├── validators.py        # Validadores puros sem side effects
│   └── mensagens.py         # Mensagens centralizadas com Enum
└── tests/
    └── test_services.py     # Testes unitários com mocks
```

---

## Fluxo de Login com 2FA

```
[1] Usuário envia e-mail + senha
        ↓
[2] Credenciais validadas (bcrypt)
        ↓
[3] Código de 6 dígitos gerado com secrets.randbelow()
    Armazenado no Redis com TTL de 10 minutos
    Enviado por e-mail via SMTP
        ↓
[4] Usuário insere o código na tela de verificação
        ↓
[5] Comparação com secrets.compare_digest() (timing-safe)
        ↓
[6] Sessão autenticada — código invalidado imediatamente
```

---

## Segurança

| Camada | Proteção |
|---|---|
| Senhas | bcrypt com salt automático |
| 2FA | Código gerado com `secrets`, comparado com `compare_digest` |
| Rate limiting | Backoff exponencial por e-mail, TTL de 1h no Redis |
| Upload | UUID como nome de arquivo, validação de extensão e tamanho |
| Ownership | Produto só editável/deletável pelo próprio dono |
| Sessão | HTTPOnly, SameSite=Lax, Secure em produção |
| Banco | FK constraints, CHECK constraints, WAL mode |

---

## Testes

```bash
pytest tests/ -v
```

```bash
pytest tests/ --cov=services --cov=utils --cov-report=term-missing
```

---

## Princípios aplicados

- **S**ingle Responsibility — cada classe tem uma responsabilidade
- **O**pen/Closed — novas implementações via interfaces, sem alterar código existente
- **L**iskov Substitution — qualquer `IPasswordHasher` funciona onde `BcryptPasswordHasher` é usado
- **I**nterface Segregation — interfaces pequenas e focadas
- **D**ependency Inversion — serviços recebem dependências pelo construtor, nunca instanciam

---

## Stack

- **Flask** — framework web
- **SQLite** — banco de dados
- **Redis** — sessões e rate limiting
- **bcrypt** — hash de senhas
- **flask-session** — sessões server-side
- **python-dotenv** — variáveis de ambiente
- **better-profanity** — filtro de conteúdo
- **pytest** — testes unitários
