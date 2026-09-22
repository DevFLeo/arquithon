# Arquithon, o Arquivista em Python

Arquithon é um aplicativo nativo, feito em Python com Tkinter, que organiza arquivos automaticamente por tipo, data, nome ou tamanho. Não tem login, não abre navegador, não depende de internet nem de servidor: é só abrir e usar, com tudo rodando dentro do próprio executável.

## O que ele faz

Você escolhe um ou mais arquivos (ou uma pasta inteira, organizada recursivamente) pelo diálogo nativo do sistema — ou simplesmente arrasta arquivos e pastas do Explorer para dentro da janela —, e o Arquithon copia cada um para a subpasta certa dentro de `uploads/`, de acordo com o critério de organização escolhido. Por tipo de arquivo, imagens vão para `imagens/png`, documentos para `documentos/pdf`, músicas para `multimedia/audio` e assim por diante — o dicionário de extensões cobre imagens, documentos, planilhas, apresentações, e-books, áudio, vídeo, arquivos compactados, código-fonte, design/CAD, executáveis e fontes. Qualquer extensão fora desse mapa cai em `outros/<extensão>`, então nada fica sem categoria.

Além de por tipo, dá para organizar por data de modificação (agrupando em pastas de ano e mês), por nome do arquivo (ordem alfabética) ou por tamanho (pequenos, médios e grandes). O critério escolhido fica salvo em `config.json`, ao lado do executável, e é lembrado da próxima vez que o app abrir.

Terminada a organização, aparece a lista do que foi para onde: cada arquivo com a categoria em que caiu, e o aviso de "salvo como ..." quando um homônimo obrigou a renomear. O botão `OK` já vem selecionado (Enter ou Esc fecham), ao lado de `Reverter`, que desfaz aquela leva na hora, e de `Abrir pasta`, para conferir no Explorer. Também há um botão "Abrir Pasta de Arquivos" sempre visível. Clicar com o botão direito em qualquer categoria ou arquivo da lista abre o Explorer do Windows direto naquele lugar. Se dois arquivos organizados tiverem o mesmo nome, o segundo recebe um sufixo `(2)`, `(3)`... para nunca sobrescrever o primeiro sem avisar.

Por padrão os arquivos são copiados para `uploads/`, mantendo o original no lugar. Tem uma opção "Mover em vez de copiar" para quem quer tirar o arquivo da origem de vez — nesse caso o app pede confirmação antes, já que é uma ação que remove o original. Uma barra de progresso aparece durante a organização de vários arquivos, e um botão "Desfazer última organização" some quando não há nada a desfazer e some depois de usado; ele reverte exatamente a última leva (cópias são apagadas, arquivos movidos voltam para onde estavam).

Tem também uma busca: digite um trecho do nome, da pasta (ex.: "imagens" ou "documentos pdf") ou do conteúdo (para arquivos de texto como `.txt`, `.md`, `.py`, `.json` e afins), e o app varre tudo que já foi organizado e mostra os resultados na hora, cada um já com a categoria, o tamanho e a data de modificação. Quem casa pelo nome do arquivo aparece antes de quem casa só pela pasta, que aparece antes de quem casa pelo conteúdo. Formatos binários como PDF, DOCX ou imagens continuam pesquisáveis pelo nome, só o conteúdo deles que não é lido. A preferência de buscar também no conteúdo fica salva em `config.json`, igual ao critério de organização.

Clicar com o botão direito num arquivo já organizado também oferece "Excluir arquivo" — remove definitivamente (sem lixeira), então o app sempre pede confirmação antes. Não dá para excluir uma categoria inteira de uma vez: só arquivo por arquivo, de propósito, para uma exclusão em massa não acontecer sem querer.

Para expandir ou recolher uma categoria na lista, não é preciso mirar na setinha: clicar em qualquer ponto da linha (o nome da categoria, os ícones, o espaço em branco) já abre ou fecha ela. A setinha continua funcionando do jeito de sempre.

