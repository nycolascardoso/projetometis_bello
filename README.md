# Projeto Metis — Automação de Extração de Imóveis e IPTU

> Automação completa para extração de dados cadastrais de imóveis e carnês de IPTU do portal e-IPTU da Prefeitura de Caçador (SC), com resolução automática de CAPTCHA, execução paralela e gravação direta em planilha Excel.

---

## Índice

- [Visão Geral](#visão-geral)
- [Como Funciona](#como-funciona)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Estrutura da Planilha](#estrutura-da-planilha)
- [Execução](#execução)
  - [Passo 1 — Extração de Imóveis](#passo-1--extração-de-imóveis)
  - [Passo 2 — Extração de IPTU](#passo-2--extração-de-iptu)
  - [Scripts PowerShell](#scripts-powershell)
- [Fluxo Detalhado por Módulo](#fluxo-detalhado-por-módulo)
  - [extracao_imoveis](#extracao_imoveis)
  - [extracao_iptu](#extracao_iptu)
- [Resolução de CAPTCHA](#resolução-de-captcha)
- [Execução Paralela](#execução-paralela)
- [Tratamento de Erros](#tratamento-de-erros)
- [Solução de Problemas](#solução-de-problemas)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)

---

## Visão Geral

O **Projeto Metis** é um robô de automação web desenvolvido em Python que lê uma lista de CPFs e CNPJs de uma planilha Excel, faz login no portal [e-IPTU de Caçador](https://tmi-apps.e-publica.net/cacador_eiptu/), extrai os dados cadastrais de todos os imóveis vinculados a cada documento e, em seguida, coleta os carnês de IPTU (parcelados ou em cota única) de cada imóvel — tudo de forma automática, sem intervenção humana.

**Destaques:**

- Resolução automática de CAPTCHA via OCR (EasyOCR)
- Cache inteligente de CAPTCHA: após 2 logins bem-sucedidos, o site estabiliza o CAPTCHA e o robô o reutiliza para todos os imóveis seguintes, eliminando chamadas desnecessárias ao OCR
- Execução paralela com múltiplos workers (browsers independentes), reduzindo drasticamente o tempo total
- Gravação incremental na planilha: dados são salvos após cada imóvel processado, garantindo que nenhum resultado seja perdido em caso de interrupção
- Suporte a modo headless (sem janela do browser aberta)
- Classificação automática de erros por categoria (Processamento vs. Conexão)

---

## Como Funciona

O projeto opera em **dois passos sequenciais**:

```
┌─────────────────────────────────────────────────────────────────────┐
│  PLANILHA: Banco_de_Imoveis.xlsx                                    │
│                                                                     │
│  Aba "Consultar"           Aba "Link de Imóveis"   Aba "Banco de   │
│  ┌────────────────────┐    ┌────────────────────┐  Dados"           │
│  │ CNPJ/CPF | Processar│   │ Cód. Imóvel | IPTU?│  ┌────────────┐  │
│  │ ...      | Sim     │   │ ...         | Sim  │  │ Carnês IPTU│  │
│  └────────────────────┘   └────────────────────┘  └────────────┘  │
│          │                          │                    ▲          │
│          │   PASSO 1                │   PASSO 2          │          │
│          ▼                          ▼                    │          │
│    extracao_imoveis           extracao_iptu              │          │
│    (login com CPF/CNPJ)       (login com Cód. Imóvel)   │          │
│    (extrai lista de imóveis)  (extrai carnê de IPTU) ────┘          │
└─────────────────────────────────────────────────────────────────────┘
```

**Passo 1 — `extracao_imoveis`:** lê os CPFs/CNPJs da aba `Consultar`, faz login no portal com cada documento, resolve o CAPTCHA, e salva os imóveis vinculados (código, inscrição imobiliária, endereço, situação, URL) na aba `Link de Imóveis`.

**Passo 2 — `extracao_iptu`:** lê os imóveis marcados com `Sim` na coluna `Extrair IPTU?` da aba `Link de Imóveis`, faz login com o **código do imóvel**, captura dados cadastrais adicionais (localização, tipologia, estrutura, utilização, proprietário) e extrai a tabela de parcelas do carnê de IPTU, salvando tudo na aba `Banco de Dados`.

---

## Estrutura do Projeto

```
Projeto Metis/
│
├── extracao_imoveis/               # Módulo do Passo 1
│   ├── __init__.py
│   ├── config.py                   # Caminhos, URL e seletores XPath
│   ├── main.py                     # Ponto de entrada; orquestra o loop de CPFs/CNPJs
│   ├── selenium_tasks.py           # Driver, login, OCR e extração da tabela de imóveis
│   └── utils.py                    # Leitura/escrita na planilha (Passo 1)
│
├── extracao_iptu/                  # Módulo do Passo 2
│   ├── __init__.py
│   ├── config.py                   # Caminhos, URLs, seletores e configuração de workers
│   ├── main.py                     # Ponto de entrada; execução paralela com ThreadPoolExecutor
│   ├── main_unique.py              # Versão sequencial legada (primeiros 100 imóveis)
│   ├── selenium_tasks.py           # Driver, CaptchaCache, login, extração do carnê
│   └── utils.py                    # Leitura/escrita na planilha (Passo 2)
│
├── MVP/                            # Provas de conceito iniciais (histórico)
│   ├── MVP-Metis.py                # Primeiro protótipo: extração manual para CSV
│   └── resolver_captcha.py         # Testes isolados de OCR
│
├── scripts/                        # Utilitários PowerShell
│   ├── setup.ps1                   # Cria o venv e instala dependências
│   ├── run_imoveis.ps1             # Ativa o venv e executa o Passo 1
│   ├── run_iptu.ps1                # Ativa o venv e executa o Passo 2
│   └── diagnose.ps1                # Verifica Python, Edge, Tesseract, planilha e URL
│
├── Banco_de_Imoveis.xlsx           # Planilha principal (entrada e saída de dados)
├── settings.ini                    # Configuração centralizada (caminhos e workers)
├── requirements.txt                # Dependências Python com versões fixadas
└── .gitignore
```

---

## Pré-requisitos

| Requisito | Versão / Observação |
|---|---|
| Python | 3.11 ou 3.12 |
| Microsoft Edge | Qualquer versão recente (Selenium Manager baixa o driver automaticamente) |
| Tesseract OCR | Necessário para OCR de CAPTCHA; instalar via `winget` (ver abaixo) |
| Git | Opcional, para clonar o repositório |

> **Não é necessário baixar o EdgeDriver manualmente.** O Selenium Manager cuida disso automaticamente. O campo `driver` no `settings.ini` é usado apenas como fallback de emergência.

---

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/nycolascardoso/projetometis_bello.git
cd projetometis_bello
```

### 2. Crie e ative o ambiente virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> No CMD use: `.\.venv\Scripts\activate.bat`

### 3. Atualize o pip e instale as dependências

```powershell
python -m pip install -U pip
pip install -r requirements.txt
```

### 4. Instale o Tesseract OCR (Windows)

```powershell
winget install -e --id UB-Mannheim.TesseractOCR
```

Ou baixe o instalador em: https://github.com/UB-Mannheim/tesseract/wiki

### 5. (Opcional) PyTorch CPU para EasyOCR mais rápido

Se o PyTorch não tiver sido instalado pelo `requirements.txt` (por exemplo, em ambiente sem GPU), instale via CDN oficial:

```powershell
pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio
```

> Na primeira execução, o EasyOCR baixará os modelos de OCR (~200 MB). Isso acontece apenas uma vez.

### Instalação via script (alternativa)

```powershell
.\scripts\setup.ps1
```

---

## Configuração

Toda a configuração do projeto está centralizada no arquivo `settings.ini` na raiz do projeto:

```ini
[paths]
planilha = C:/Projetos/Projeto_Metis/Projeto Metis/Banco_de_Imoveis.xlsx
driver   = C:/Users/ngcar/edgedriver_win64/msedgedriver.exe

[execution]
n_workers = 3
headless  = true
```

| Chave | Descrição |
|---|---|
| `planilha` | Caminho absoluto para o arquivo `Banco_de_Imoveis.xlsx` |
| `driver` | Caminho do EdgeDriver (usado apenas como fallback se o Selenium Manager falhar) |
| `n_workers` | Número de browsers paralelos no Passo 2. Recomendado: 2–4 |
| `headless` | `true` = browser sem janela (mais rápido); `false` = visível (útil para depuração) |

> **Atenção:** ajuste o caminho de `planilha` para onde o arquivo `.xlsx` está na sua máquina antes de executar.

---

## Estrutura da Planilha

O projeto lê e escreve em três abas do arquivo `Banco_de_Imoveis.xlsx`:

### Aba `Consultar` — Entrada do Passo 1

| Col | Campo | Descrição |
|---|---|---|
| A | CNPJ / CPF | Documento do proprietário (formatado, ex: `50.136.653/0001-70`) |
| B | Status | Atualizado automaticamente: `Em progresso`, `Finalizado`, `Erro: ...` |
| C | Última Atualização | Timestamp da última operação |
| D | Tipo de Doc. | `CNPJ proprietário` ou `CPF proprietário` (pode ser fórmula Excel) |
| E | Processar | **`Sim`** = será processado; `Não` = ignorado |

> A coluna E é definida como `Não` automaticamente após cada CNPJ/CPF ser finalizado com sucesso.

### Aba `Link de Imóveis` — Saída do Passo 1 / Entrada do Passo 2

| Col | Campo | Descrição |
|---|---|---|
| A | CNPJ / CPF | Documento de origem |
| B | Código do Imóvel | Usado no login do Passo 2 |
| C | Inscrição Imobiliária | Identificador cadastral |
| D | Logradouro | Endereço |
| E | Complemento | Complemento do endereço |
| F | Bairro | Bairro |
| G | Situação | Ex: `Ativo`, `Inativo` |
| H | URL do Imóvel | Link direto no portal |
| I | Status | Status do Passo 1 |
| J | Última Atualização | Timestamp |
| K | Extrair IPTU? | **`Sim`** = será processado no Passo 2 |
| L | IPTU Extraído? | Atualizado automaticamente: `Sim`, `Sem Lançamento IPTU`, `Erro de Conexão`, `Erro de Processamento` |
| M | Localização | Preenchido no Passo 2 |
| N | Tipologia | Preenchido no Passo 2 |
| O | Estrutura | Preenchido no Passo 2 |
| P | Utilização | Preenchido no Passo 2 |
| Q | Proprietário | Preenchido no Passo 2 |

### Aba `Banco de Dados` — Saída do Passo 2

Cada linha representa **uma parcela de IPTU**. Colunas:

| Col | Campo |
|---|---|
| A | Inscrição Imobiliária |
| B–N | Dados da parcela (Ano, Descrição, Nº Parcela, Sub-parcela, Tipo Débito, Dt. Vcto., Vlr. Parcela, Desconto, Juros, Multa, Correção, Honorários, Vlr. Corrigido) |
| O | Tipo de Pagamento (`Cota Única 20%`, `Cota Única 10%` ou `Parcelado`) |
| P | Código do Imóvel (referência cruzada) |

---

## Execução

### Passo 1 — Extração de Imóveis

```powershell
# Ative o ambiente virtual primeiro
.\.venv\Scripts\Activate.ps1

# Execute o Passo 1
python -m extracao_imoveis.main
```

O que acontece:
1. A planilha é carregada e todas as linhas com `Processar = Sim` na aba `Consultar` são selecionadas
2. Um browser Edge é aberto
3. Para cada CNPJ/CPF, o robô faz login, resolve o CAPTCHA, extrai todos os imóveis vinculados e os salva na aba `Link de Imóveis`
4. A planilha é salva imediatamente após cada CNPJ/CPF processado (proteção contra crashes)
5. O status na aba `Consultar` é atualizado para `Finalizado` (ou `Erro: ...` em caso de falha)

### Passo 2 — Extração de IPTU

```powershell
python -m extracao_iptu.main
```

O que acontece:
1. A planilha é carregada e todos os imóveis com `Extrair IPTU? = Sim` (coluna K) na aba `Link de Imóveis` são selecionados
2. Os imóveis são divididos em N chunks (um por worker) usando distribuição intercalada: `chunk[i] = imoveis[i::n]`
3. N browsers Edge são abertos em paralelo (headless por padrão)
4. Cada worker processa seu chunk de forma independente, com seu próprio `CaptchaCache`
5. A planilha é protegida por um `threading.Lock` global, garantindo escritas seguras entre workers
6. Para cada imóvel: login → captura de dados cadastrais → acesso ao carnê IPTU → extração das parcelas → gravação na aba `Banco de Dados`

### Scripts PowerShell

Para facilitar a execução sem precisar ativar o venv manualmente:

```powershell
# Diagnóstico do ambiente
.\scripts\diagnose.ps1

# Executar Passo 1
.\scripts\run_imoveis.ps1

# Executar Passo 2
.\scripts\run_iptu.ps1
```

O script `diagnose.ps1` verifica automaticamente:
- Se Python está instalado e acessível
- Se o Microsoft Edge está no PATH
- Se o Tesseract está instalado
- Se o arquivo da planilha existe no caminho configurado
- Se o portal e-IPTU está acessível pela rede

---

## Fluxo Detalhado por Módulo

### extracao_imoveis

```
main.py
  └─ carregar_planilha()                    # utils.py: abre o .xlsx sem data_only
  └─ obter_linhas_para_processamento()      # utils.py: filtra linhas com Processar=Sim
       └─ Detecta fórmulas na col. D:
          se tipo_doc começa com "=",
          infere pelo tamanho do CPF/CNPJ
  └─ iniciar_driver()                       # selenium_tasks.py: Edge via Selenium Manager
  └─ Para cada CNPJ/CPF (até 3 tentativas):
       └─ atualizar_status_consultar()      # "Em progresso"
       └─ realizar_login()                  # acessa URL, seleciona tipo, insere doc, OCR
            └─ resolver_captcha()           # EasyOCR lazy singleton
       └─ extrair_tabela_imoveis()          # lê tabela HTML; fallback para imóvel único
       └─ aba_links.append(dados)           # escreve na aba "Link de Imóveis"
       └─ planilha.save()                   # salva após CADA imóvel com sucesso
       └─ atualizar_status_consultar()      # "Finalizado" (define Processar="Não")
```

### extracao_iptu

```
main.py
  └─ carregar_planilha()                    # utils.py
  └─ Coleta imóveis com col. K = "Sim"
  └─ Divide em N chunks intercalados
  └─ ThreadPoolExecutor(max_workers=N)
       └─ worker(id, chunk, ...)            # N workers em paralelo
            └─ iniciar_driver(headless=True)
            └─ CaptchaCache()               # cache local por worker
            └─ Para cada imóvel no chunk:
                 └─ processar_imovel()
                      └─ realizar_login()
                           └─ CaptchaCache.reusable?
                              Sim → reutiliza texto do CAPTCHA
                              Não → resolver_captcha() (OCR)
                           └─ Login OK → cache.update()
                           └─ Login FALHOU com cache → cache.invalidate()
                      └─ capturar_inscricao_imobiliaria()
                      └─ capturar_dados_adicionais()
                           └─ Imóvel Baldio? → preenche "Baldio s/uso"
                      └─ acessar_carne_iptu()
                      └─ extrair_tabela_iptu()
                           └─ Sem parcelas → "Sem Lançamento IPTU"
                           └─ Com parcelas → classifica (Cota/Parcelado)
                      └─ _planilha_lock:
                           └─ salvar_dados_na_aba()     # "Banco de Dados"
                           └─ atualizar_status_iptu()   # col. L = "Sim"
                           └─ atualizar_dados_imovel()  # cols. M–Q
```

---

## Resolução de CAPTCHA

O portal e-IPTU exibe um CAPTCHA numérico em cada login. O projeto resolve isso de forma automática com a seguinte estratégia:

### OCR com EasyOCR

1. A imagem do CAPTCHA é capturada diretamente do atributo `src` do elemento `<img>` (base64)
2. A imagem é convertida para escala de cinza e processada pelo `easyocr.Reader(['en'])`
3. O texto extraído é digitado automaticamente no campo do CAPTCHA
4. O arquivo temporário é deletado após o uso

O `Reader` do EasyOCR é inicializado como **singleton lazy** — carregado apenas uma vez na primeira chamada, compartilhado entre threads via `threading.Lock` para evitar inicializações concorrentes.

### Cache de CAPTCHA (Passo 2)

O site apresenta um comportamento documentado: **a partir do 3º login em uma mesma sessão do browser, o CAPTCHA não muda mais**. O `CaptchaCache` aproveita isso:

```
Login 1: CAPTCHA = "7392" → OCR → login OK → cache.update("7392"), count=1
Login 2: CAPTCHA = "8541" → OCR → login OK → cache.update("8541"), count=2
Login 3: cache.reusable = True → reutiliza "8541" sem chamar OCR
Login 4: reutiliza "8541"
...
Login N: reutiliza "8541"

Se login falhar com o cache → cache.invalidate() → próxima tentativa usa OCR
```

Isso elimina o custo de OCR para a grande maioria dos imóveis, acelerando significativamente o Passo 2.

---

## Execução Paralela

O Passo 2 usa `ThreadPoolExecutor` para processar múltiplos imóveis simultaneamente, cada worker com seu próprio browser e cache:

```
imoveis = [1, 2, 3, 4, 5, 6, 7, 8, 9]
n_workers = 3

chunk[0] = [1, 4, 7]   → Worker 1 (browser próprio)
chunk[1] = [2, 5, 8]   → Worker 2 (browser próprio)
chunk[2] = [3, 6, 9]   → Worker 3 (browser próprio)
```

A distribuição intercalada (`imoveis[i::n]`) garante que os workers percorram a lista de forma uniforme, sem sobreposição.

**Thread Safety:** todas as operações de leitura e escrita na planilha são protegidas por um `threading.Lock` global (`_planilha_lock`). Cada worker solicita o lock, realiza sua gravação e libera — garantindo que nunca dois workers escrevam ao mesmo tempo.

**Configuração recomendada de workers:**

| Máquina | `n_workers` sugerido |
|---|---|
| 4 GB RAM | 2 |
| 8 GB RAM | 3 |
| 16 GB RAM | 4–5 |

> Cada browser Edge em headless consome ~200–400 MB de RAM.

---

## Tratamento de Erros

### Categorias de status na coluna `IPTU Extraído?`

| Status | Significa |
|---|---|
| `Sim` | IPTU extraído com sucesso |
| `Sem Lançamento IPTU` | Imóvel sem carnê disponível no portal |
| `Erro de Conexão` | Falha de rede detectada (timeout, DNS, internet caída) |
| `Erro de Processamento` | Qualquer outro erro (CAPTCHA inválido, elemento não encontrado, etc.) |

O sistema identifica erros de rede pelo texto da exceção, buscando padrões como:
`err_connection_timed_out`, `err_name_not_resolved`, `err_internet_disconnected`, `net::err_`, entre outros.

Isso permite filtrar na planilha os imóveis que falharam por queda de internet (re-tentáveis) dos que tiveram erro no próprio processamento (que podem precisar de investigação manual).

### Estratégia de retentativas

- **Passo 1:** até 3 tentativas por CNPJ/CPF
- **Passo 2:** até 2 tentativas de login por imóvel (configurável em `SETTINGS["max_tentativas_login"]` no `config.py`)
- Imóveis com erro não bloqueiam os demais — o worker registra o status e segue para o próximo

### Salvamento incremental

- **Passo 1:** a planilha é salva após cada CNPJ/CPF processado com sucesso
- **Passo 2:** a planilha é salva após cada imóvel (após cada escrita na aba `Banco de Dados` e atualização de status)

Em caso de crash ou interrupção, apenas o imóvel em processamento no momento pode ser perdido. Todos os anteriores estão salvos.

---

## Solução de Problemas

### `0 linhas encontradas para processamento`

Verifique se:
1. O caminho da planilha em `settings.ini` está correto e aponta para o arquivo certo
2. A coluna `Processar` (col. E) está com valor `Sim` (não `SIM`, não `sim`)
3. O arquivo não está aberto no Excel (isso pode travar a leitura)

### `No module named 'easyocr'` ou `No module named 'numpy'`

O ambiente virtual não está ativado ou as dependências não foram instaladas:
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### EasyOCR demora muito na primeira execução

Normal. O EasyOCR baixa os modelos de rede neural (~200 MB) na primeira vez. A partir da segunda execução, os modelos já estão em cache local.

### O browser abre mas não faz nada / trava na página de login

- Tente definir `headless = false` no `settings.ini` para visualizar o que está acontecendo
- Execute `.\scripts\diagnose.ps1` para verificar se o portal está acessível
- Verifique se a internet está estável

### `Device or resource busy` ao tentar remover diretório travado

O diretório está sendo mantido por um processo ativo. Reinicie o terminal ou o computador e execute:
```powershell
Remove-Item -Path "<caminho>" -Recurse -Force
```

### CAPTCHA resolvido incorretamente com frequência

O OCR pode confundir caracteres similares. Isso é esperado ocasionalmente — o sistema tentará novamente automaticamente. Se a taxa de erro for alta, verifique se o EasyOCR está usando GPU (mais preciso) ou experimente instalar o PyTorch com suporte a CUDA.

---

## Tecnologias Utilizadas

| Tecnologia | Versão | Papel |
|---|---|---|
| [Python](https://www.python.org/) | 3.11 / 3.12 | Linguagem principal |
| [Selenium](https://www.selenium.dev/) | 4.41.0 | Automação do browser Edge |
| [openpyxl](https://openpyxl.readthedocs.io/) | 3.1.5 | Leitura e escrita de arquivos `.xlsx` |
| [EasyOCR](https://github.com/JaidedAI/EasyOCR) | 1.7.2 | Reconhecimento de texto no CAPTCHA |
| [Pillow](https://python-pillow.org/) | 12.1.1 | Processamento de imagem do CAPTCHA |
| [NumPy](https://numpy.org/) | 2.4.2 | Conversão da imagem para array |
| [PyTorch](https://pytorch.org/) | 2.10.0 | Backend de inferência do EasyOCR |
| [OpenCV](https://opencv.org/) | 4.13.0 | Pré-processamento de imagem (EasyOCR) |
| [ThreadPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html) | stdlib | Execução paralela de workers |
| [configparser](https://docs.python.org/3/library/configparser.html) | stdlib | Leitura do `settings.ini` |
| Microsoft Edge + Selenium Manager | — | Browser controlado; driver gerenciado automaticamente |

---

> Desenvolvido para automação interna de consultas ao portal e-IPTU da Prefeitura de Caçador (SC).
