# Pontos de melhoria — Arquithon

Este documento reúne o que foi observado no código atual e ideias para transformar o projeto em um arquivista pessoal totalmente offline, com uma experiência de uso melhor em Python.

## 1. Tornar o sistema realmente offline

Hoje o projeto está configurado para deploy em nuvem (Render + PostgreSQL) e o front-end carrega o CSS (`water.css`) via CDN — ou seja, sem internet o visual quebra.

- Vendorizar o `water.css` (ou outro CSS) localmente em `static/`, em vez de puxar de CDN.
- Deixar o SQLite como banco padrão sempre, mantendo o suporte a Postgres/Render como opção *extra*, não como caminho principal.
- Abrir o navegador automaticamente na página local ao iniciar (`webbrowser.open("http://127.0.0.1:5000")`), para não depender do usuário digitar a URL.
- Empacotar como aplicativo desktop, para rodar com duplo clique, sem terminal:
  - **pywebview**: abre a interface Flask dentro de uma janela nativa (sem navegador visível).
  - **PyInstaller**: gera um `.exe` único para Windows, com tudo embutido.

## 2. Separar front-end e back-end de forma mais clara

Você mencionou querer usar "uma página que permita o uso de front ou o uso de back". Hoje as duas coisas estão acopladas: as rotas do Flask devolvem HTML pronto (Jinja).

- Expor uma API JSON simples no back-end (`/api/arquivos`, `/api/upload`, etc.), separada das rotas que renderizam páginas.
- O front-end atual (Jinja + water.css) passa a ser só *um* consumidor dessa API — no futuro dá para trocar por outro front (outro framework, um app desktop, etc.) sem mexer no back.
- Isso também facilita usar o Arquithon "sem página nenhuma", direto por script/CLI, reaproveitando a mesma lógica de organização.

## 3. Problemas técnicos encontrados no código atual

- **`requirements.txt` está salvo em UTF-16** (confirmado com `file requirements.txt`). Isso quebra `pip install -r requirements.txt` em vários ambientes, que esperam UTF-8/ASCII. Precisa resalvar o arquivo em UTF-8.
- **`arquivista.db` e `arquivista.log` estão versionados no Git**, junto com `__pycache__/app.cpython-313.pyc`. O banco contém hash de senha de usuários reais — não deveria estar no repositório. Falta um `.gitignore` cobrindo `*.db`, `*.log`, `__pycache__/`, `venv/`, `uploads/`.
- **`SECRET_KEY` tem um valor padrão fixo no código** (`'uma-chave-de-desenvolvimento-super-segura'`). Mesmo em uso local, é melhor gerar uma chave aleatória e guardá-la fora do código versionado (`.env`, não commitado).
- Sem tratamento de erros de I/O (disco cheio, permissão negada, nome de arquivo duplicado sobrescrevendo o anterior).

## 4. Experiência de uso (UX)

- Drag-and-drop de arquivos na página principal, além do botão de seleção.
- Barra de progresso durante o upload.
- Ações sobre os arquivos já organizados: baixar, renomear, mover de categoria, excluir (hoje só é possível listar).
- Busca/filtro por nome, tipo ou data na lista de arquivos organizados.
- Permitir apontar para uma pasta já existente no PC (ex. `Downloads`) e organizar o que já está lá, não só o que for enviado pelo formulário.

## 5. Robustez e manutenção do código

- Não há testes automatizados — nem para a lógica de organização (`scan_organized_files`, `allowed_file`), nem para as rotas.
- O mapeamento de extensões (`EXTENSION_MAP`) está fixo no código — mover para um arquivo de configuração (JSON/YAML) editável pelo usuário, sem precisar mexer no `app.py`.
- Padronizar logging com `RotatingFileHandler` (o `arquivista.log` atual não tem rotação nem tamanho controlado).

## 6. Ideias para evoluir o projeto (o que você poderia usar)

- **CLI com Typer/Click**: rodar a organização de arquivos direto pelo terminal ou em tarefas agendadas, sem precisar abrir a página.
- **watchdog**: monitorar uma pasta e organizar arquivos automaticamente assim que forem adicionados, sem precisar fazer upload manual.
- **Tarefa agendada do Windows**: rodar o Arquithon em segundo plano, organizando periodicamente.
- **pywebview**: melhor opção para "página" que roda 100% local sem parecer um site — janela nativa, ícone próprio, sem barra de endereço.
- **PyInstaller**: distribuir como executável único, sem o usuário precisar instalar Python nem dependências.

## Prioridade sugerida

1. Corrigir `requirements.txt` (UTF-16 → UTF-8) e criar `.gitignore` — são bugs simples que afetam qualquer pessoa tentando rodar o projeto.
2. Remover CDN do front-end (vendorizar CSS) — pré-requisito para "offline de verdade".
3. Separar API (back) de páginas (front) — base para as demais melhorias de UX e para uma futura CLI.
4. Empacotamento desktop (pywebview/PyInstaller) — melhora a experiência final de "abrir e usar" em Python.
