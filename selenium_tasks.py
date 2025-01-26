from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from config import DRIVER_PATH, SELECTORS, URLS
from utils import registrar_log, salvar_links, salvar_dados_banco

# Configuração do WebDriver
def iniciar_driver():
    from selenium.webdriver.edge.service import Service
    from selenium.webdriver.edge.options import Options

    service = Service(executable_path=DRIVER_PATH)
    options = Options()
    options.add_argument("start-maximized")
    return webdriver.Edge(service=service, options=options)

# Função para extrair links de imóveis
def extrair_links_imoveis(driver):
    """
    Extrai os links de todos os imóveis disponíveis na tabela.
    """
    links_imoveis = []
    try:
        tabela = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, SELECTORS["tabela_imoveis"]))
        )
        linhas = tabela.find_elements(By.XPATH, './/tbody/tr')

        for linha in linhas:
            try:
                link_elemento = linha.find_element(By.XPATH, SELECTORS["coluna_link"])
                link_url = link_elemento.get_attribute('href')
                codigo_imovel = linha.find_element(By.XPATH, SELECTORS["coluna_codigo_imovel"]).text.strip()
                inscricao_imobiliaria = linha.find_element(By.XPATH, SELECTORS["coluna_inscricao_imobiliaria"]).text.strip()
                links_imoveis.append({
                    "link": link_url,
                    "codigo_imovel": codigo_imovel,
                    "inscricao_imobiliaria": inscricao_imobiliaria
                })
            except Exception as e:
                print(f"Erro ao capturar link: {e}")
                continue
    except Exception as e:
        print(f"Erro ao localizar tabela de imóveis: {e}")
    return links_imoveis

# Função para processar débitos de um imóvel
def processar_debitos(driver, cnpj_cpf, codigo_imovel, aba_banco_dados):
    """
    Extrai a tabela de débitos de um imóvel e salva os dados na aba 'Banco de Dados'.
    """
    try:
        # Aguarda a tabela de débitos ser carregada
        tabela = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, SELECTORS["tabela_debitos"]))
        )
        linhas = tabela.find_elements(By.XPATH, './/tbody/tr')
        dados = []

        for linha in linhas:
            celulas = linha.find_elements(By.TAG_NAME, 'td')
            linha_dados = [celula.text.strip() for celula in celulas]
            dados.append(linha_dados)

        # Salvar os dados na aba "Banco de Dados"
        salvar_dados_banco(aba_banco_dados, cnpj_cpf, codigo_imovel, dados)

    except Exception as e:
        print(f"Erro ao processar débitos: {e}")

# Função principal para consultar um imóvel
def consultar_imovel(driver, cnpj_cpf, tipo_doc, planilha, aba_links, aba_banco_dados, aba_log):
    """
    Realiza a consulta de um imóvel e processa as informações.
    """
    try:
        # Acessa a página de login
        driver.get(URLS["login"])
        time.sleep(2)

        # Preenche o tipo de documento e o valor correspondente
        seletor = driver.find_element(By.ID, SELECTORS["login_selector"])
        seletor.send_keys(tipo_doc)

        campo = driver.find_element(By.XPATH, SELECTORS["input_campo"])
        driver.execute_script("arguments[0].value = arguments[1];", campo, cnpj_cpf)

        # Realiza o login
        botao_login = driver.find_element(By.XPATH, SELECTORS["botao_login"])
        botao_login.click()
        time.sleep(3)

        # Extrai os links dos imóveis
        links = extrair_links_imoveis(driver)

        # Salvar os links na aba "Link de Imóveis"
        salvar_links(aba_links, cnpj_cpf, links, PLANILHA_PATH)

        # Processar débitos para cada imóvel
        for link in links:
            driver.get(link["link"])
            time.sleep(2)
            processar_debitos(driver, cnpj_cpf, link["codigo_imovel"], aba_banco_dados)

        # Registrar sucesso no log
        registrar_log(aba_log, cnpj_cpf, tipo_doc, "Sucesso", "Consulta realizada com sucesso.")

    except Exception as e:
        registrar_log(aba_log, cnpj_cpf, tipo_doc, "Erro", str(e))

