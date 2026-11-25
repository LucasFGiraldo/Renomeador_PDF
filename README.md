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
4. Sucessos vão para `historico.txt`. Falhas vão para `erros.txt` e o
   PDF problemático é movido para
   `PASTA_ENTRADA/ERRO_PROCESSAMENTO/`, para não ficar sendo
   reprocessado (e re-logado como erro) a cada varredura.

## Como rodar

```bash
pip install -r requisitos.txt
python main.py
```

Deixe o terminal aberto — ele fica monitorando continuamente.
Pressione `CTRL+C` para parar.

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