# Arquithon, o Arquivista em python

Aplicação web feita em **Python + Flask** que organiza arquivos automaticamente por tipo (imagens, documentos, planilhas, compactados, etc.), com login individual por usuário. A ideia do projeto é evoluir para um **arquivista pessoal, 100% offline**, que roda localmente na sua máquina sem depender de internet ou de serviços em nuvem.

## Funcionalidades atuais

- Login e cadastro de usuários (senha com hash, via `werkzeug.security`)
- Upload de múltiplos arquivos de uma vez
- Organização automática por extensão em subpastas (`imagens/png`, `documentos/pdf`, `multimedia/audio`, etc.)
- Pasta de upload isolada por usuário (`uploads/<id_do_usuario>/...`)
- Painel web listando os arquivos já organizados por categoria

## Stack

- [Flask](https://flask.palletsprojects.com/) — servidor web (back-end)
- [Flask-Login](https://flask-login.readthedocs.io/) — autenticação de sessão
- [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/) — ORM / banco de dados
- SQLite — banco de dados local (padrão)
- Jinja2 + [water.css](https://watercss.kognise.dev/) — templates e estilo (front-end)

## Como rodar localmente

1. Crie e ative um ambiente virtual:

   ```bash
   python -m venv venv
   venv\Scripts\activate      # Windows
   ```

2. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

3. Rode a aplicação:

   ```bash
   python app.py
   ```

4. Acesse **http://127.0.0.1:5000** no navegador, crie uma conta e comece a enviar arquivos.

> O banco de dados SQLite (`arquivista.db`) é criado automaticamente na primeira execução.

## Estrutura do projeto

```
arquithon/
├── app.py              # rotas, autenticação e lógica de organização (back-end)
├── requirements.txt    # dependências Python
├── templates/           # páginas HTML (front-end)
│   ├── index.html
│   ├── login.html
│   └── register.html
└── uploads/             # arquivos organizados por usuário (criado em tempo de execução)
```

## Status do projeto

O código atual já inclui configuração para deploy em nuvem (Render + PostgreSQL). O objetivo é reorganizar o projeto para priorizar o **uso local/offline** como modo principal, mantendo o deploy em nuvem como opção secundária. Detalhes em [MELHORIAS.md](MELHORIAS.md).
