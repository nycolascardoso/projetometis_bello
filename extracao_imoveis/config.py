from configparser import ConfigParser
from pathlib import Path

_cfg = ConfigParser()
_cfg.read(Path(__file__).resolve().parents[1] / 'settings.ini', encoding='utf-8')

# Caminho da planilha
PLANILHA_PATH = _cfg.get('paths', 'planilha')

# Caminho do driver (fallback manual)
DRIVER_PATH = _cfg.get('paths', 'driver')

# URL de login
URL_LOGIN = "https://tmi-apps.e-publica.net/cacador_eiptu/"

# Seletores para página de login e extração da tabela de imóveis (múltiplos imóveis)
SELECTORS = {
    "login_selector": "cbLogin",
    "input_campo": '//*[@id="inscri"]',
    "botao_login": '//*[@id="form_index_proprietario"]/table[2]/tbody/tr/td/input[1]',
    "tabela_imoveis": '/html/body/div[1]/div[1]/div[2]/form/table',
    "tabela_linhas": './/tbody/tr',
    "tabela_celula_link": './/td[1]/a',
    "tabela_celula_codigo": './/td[2]',
    "tabela_celula_inscricao": './/td[3]',
    "tabela_celula_logradouro": './/td[4]',
    "tabela_celula_complemento": './/td[5]',
    "tabela_celula_bairro": './/td[6]',
    "tabela_celula_situacao": './/td[7]',
    "mensagem_erro": "/html/body/div/div[1]/div[2]/div[1]",
    "captcha_image": '//*[@id="form_index_proprietario"]/table[1]/tbody/tr[3]/td[1]/div/img',
    "captcha_input": '//*[@id="cod"]'
}

# Seletores para página de imóvel único (apenas um imóvel vinculado ao CPF/CNPJ)
SINGLE_IMOVEL_SELECTORS = {
    "codigo_imovel": '/html/body/div/div[1]/div[2]/div[8]/div/div/table/tbody/tr[2]/td[2]/input',
    "inscricao_imobiliaria": '//*[@id="agrupador-area"]/div[2]/div[2]/div/div/table/tbody/tr[2]/td[2]/input',
    "logradouro": '//*[@id="agrupador-area"]/div[2]/div[2]/div/div/table/tbody/tr[3]/td[2]/input',
    "complemento": '//*[@id="agrupador-area"]/div[2]/div[2]/div/div/table/tbody/tr[4]/td[2]/input',
    "bairro": '//*[@id="agrupador-area"]/div[2]/div[2]/div/div/table/tbody/tr[4]/td[4]/input',
    "situacao": '//*[@id="agrupador-area"]/div[2]/div[2]/div/div/table/tbody/tr[2]/td[4]/input'
}
