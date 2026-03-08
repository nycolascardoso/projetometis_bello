import os

# 🔹 Pasta raiz do projeto (onde está o Banco_de_Imoveis.xlsx)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 🔹 Caminho da planilha (relativo ao projeto)
PLANILHA_PATH = os.path.join(BASE_DIR, 'Banco_de_Imoveis.xlsx')

# 🔹 Arquivo de status em tempo real (usado pelo app Streamlit)
STATUS_PATH = os.path.join(BASE_DIR, 'runtime_status.json')

# 🔹 Caminho do WebDriver (Selenium Manager gerencia automaticamente; manter para fallback)
DRIVER_PATH = "C:/Users/ngcar/edgedriver_win64/msedgedriver.exe"

# 🔹 URLs do sistema
URL_LOGIN = "https://nfse1.publica.inf.br/cacador_eiptu/"
URL_CARNE_IPTU = "https://nfse1.publica.inf.br/cacador_eiptu/jsp/portal/consultaDebitoIptu.jsp"

# 🔹 Configurações gerais
SETTINGS = {
    "max_tentativas_login": 2,  # Máximo de tentativas de login antes de desistir
    "max_tentativas_captcha": 2,  # Máximo de tentativas para resolver CAPTCHA
    "timeout_padrao": 10,  # Tempo de espera do Selenium (segundos)
}

# 🔹 Seletores para login e elementos do site
SELECTORS = {
    "login_selector": "cbLogin",
    "input_campo": '//*[@id="inscri"]',
    "captcha_image": '//*[@id="form_index_proprietario"]/table[1]/tbody/tr[3]/td[1]/div/img',
    "captcha_input": '//*[@id="cod"]',
    "botao_login": '//*[@id="form_index_proprietario"]/table[2]/tbody/tr/td/input[1]',
    "mensagem_erro": "/html/body/div/div[1]/div[2]/div[1]",

    # 🔹 Informações do imóvel na página pós-login
    "inscricao_imobiliaria": '//*[@id="agrupador-area"]/div[2]/div[2]/div/div/table/tbody/tr[2]/td[2]/input',
    "localizacao": '//*[@id="agrupador-area"]/div[2]/div[10]/div/div/table/tbody/tr[3]/td[6]/input',
    "tipologia": '//*[@id="agrupador-area"]/div[2]/div[10]/div/div/table/tbody/tr[2]/td[4]/input',
    "estrutura": '//*[@id="agrupador-area"]/div[2]/div[10]/div/div/table/tbody/tr[4]/td[2]/input',
    "utilizacao": '//*[@id="agrupador-area"]/div[2]/div[10]/div/div/table/tbody/tr[5]/td[4]/input',
    "proprietario": '//*[@id="agrupador-area"]/div[2]/div[2]/div/div/table/tbody/tr[1]/td[2]/input',
    "ocupacao": '//*[@id="agrupador-area"]/div[2]/div[6]/div/div/table/tbody/tr[4]/td[6]/input'
}

# 🔹 Seletores para imóveis individuais
SINGLE_IMOVEL_SELECTORS = {
    "codigo_imovel": '//*[@id="agrupador-area"]/div[2]/div[2]/div/div/table/tbody/tr[1]/td[2]/input'
}

# 🔹 Seletores para a tabela do Carnê IPTU
TABLE_SELECTORS = {
    "elemento_tabela_iptu": '//*[@id="frm_lista_debitos"]/table',  # 🟢 Renomeado para evitar conflito
    "linhas_tabela_iptu": '//*[@id="frm_lista_debitos"]/table/tbody/tr',
    "colunas_tabela_iptu": './/td'
}

