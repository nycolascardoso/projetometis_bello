# Caminho da planilha
PLANILHA_PATH = 'C:/Users/ngcar/OneDrive/Documentos/Python Scripts/Projeto Metis/Banco_de_Imoveis.xlsx'

# Caminho do driver
DRIVER_PATH = "C:/Users/ngcar/edgedriver_win64/msedgedriver.exe"

# URL de login
URL_LOGIN = "https://nfse1.publica.inf.br/cacador_eiptu/"

# URL da aba do Carnê IPTU
URL_CARNE_IPTU = "https://nfse1.publica.inf.br/cacador_eiptu/jsp/portal/consultaDebitoIptu.jsp"

# Seletores para página de login e extração
SELECTORS = {
    "login_selector": "cbLogin",  # Seletor do tipo de login
    "input_campo": '//*[@id="inscri"]',  # Campo do Código do Imóvel
    "captcha_image": '//*[@id="form_index_proprietario"]/table[1]/tbody/tr[3]/td[1]/div/img',  # CAPTCHA
    "captcha_input": '//*[@id="cod"]',  # Entrada do CAPTCHA
    "botao_login": '//*[@id="form_index_proprietario"]/table[2]/tbody/tr/td/input[1]',  # Botão de login
    "tabela_iptu": '//*[@id="frm_lista_debitos"]/table',  # Tabela de dados IPTU
    "tabela_imoveis": '/html/body/div[1]/div[1]/div[2]/form/table',  # XPath completo da tabela de imóveis
    "mensagem_erro": "/html/body/div/div[1]/div[2]/div[1]",  # XPath da mensagem de erro
    "pagina_consulta": "https://nfse1.publica.inf.br/cacador_eiptu/jsp/portal/consultaDebitoIptu.jsp"
}

SINGLE_IMOVEL_SELECTORS = {
    "codigo_imovel": '/html/body/div/div[1]/div[2]/div[8]/div/div/table/tbody/tr[2]/td[2]/input',
}
# Caso surjam novos elementos que precisem de seletores adicionais, poderão ser incluídos aqui.