Arrastar e soltar funciona em qualquer ponto da janela, com arquivos e pastas na mesma leva: as pastas entram inteiras, recursivamente, e tudo segue o mesmo critério de organização e a mesma opção de mover em vez de copiar. Soltar a própria pasta do Arquithon é recusado, para o app não organizar a si mesmo. Se o sistema não oferecer suporte (fora do Windows), a área de soltar simplesmente não aparece.

Um botão "⚙️ Configurações" no canto superior direito abre o tamanho da fonte (pequena/média/grande), o tema (claro/escuro), se a caixa "Mover em vez de copiar" já deve vir marcada e se a janela deve reabrir do tamanho e no lugar em que foi fechada da última vez. Tudo isso também fica salvo em `config.json` e some ou aparece na hora, sem precisar reabrir o app — exceto a posição/tamanho da janela e a caixa de mover, que só valem a partir da próxima vez que o app abrir.

Atalhos de teclado: `Ctrl+O` abre o seletor de arquivos, `Ctrl+F` foca o campo de busca.

## Tecnologia

Tudo usa apenas a biblioteca padrão do Python — Tkinter para a interface, `json` para guardar a preferência de organização, `shutil`/`os` para mover e organizar os arquivos, `dataclasses` para o índice de busca, `ctypes` para receber os arquivos arrastados do Explorer (o Tkinter puro não recebe drag and drop; em vez de depender do `tkinterdnd2` e da extensão Tcl que vem com ele, o app fala direto com a API do Windows). Nenhuma dependência externa é necessária para rodar `python app.py`; o PyInstaller só entra na hora de gerar o `.exe`.

O código é dividido por responsabilidade: `core/` guarda toda a regra de negócio (caminhos, organização, busca, integração com o Explorer) sem depender de Tkinter, e `ui/` guarda só a interface, que consome o `core`. Essa separação é o que torna fácil testar a lógica isoladamente (veja `tests/`) e crescer o app sem esbarrar num arquivo gigante — um novo critério de organização, por exemplo, é só uma função nova em `core/organizer.py`.

## Rodando localmente

Com o Python instalado, basta

```bash
python app.py
```

A janela abre direto no organizador — não existe tela de login.

## Gerando o executável

Para distribuir como aplicativo Windows, sem exigir Python na máquina de quem for usar

```bash
pip install -r requirements.txt
python -m PyInstaller Arquithon.spec
```

O executável sai em `dist/Arquithon.exe`. Ao abrir, a pasta `uploads/` e o arquivo `config.json` são criados ao lado do próprio `.exe`, então basta mover o executável para onde você quiser manter os arquivos organizados.

## Estrutura do projeto

```
arquithon/
├── app.py               ponto de entrada, só sobe a janela
├── core/                regra de negócio, sem Tkinter
│   ├── paths.py          onde ficam uploads/ e config.json
│   ├── config.py         leitura/escrita do config.json
│   ├── organizer.py      dicionário de extensões e critérios de organização
│   ├── search.py         indexação e busca nos arquivos organizados
│   └── fs_utils.py        abrir pastas/arquivos no Explorer
├── ui/                  interface Tkinter, consome o core
│   ├── styles.py          paleta de cores e tamanhos de fonte (tema claro/escuro)
│   ├── dnd.py             arrastar e soltar arquivos do Explorer (API do Windows)
│   ├── result_dialog.py   lista de "o que foi para onde" ao fim da organização
│   ├── settings_dialog.py tela de configurações (fonte, tema, padrões)
│   ├── window_state.py    lembra tamanho e posição da janela entre uma sessão e outra
│   ├── app_window.py
│   └── main_frame.py
├── tests/               testes de core/ (unittest, sem dependências externas)
├── Arquithon.spec       configuração do PyInstaller para gerar o .exe
├── requirements.txt     dependência de build (pyinstaller)
└── uploads/             arquivos organizados (criado em tempo de execução)
```

Para rodar os testes: `python -m unittest discover`.

## Status

O projeto já passou por uma versão web (Flask + HTML, com deploy em nuvem) e por uma versão com login por usuário. A versão atual prioriza simplicidade: um aplicativo offline, sem contas, sem servidor, para uso pessoal direto na máquina.
