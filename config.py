# Caminho da planilha
PLANILHA_PATH = 'C:/Users/ngcar/OneDrive/Documentos/Python Scripts/Projeto Metis/Banco_de_Imoveis.xlsx'

# Caminho do driver
DRIVER_PATH = "C:/Users/ngcar/edgedriver_win64/msedgedriver.exe"

# URLs
URLS = {
    "login": "https://nfse1.publica.inf.br/cacador_eiptu/",
    "gerenciamento": "https://nfse1.publica.inf.br/cacador_eiptu/jsp/debito/gerenciamento/index.jsp#",
    "home": "https://nfse1.publica.inf.br/cacador_eiptu/jsp/portal/home.jsp"
}

# Seletores HTML
SELECTORS = {
    # Tela de login
    "login_selector": "cbLogin",
    "input_campo": '//*[@id="inscri"]',
    "botao_login": '//*[@id="form_index_proprietario"]/table[2]/tbody/tr/td/input[1]',

    # Tela de gerenciamento
    "tabela_debitos": '//*[@id="frm_lista_debitos"]//table',
    "botao_proximo": '//a[text()="Próximo"]',

    # Tela de imóveis
    "tabela_imoveis": 'tableDados',
    "coluna_link": './/td[1]/a',
    "coluna_codigo_imovel": './/td[2]',
    "coluna_inscricao_imobiliaria": './/td[3]',
    "coluna_logradouro": './/td[4]',
    "coluna_complemento": './/td[5]',
    "coluna_bairro": './/td[6]',
    "coluna_situacao": './/td[7]',

    # Dropdown do cabeçalho
    "menu_valores_iptu": '//a[text()="Valores IPTU"]',
    "dropdown_consultar_emitir": '//a[text()="Consultar/Emitir débitos de IPTU"]'
}

# Timeout padrão para espera explícita
DEFAULT_TIMEOUT = 10

# Configuração do WebDriver
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options

def iniciar_driver():
    """
    Configura e inicia o WebDriver do Selenium para Microsoft Edge.
    """
    service = Service(executable_path=DRIVER_PATH)
    options = Options()
    options.add_argument("start-maximized")
    driver = webdriver.Edge(service=service, options=options)
    return driver
