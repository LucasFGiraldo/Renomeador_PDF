# Sistema de Renomeação Automática de PDFs

## Como funciona

1. Ao rodar `main.py`, o programa **sempre** pergunta as informações
   fixas (sufixo do nome, e se deve incluir DATA / VALOR / NOME do
   favorecido) e regrava o arquivo `config_user.txt`.
2. Em seguida, fica monitorando a `PASTA_ENTRADA` (definida em
   `config.py`) em loop, a cada `INTERVALO_MONITORAMENTO` segundos.
3. Para cada PDF novo encontrado:
   - espera ele ficar "estável" (tamanho parado), para não ler um
     arquivo que ainda está sendo colado/copiado;
   - lê o texto do PDF (`leitor_pdf.py`);
   - extrai as informações variáveis do texto (`extrator.py`);
   - monta o nome final combinando o fixo + as variáveis marcadas como
     "S" (`renomeador.py`);
   - move o arquivo já renomeado para `PASTA_RESULTADOS`.
4. Sucessos e falhas ficam registrados no banco SQLite `historico.db`
   (veja na tela Histórico). O PDF que falhou é movido para a pasta de
   erros (`PASTA_ERROS_PDF`), para não ficar sendo reprocessado (e
   registrado como erro) a cada varredura. Quem vinha das versões com
   `historico.txt`/`erros.txt` tem esse histórico importado para o
   banco automaticamente na primeira execução.

## Instalação no computador de uso (sem terminal)

Feito uma única vez por quem instala; depois, quem usa só precisa do
atalho na Área de Trabalho.

1. Instale o Python (python.org), marcando **"Add Python to PATH"**.
2. Baixe o projeto (`git clone` ou `git pull`) e crie o `config.py`
   com os caminhos das pastas (veja a seção *Caminhos* abaixo).
3. Dê dois cliques em **`instalar.bat`**.

O instalador (não precisa de administrador):

- instala as dependências Python;
- faz o sistema ligar sozinho, **sem janela**, sempre que o usuário
  entrar no Windows. O monitor também já começa ligado, se houver
  configuração salva; se a unidade de rede ainda não estiver
  conectada, ele espera e tenta de novo;
- cria o atalho **"Renomeador de PDFs"** na Área de Trabalho, que abre
  o sistema no navegador (e liga o servidor, se ele estiver desligado).

As mensagens do servidor ficam em `servidor.log`. Para desfazer, use
**`desinstalar.bat`** (não apaga arquivos nem histórico).

Depois de um `git pull` com mudanças no código, reinicie o servidor:
rode o `desinstalar.bat` e o `instalar.bat` de novo (ou reinicie o
computador).

## Como rodar

```bash
python -m pip install -r requisitos.txt
```

Há dois jeitos de usar o sistema (use um ou outro, não os dois ao
mesmo tempo, para não haver dois monitores na mesma pasta):

**Modo terminal** — pergunta as configurações e já começa a monitorar.
Pressione `CTRL+C` para parar.

```bash
python main.py
```

**Modo interface web** — sobe um servidor local com as telas (Painel,
Configuração, Histórico e Erros). Abra **http://localhost:8000** no
navegador; a configuração e o monitor passam a ser controlados por lá.

```bash
python api.py
```

As telas já vêm compiladas na pasta `interface/`, então o computador
que só *usa* o sistema não precisa de Node.js.

Principais rotas da API:

| Rota | O que faz |
|---|---|
| `GET /api/status` | Monitor ligado/desligado, fila, erros, totais do dia, pastas acessíveis |
| `POST /api/monitor/iniciar` / `parar` | Liga ou desliga o monitor |
| `GET` / `PUT /api/configuracao` | Lê ou salva sufixo e campos do nome |
| `POST /api/configuracao/previa` | Mostra como ficaria o nome, sem renomear nada |
| `GET /api/historico` | Eventos de renomeação (filtros `status` e `busca`) |
| `GET /api/erros` | PDFs na pasta de erros e o motivo |
| `GET /api/erros/{arquivo}/pdf` | Abre o PDF com erro no navegador |
| `POST /api/erros/{arquivo}/reprocessar` | Tenta de novo, com dados corrigidos à mão (opcional) |
| `POST /api/pdfs` | Envia PDFs para a pasta de entrada |

A documentação interativa da API fica em http://localhost:8000/docs.
A API só aceita conexões do próprio computador (`127.0.0.1`).
O histórico (sucessos e erros) fica no banco SQLite `historico.db`.

## Como customizar para o seu tipo de PDF

O `extrator.py` é genérico: funciona por **rótulos** (`Nome:`,
`Valor:`, `Data Pagamento:`...) e **cabeçalhos de seção**
(`Favorecido`, `Dados de quem recebeu`...), e não por banco. Cada
rótulo é procurado nas três disposições que o `pypdf` costuma gerar:

```
Nome: FULANO                 (mesma linha)
Nome:                        (linha de baixo — ex.: banco XO)
 FULANO
FULANONome:                  (invertido — ex.: Bradesco)
```

Quando o comprovante tem dois nomes (quem pagou e quem recebeu), vale
o que estiver mais perto de um cabeçalho de favorecido/recebedor. A
data de pagamento tem prioridade sobre a de vencimento, e o valor
pago/total sobre o valor de face.

Se um banco novo usar outro rótulo ou cabeçalho, acrescente-o nas
listas do início do `extrator.py` (`_ROTULOS_*` e `_CABECALHOS_*`). Uma forma rápida de descobrir o
texto exato é rodar:

```python
import leitor_pdf
print(leitor_pdf.ler_pdf("caminho/para/um_exemplo.pdf"))
```

e ver como o texto realmente sai (o `pypdf` às vezes junta ou separa
linhas de forma diferente do PDF visual).

## Caminhos (`config.py`)

- `PASTA_ENTRADA`: pasta monitorada (onde os PDFs são colados).
- `PASTA_RESULTADOS`: pasta onde os PDFs já renomeados são colocados.
- `PASTA_ERROS_PDF`: nome da subpasta (dentro de `PASTA_ENTRADA`) para
  onde vão os PDFs que falharam.

Ambas as pastas são criadas automaticamente se não existirem.
## Desenvolvendo a interface (Angular)

O código-fonte das telas fica em `frontend/` (Angular). Só é preciso
Node.js para **alterar** as telas:

```bash
cd frontend
npm install
npm start          # http://localhost:4200, com recarga automática
```

Deixe o `python api.py` rodando ao mesmo tempo: o `npm start` encaminha
as chamadas `/api` para ele. Ao terminar, gere a versão compilada
(vai para `interface/`, que é versionada) e faça o commit:

```bash
npm run build
```
