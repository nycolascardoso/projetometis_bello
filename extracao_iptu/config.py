from configparser import ConfigParser
from pathlib import Path

_cfg = ConfigParser()
_cfg.read(Path(__file__).resolve().parents[1] / 'settings.ini', encoding='utf-8')

# Caminho da planilha
PLANILHA_PATH = _cfg.get('paths', 'planilha')

# Caminho do WebDriver (fallback manual)
DRIVER_PATH = _cfg.get('paths', 'driver')

# URLs do sistema
URL_LOGIN = "https://tmi-apps.e-publica.net/cacador_eiptu/"
URL_CARNE_IPTU = "https://tmi-apps.e-publica.net/cacador_eiptu/jsp/portal/consultaDebitoIptu.jsp"

# Configurações gerais
SETTINGS = {
    "max_tentativas_login": 4,    # tentativas externas de login por imóvel
    "max_tentativas_captcha": 3,  # tentativas de OCR por login (loop interno)
    "timeout_padrao": 10,
}

# Seletores para login e elementos do site
SELECTORS = {
    "login_selector": "cbLogin",
    "input_campo": '//*[@id="inscri"]',
    "captcha_image": '//*[@id="form_index_proprietario"]/table[1]/tbody/tr[3]/td[1]/div/img',
    "captcha_input": '//*[@id="cod"]',
    "botao_login": '//*[@id="form_index_proprietario"]/table[2]/tbody/tr/td/input[1]',
    "mensagem_erro": "/html/body/div/div[1]/div[2]/div[1]",
    "inscricao_imobiliaria": '//*[@id="agrupador-area"]/div[2]/div[2]/div/div/table/tbody/tr[2]/td[2]/input',
    "localizacao": '//*[@id="agrupador-area"]/div[2]/div[10]/div/div/table/tbody/tr[3]/td[6]/input',
    "tipologia": '//*[@id="agrupador-area"]/div[2]/div[10]/div/div/table/tbody/tr[2]/td[4]/input',
    "estrutura": '//*[@id="agrupador-area"]/div[2]/div[10]/div/div/table/tbody/tr[4]/td[2]/input',
    "utilizacao": '//*[@id="agrupador-area"]/div[2]/div[10]/div/div/table/tbody/tr[5]/td[4]/input',
    "proprietario": '//*[@id="agrupador-area"]/div[2]/div[2]/div/div/table/tbody/tr[1]/td[2]/input',
    "ocupacao": '//*[@id="agrupador-area"]/div[2]/div[6]/div/div/table/tbody/tr[4]/td[6]/input'
}

# Seletores para imóvel individual
SINGLE_IMOVEL_SELECTORS = {
    "codigo_imovel": '//*[@id="agrupador-area"]/div[2]/div[2]/div/div/table/tbody/tr[1]/td[2]/input'
}

# Configurações de execução paralela
EXECUTION = {
    "n_workers": _cfg.getint('execution', 'n_workers', fallback=3),
    "headless": _cfg.getboolean('execution', 'headless', fallback=True),
}

# Seletores para a tabela do Carnê IPTU
TABLE_SELECTORS = {
    "elemento_tabela_iptu": '//*[@id="frm_lista_debitos"]/table',
    "linhas_tabela_iptu": '//*[@id="frm_lista_debitos"]/table/tbody/tr',
    "colunas_tabela_iptu": './/td'
}
