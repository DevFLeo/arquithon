# Plano de Melhorias do Arquithon

Este documento reúne as issues abertas no GitHub ([DevFLeo/arquithon](https://github.com/DevFLeo/arquithon/issues)) e outros pontos encontrados em uma revisão do código. Para cada item há **o problema**, **como resolver** e **como validar**.

> Estado de referência: branch `main` no commit `e886fd6`. Nesse ponto os 41 testes (`python -m unittest discover`) passam.

---

## Sumário

| # | Issue | Área | Prioridade | Esforço |
|---|-------|------|-----------|---------|
| [#8](#issue-8--format_category_label-usa-strcapitalize-errado) | `capitalize()` estraga os rótulos de tamanho e de data | `core/organizer.py` | Alta | Baixo |
| [#2](#issue-2--configjson-pode-corromper-durante-a-escrita) | `config.json` pode corromper durante a escrita | `core/config.py` | Alta | Baixo |
| [#6](#issue-6--organizeresult-não-informa-o-motivo-da-falha) | O resultado não diz por que cada arquivo falhou | `core/organizer.py`, `ui/result_dialog.py` | Alta | Médio |
| [#1](#issue-1--arquivo-some-entre-o-scan-e-a-organização) | Arquivo some entre o scan e a organização | `core/organizer.py` | Média | Baixo (vem junto com #6) |
| [#7](#issue-7--busca-reindexa-uploads-inteiro-a-cada-busca) | A busca reindexa `uploads/` inteiro | `core/search.py`, `ui/main_frame.py` | Média | Médio |
| [#3](#issue-3--condição-de-corrida-em-configset) | Condição de corrida em `config.set()` | `core/config.py` | Baixa | Baixo |
| [#4](#issue-4--getsystemmetrics-sem-argtypesrestype) | `GetSystemMetrics` sem `argtypes`/`restype` | `ui/window_state.py` | Baixa | Trivial |
| [#5](#issue-5--vazamento-em-_installed_procs) | Vazamento em `_installed_procs` | `ui/dnd.py` | Baixa | Baixo |

**Ordem sugerida:** #8 → #2 → #6 + #1 (juntas) → #7 → #3 → #4 → #5, e depois as [melhorias gerais](#melhorias-gerais-fora-das-issues).

---

## Issue #8: `format_category_label` usa `str.capitalize()` errado

**Problema.** `str.capitalize()` põe a primeira letra da string em maiúscula e todo o resto em minúscula. Por isso:
- no modo **Tamanho**, `pequenos (menos de 1MB)` vira `Pequenos (menos de 1mb)`;
- no modo **Data**, `01 - janeiro` começa com dígito, então o mês nunca fica maiúsculo.

**Situação.** A PR #9 corrigia isso, mas foi **fechada sem merge**: o `main` ainda usa `p.capitalize()` ([core/organizer.py](core/organizer.py), `format_category_label`). A issue #8 continua aberta.

**Como resolver.** Reabrir ou refazer a PR #9. Basta pôr em maiúscula a primeira *letra* encontrada, sem mexer no resto:

```python
def _capitalizar_primeira_letra(texto: str) -> str:
    for i, ch in enumerate(texto):
        if ch.isalpha():
            return texto[:i] + ch.upper() + texto[i + 1:]
    return texto


def format_category_label(rel_path: str) -> str:
    partes = rel_path.split(os.sep)
    icone = '📅' if partes[0].isdigit() else CATEGORY_ICONS.get(partes[0], '📁')
    texto = ' › '.join(_capitalizar_primeira_letra(p) for p in partes)
    return f'{icone} {texto}'
```

**Testes** (em `tests/test_organizer.py`):
- `format_category_label(os.path.join('tamanho', 'pequenos (menos de 1MB)'))` contém `Pequenos (menos de 1MB)`;
- `format_category_label(os.path.join('2024', '01 - janeiro'))` contém `01 - Janeiro`.

---

## Issue #2: `config.json` pode corromper durante a escrita

**Problema.** `save()` abre `config.json` em modo `'w'`, o que apaga o conteúdo antes de escrever o novo. Se o processo cair nesse meio-tempo (crash, queda de energia, disco cheio), o arquivo fica inválido. Na próxima abertura, `load()` devolve `{}` e **todas as preferências somem** sem aviso.

**Como resolver.** Fazer uma escrita atômica: gravar num arquivo temporário no mesmo diretório e trocar os arquivos com `os.replace()`, que é atômico no mesmo volume.

```python
import json
import os
import tempfile

from core import paths


def save(data: dict) -> None:
    pasta = os.path.dirname(paths.CONFIG_PATH) or '.'
    fd, tmp = tempfile.mkstemp(prefix='.config-', suffix='.tmp', dir=pasta)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, paths.CONFIG_PATH)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise
```

**Extra opcional.** Quando `load()` encontrar um JSON inválido, renomear o arquivo para `config.json.bak` antes de devolver `{}`. Assim fica possível recuperar as preferências manualmente, em vez de sobrescrever tudo no próximo `save()`.

**Testes:**
- depois de `save()`, nenhum `.config-*.tmp` sobra na pasta;
- simular uma falha em `json.dump` (com `unittest.mock.patch`) e verificar que o `config.json` antigo continua intacto.

---

## Issue #6: `OrganizeResult` não informa o motivo da falha

**Problema.** `organize_files` faz `except OSError: failed += 1`. O usuário vê "3 não puderam ser copiados", mas não sabe **quais** arquivos nem **por quê** (permissão, arquivo em uso, caminho longo, disco cheio…).

**Como resolver.**

1. Criar uma dataclass de falha e guardar uma lista delas no resultado:

```python
@dataclass
class Failure:
    source: str
    reason: str


@dataclass
class OrganizeResult:
    successful: int
    failed: int
    operations: list[Operation] = field(default_factory=list)
    failures: list[Failure] = field(default_factory=list)
```

2. No laço de `organize_files`:

```python
except OSError as exc:
    failed += 1
    failures.append(Failure(source=path, reason=_motivo_amigavel(exc)))
```

3. Criar `_motivo_amigavel(exc)`, que traduz os casos mais comuns para português:
   - `FileNotFoundError` → "Arquivo não encontrado (foi removido ou renomeado?)"
   - `PermissionError` → "Sem permissão ou arquivo em uso por outro programa"
   - `errno.ENOSPC` → "Disco cheio"
   - `errno.ENAMETOOLONG` / `winerror 206` → "Caminho muito longo"
   - qualquer outro caso → `exc.strerror or str(exc)`

4. Em [ui/result_dialog.py](ui/result_dialog.py), quando `resultado.failures` não estiver vazio, mostrar uma segunda lista, "Não foi possível organizar", com as colunas `Arquivo | Motivo`.

5. Em [ui/main_frame.py](ui/main_frame.py) (`_organize_paths`), quando **nenhum** arquivo der certo, mostrar os motivos no `showwarning` em vez da mensagem genérica. Pode ser só os primeiros N, seguidos de "e mais X".

**Testes:** organizar um caminho inexistente e checar que `failures[0].reason` fala em "não encontrado"; e que `len(failures) == failed`.

---

## Issue #1: arquivo some entre o scan e a organização

**Problema.** `_dest_by_date` chama `os.path.getmtime(path)` sem tratar erro, e `_dest_by_size` tem o mesmo problema com `os.path.getsize`. Se o arquivo sumir no meio do lote (antivírus, OneDrive, outro programa), a falha é contada sem nenhuma explicação.

**Como resolver.** Isso se resolve **junto com a #6**. A exceção já cai no `except OSError` do laço, então basta que esse `except` registre o motivo (`FileNotFoundError` → "Arquivo não encontrado"). Não vale a pena engolir a exceção dentro de `_dest_by_date`: o arquivo não existe mais, então não há como organizá-lo.

**Melhoria complementar.** No começo de cada iteração, checar `os.path.isfile(path)` e registrar logo a falha, antes de criar pastas de destino que ficariam vazias.

**Testes:** apagar o arquivo depois de montar a lista (ou fazer um `patch` de `os.path.getmtime` que levante `FileNotFoundError`) e verificar a falha com o motivo certo, nos modos `data` e `tamanho`.

---

## Issue #7: busca reindexa `uploads/` inteiro a cada busca

**Correção do diagnóstico.** Hoje a busca **não** roda a cada tecla. `_run_search` só é chamado no `<Return>` e no botão "Buscar" ([ui/main_frame.py](ui/main_frame.py), `_build_search_card`). O problema que existe de fato é outro: **cada busca** chama `search.build_index()`, que percorre todo o `uploads/` e lê até 2000 caracteres de cada arquivo de texto, **na thread da interface**. Com muitos arquivos, a janela congela a cada busca.

**Como resolver (em etapas):**

1. **Cache do índice com invalidação explícita.** Guardar o índice em `MainFrame` (`self._index = None`) e só reconstruí-lo quando:
   - for `None` (primeira busca);
   - depois de `_organize_paths`, `_undo_last_organize` ou `_delete_selected_file` (basta fazer `self._index = None`);
   - o usuário pedir, com um botão "Atualizar" ou a tecla `F5`.

   ```python
   def _get_index(self):
       if self._index is None:
           self._index = search.build_index()
       return self._index
   ```

   Isso preserva a vantagem citada no docstring de `core/search.py` (nada de cache complicado), porque as mudanças feitas pelo próprio app já invalidam o índice. Mudanças feitas fora do app só aparecem depois do "Atualizar", e isso deve ser documentado.

2. **Indexar fora da thread da UI.** Rodar `build_index()` num `threading.Thread` e entregar o resultado à interface com `self.after(0, ...)`. Enquanto isso, mostrar "Indexando…" e desabilitar o botão de busca.

3. **(Opcional) Busca enquanto digita.** Se quiserem busca ao vivo, usar *debounce* com o mesmo padrão de `window.after`/`after_cancel` de `ui/window_state.py`, com uns 250 ms depois da última tecla. Com o cache do passo 1, cada busca vira só um filtro em memória.

**Testes:** em `tests/test_search.py`, confirmar que o `search()` sobre um índice já montado não acessa o disco (com um `patch` de `os.walk`). A invalidação pode ser testada instanciando a lógica fora do Tk, ou extraindo um pequeno `IndexCache` para `core/search.py`.

---

## Issue #3: condição de corrida em `config.set()`

**Correção do diagnóstico.** No processo atual **não há corrida**. O Tkinter tem uma única thread, e os callbacks de `window.after` rodam na mesma thread do clique em "Salvar", um depois do outro, sem se intercalar. Os riscos reais são dois:
- **duas instâncias do app** abertas ao mesmo tempo, gravando o mesmo `config.json`;
- **futuras threads**, por exemplo a indexação em segundo plano sugerida na #7, se um dia elas chamarem `config.set`.

Além disso, cada `config.get()` e cada `config.set()` relê o arquivo inteiro do disco, o que é desnecessário.

**Como resolver.**
1. Manter a config **em memória** durante o processo: carregar uma vez e fazer `set()` atualizar o dicionário e gravar com o `save()` atômico da #2.
2. Proteger `set()` com um `threading.Lock` (custa quase nada e deixa o código pronto para threads).
3. Para várias instâncias, a solução mais simples é na hora de gravar: reler o arquivo, aplicar **só a chave alterada** e salvar, com tudo dentro do lock.

```python
_lock = threading.Lock()
_cache: dict | None = None


def _dados() -> dict:
    global _cache
    if _cache is None:
        _cache = load()
    return _cache


def get(key, default=None):
    with _lock:
        return _dados().get(key, default)


def set(key, value) -> None:
    with _lock:
        atual = load()          # pega o que outra instância possa ter gravado
        atual[key] = value
        save(atual)
        global _cache
        _cache = atual
```

**Atenção nos testes.** `tests/test_config.py` provavelmente troca `paths.CONFIG_PATH` entre os testes. Nesse caso, é preciso uma função `_reset_cache()` para os testes chamarem no `setUp`.

---

## Issue #4: `GetSystemMetrics` sem `argtypes`/`restype`

**Problema.** Em [ui/window_state.py](ui/window_state.py) (`_area_das_telas`), `GetSystemMetrics` é chamado sem declarar a assinatura. O padrão do ctypes (`c_int`) até funciona, mas o código fica inconsistente com `ui/dnd.py` e frágil se alguém mudar algo depois.

**Como resolver:**

```python
import ctypes
from ctypes import wintypes

metric = ctypes.windll.user32.GetSystemMetrics
metric.argtypes = [ctypes.c_int]
metric.restype = ctypes.c_int
SM_XVIRTUALSCREEN, SM_YVIRTUALSCREEN, SM_CXVIRTUALSCREEN, SM_CYVIRTUALSCREEN = 76, 77, 78, 79
x, y = metric(SM_XVIRTUALSCREEN), metric(SM_YVIRTUALSCREEN)
largura, altura = metric(SM_CXVIRTUALSCREEN), metric(SM_CYVIRTUALSCREEN)
```

Aproveitar para trocar os números mágicos por constantes nomeadas.

**Validação manual:** com um segundo monitor posicionado **à esquerda** do principal (coordenada X negativa), fechar o app nesse monitor e reabrir. A janela deve voltar no mesmo lugar, e não centralizada.

---

## Issue #5: vazamento em `_installed_procs`

**Problema.** Em [ui/dnd.py](ui/dnd.py), cada `enable_file_drop` bem-sucedido adiciona o callback à lista global `_installed_procs`, e nada nunca é removido. Quem cria e destrói janelas com drag-and-drop várias vezes acumula objetos.

**Como resolver.**
1. Trocar a lista por um dicionário `hwnd -> (proc, previous_proc)`.
2. No `cancelar` (ligado ao `<Destroy>`):
   - **restaurar o WNDPROC original** com `set_window_long(hwnd, GWL_WNDPROC, previous_proc)` *antes* de soltar a referência. Sem isso, o Windows ainda pode chamar o ponteiro morto enquanto a janela é destruída;
   - chamar `shell32.DragAcceptFiles(hwnd, False)`;
   - fazer `_installed_procs.pop(hwnd, None)`.
3. Se `enable_file_drop` for chamado duas vezes para o mesmo `hwnd`, não instalar de novo: devolver `True` direto.

**Cuidado.** O `argtypes` de `set_window_long` hoje espera `wndproc_type`, e `previous_proc` é um inteiro (`LRESULT`). Para restaurar, é preciso uma segunda declaração (ou usar `ctypes.c_void_p` como tipo do terceiro argumento nos dois usos).

**Testes:** difícil de automatizar fora do Windows. Uma opção é um teste marcado com `@unittest.skipUnless(sys.platform == 'win32')` que cria e destrói um `tk.Tk()` três vezes e confere que `len(dnd._installed_procs) == 0` no final.

---

## Melhorias gerais (fora das issues)

### Repositório e processo
- **Tirar o `Arquithon.exe` (~11 MB) do Git.** Binários no histórico incham cada clone para sempre. Publicar o executável em **GitHub Releases**, adicionar `*.exe` ao `.gitignore` e rodar `git rm --cached Arquithon.exe`.
- **Mensagens de commit.** Vários commits recentes têm como mensagem o próprio comando colado (`git add .`, `git remote add origin ...`). Usar mensagens descritivas, de preferência no padrão *Conventional Commits* (`fix:`, `feat:`, `docs:`), deixa o histórico legível e permite gerar changelog.
- **Trabalhar com branches e PRs** em vez de commitar direto no `main`. A PR #9 mostra o risco: foi fechada sem merge e a correção se perdeu.
- **Nome do `.spec`.** O commit `e8ec64c` diz ter renomeado `Arquithon.spec` para `arquithon.spec`, mas o arquivo versionado continua `Arquithon.spec`. O Windows não diferencia maiúsculas e minúsculas, então o Git não percebeu a mudança. Para renomear de verdade: `git mv Arquithon.spec tmp.spec && git mv tmp.spec arquithon.spec`.
- **`requirements.txt` desatualizado.** O comentário cita `sqlite3` e `hashlib`, mas nenhum dos dois é usado no código. Ajustar o comentário.

### Qualidade e CI
- **GitHub Actions**: um workflow simples (`windows-latest` + `ubuntu-latest`, Python 3.10+) rodando `python -m unittest discover` em cada push e PR. Assim uma PR como a #9 mostraria o resultado dos testes antes do merge.
- **Lint e formatação**: adicionar `ruff` (lint + format) num `pyproject.toml`, e opcionalmente `pre-commit`.
- **Cobertura**: rodar `coverage run -m unittest discover` e mirar primeiro em `core/` (a UI é mais difícil de testar).
- **Testes de regressão**: cada issue corrigida deve vir com um teste que falhava antes da correção.

### Código
- **Organização em thread separada.** `organize_files` roda na thread da UI e usa `update_idletasks()` para mover a barra de progresso. Com muitos arquivos ou arquivos grandes, a janela para de responder, e o botão de fechar não funciona durante a cópia. O mesmo padrão sugerido na #7 (thread + `after`) resolve isso e permite um botão "Cancelar".
- **Logging.** Não existe nenhum log. Um `logging` com `RotatingFileHandler` ao lado do `config.json` (ex.: `arquithon.log`) ajudaria a diagnosticar relatos de usuários, principalmente falhas de cópia (#6) e erros de ctypes (#4, #5).
- **Desfazer mais completo.** `undo_operations` também só conta falhas. Aplicar a mesma ideia da #6 (lista de motivos).
- **Lixeira ao excluir.** `delete_file` apaga de vez. Uma alternativa sem dependências no Windows é `SHFileOperationW` com `FOF_ALLOWUNDO` via ctypes, para mandar o arquivo para a Lixeira.

---

## Checklist de execução

- [ ] #8: reabrir/refazer a PR #9 e fazer o merge
- [ ] #2: escrita atômica em `config.save()`
- [ ] #6 + #1: `failures` em `OrganizeResult` e exibição no `result_dialog`
- [ ] #7: cache do índice com invalidação e indexação em thread
- [ ] #3: config em memória com lock
- [ ] #4: `argtypes`/`restype` e constantes em `GetSystemMetrics`
- [ ] #5: dicionário por `hwnd` e restauração do WNDPROC no `<Destroy>`
- [ ] CI com GitHub Actions
- [ ] Remover `Arquithon.exe` do repositório e publicar em Releases
- [ ] Corrigir o nome do `.spec` e o comentário do `requirements.txt`
