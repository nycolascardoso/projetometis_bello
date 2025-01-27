# Caminho da planilha
PLANILHA_PATH = 'C:/Users/ngcar/OneDrive/Documentos/Python Scripts/Projeto Metis/Banco_de_Imoveis.xlsx'

# Caminho do driver
DRIVER_PATH = "C:/Users/ngcar/edgedriver_win64/msedgedriver.exe"

# URL de login
URL_LOGIN = "https://nfse1.publica.inf.br/cacador_eiptu/"

# Seletores
SELECTORS = {
    "login_selector": "cbLogin",  # Seletor do tipo de documento
    "input_campo": '//*[@id="inscri"]',  # Campo de entrada para CNPJ/CPF
    "botao_login": '//*[@id="form_index_proprietario"]/table[2]/tbody/tr/td/input[1]',  # Botão "Login"
    "tabela_imoveis": '/html/body/div[1]/div[1]/div[2]/form/table',  # XPATH completo da tabela de imóveis
    "tabela_linhas": './/tbody/tr',  # Linhas da tabela
    "tabela_celula_link": './/td[1]/a',  # Link do imóvel na tabela
    "tabela_celula_codigo": './/td[2]',  # Código do imóvel
    "tabela_celula_inscricao": './/td[3]',  # Inscrição imobiliária
    "tabela_celula_logradouro": './/td[4]',  # Logradouro
    "tabela_celula_complemento": './/td[5]',  # Complemento
    "tabela_celula_bairro": './/td[6]',  # Bairro
    "tabela_celula_situacao": './/td[7]',  # Situação
    "mensagem_erro": "/html/body/div/div[1]/div[2]/div[1]"  # XPath da mensagem de erro
}
