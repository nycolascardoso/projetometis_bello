import os

# Pasta raiz do projeto (onde está o Banco_de_Imoveis.xlsx)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Caminho da planilha (relativo ao projeto)
PLANILHA_PATH = os.path.join(BASE_DIR, 'Banco_de_Imoveis.xlsx')

# Arquivo de status em tempo real (usado pelo app Streamlit)
STATUS_PATH = os.path.join(BASE_DIR, 'runtime_status.json')

# Caminho do driver (Selenium Manager gerencia automaticamente; manter para fallback)
DRIVER_PATH = "C:/Users/ngcar/edgedriver_win64/msedgedriver.exe"

# URL de login
URL_LOGIN = "https://nfse1.publica.inf.br/cacador_eiptu/"

# Seletores para página de login e para a extração da tabela de imóveis (caso haja mais de um imóvel)
SELECTORS = {
    "login_selector": "cbLogin",  # Seletor do tipo de documento
    "input_campo": '//*[@id="inscri"]',  # Campo de entrada para CNPJ/CPF
    "botao_login": '//*[@id="form_index_proprietario"]/table[2]/tbody/tr/td/input[1]',  # Botão "Login"
    "tabela_imoveis": '/html/body/div[1]/div[1]/div[2]/form/table',  # XPath completo da tabela de imóveis
    "tabela_linhas": './/tbody/tr',  # Linhas da tabela
    "tabela_celula_link": './/td[1]/a',  # Link do imóvel na tabela
    "tabela_celula_codigo": './/td[2]',  # Código do imóvel
    "tabela_celula_inscricao": './/td[3]',  # Inscrição imobiliária
    "tabela_celula_logradouro": './/td[4]',  # Logradouro
    "tabela_celula_complemento": './/td[5]',  # Complemento
    "tabela_celula_bairro": './/td[6]',  # Bairro
    "tabela_celula_situacao": './/td[7]',  # Situação
    "mensagem_erro": "/html/body/div/div[1]/div[2]/div[1]",  # XPath da mensagem de erro
    "captcha_image": '//*[@id="form_index_proprietario"]/table[1]/tbody/tr[3]/td[1]/div/img',  # XPath da imagem do CAPTCHA
    "captcha_input": '//*[@id="cod"]'  # XPath do campo de entrada do CAPTCHA
}

# Seletores para página de imóvel único (quando existir apenas um imóvel)
SINGLE_IMOVEL_SELECTORS = {
    "codigo_imovel": '/html/body/div/div[1]/div[2]/div[8]/div/div/table/tbody/tr[2]/td[2]/input',
    "inscricao_imobiliaria": '//*[@id="agrupador-area"]/div[2]/div[2]/div/div/table/tbody/tr[2]/td[2]/input',
    "logradouro": '//*[@id="agrupador-area"]/div[2]/div[2]/div/div/table/tbody/tr[3]/td[2]/input',
    "complemento": '//*[@id="agrupador-area"]/div[2]/div[2]/div/div/table/tbody/tr[4]/td[2]/input',
    "bairro": '//*[@id="agrupador-area"]/div[2]/div[2]/div/div/table/tbody/tr[4]/td[4]/input',
    "situacao": '//*[@id="agrupador-area"]/div[2]/div[2]/div/div/table/tbody/tr[2]/td[4]/input'
}