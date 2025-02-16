from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime
import numpy as np
import time
import base64
from io import BytesIO
from PIL import Image
import easyocr
from extracao_iptu.config import DRIVER_PATH, SELECTORS, URL_LOGIN, SINGLE_IMOVEL_SELECTORS, PLANILHA_PATH

# Inicia o WebDriver
def iniciar_driver():
    """Inicia o driver do Selenium."""
    from selenium.webdriver.edge.service import Service
    from selenium.webdriver.edge.options import Options

    service = Service(executable_path=DRIVER_PATH)
    options = Options()
    options.add_argument("start-maximized")
    return webdriver.Edge(service=service, options=options)

# Resolve o CAPTCHA (se necessário)
def resolver_captcha(driver):
    """Resolve o CAPTCHA e retorna o texto lido."""
    try:
        print("🟡 Buscando a imagem do CAPTCHA...")
        captcha_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, SELECTORS["captcha_image"]))
        )

        print("📸 Capturando imagem do CAPTCHA...")
        captcha_base64 = captcha_element.get_attribute("src").split(",")[-1]
        captcha_bytes = base64.b64decode(captcha_base64)
        captcha_image = Image.open(BytesIO(captcha_bytes))

        # Salva a imagem temporariamente para depuração
        captcha_image.save("captcha_temp.png")
        print("💾 CAPTCHA salvo como 'captcha_temp.png'")

        # Carrega a imagem salva e converte para NumPy array
        captcha_image = Image.open("captcha_temp.png").convert("L")  # Converte para escala de cinza
        captcha_array = np.array(captcha_image)  # Converte para array NumPy

        # Processa a imagem com EasyOCR
        print("🧐 Lendo CAPTCHA com OCR...")
        reader = easyocr.Reader(["en"])
        result = reader.readtext(captcha_array, detail=0)

        captcha_text = result[0] if result else ""
        print(f"🟢 CAPTCHA resolvido: {captcha_text}")

        return captcha_text

    except Exception as e:
        print(f"❌ Erro ao resolver CAPTCHA: {e}")
        return ""


# Realiza login no sistema
def realizar_login(driver, codigo_imovel):
    """Realiza o login e verifica se foi bem-sucedido, resolvendo o CAPTCHA."""
    try:
        print(f"Tentando login com código do imóvel: {codigo_imovel}")
        driver.get(URL_LOGIN)
        time.sleep(2)

        # Seleciona o tipo de login e insere o código do imóvel
        seletor_login = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, SELECTORS["login_selector"]))
        )
        seletor_login.send_keys("Cód. do imóvel")

        campo_codigo = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, SELECTORS["input_campo"]))
        )
        driver.execute_script("arguments[0].value = arguments[1];", campo_codigo, codigo_imovel)

        # Resolve o CAPTCHA
        captcha_text = resolver_captcha(driver)
        if not captcha_text:
            raise Exception("Falha ao resolver CAPTCHA")
        captcha_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, SELECTORS["captcha_input"]))
        )
        captcha_input.send_keys(captcha_text)
 
        time.sleep(3)  # Aguarda antes de enviar o formulário

        # Clica no botão de login
        botao_login = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, SELECTORS["botao_login"]))
        )
        botao_login.click()

        # Aguarda até que algum dos seguintes elementos apareça:
        WebDriverWait(driver, 10).until(
            lambda d: d.find_elements(By.XPATH, SELECTORS["mensagem_erro"]) or
                      d.find_elements(By.XPATH, SELECTORS["tabela_imoveis"]) or
                      d.find_elements(By.XPATH, SINGLE_IMOVEL_SELECTORS["codigo_imovel"])
        )

        # Verifica se há mensagem de erro
        erro_elems = driver.find_elements(By.XPATH, SELECTORS["mensagem_erro"])
        if erro_elems:
            erro_text = erro_elems[0].text.strip()
            if erro_text:
                print(f"❌ Erro de login: {erro_text}")
                raise Exception(f"Erro de login: {erro_text}")

        # Verifica se o login foi bem-sucedido
        if driver.find_elements(By.XPATH, SELECTORS["tabela_imoveis"]):
            print("🟢 Login realizado com sucesso! Tela 2 (tabela) detectada.")
        elif driver.find_elements(By.XPATH, SINGLE_IMOVEL_SELECTORS["codigo_imovel"]):
            print("🟢 Login realizado com sucesso! Imóvel único detectado.")
        else:
            raise Exception("❌ Erro: Nenhum elemento de sucesso encontrado.")

    except Exception as e:
        print(f"🔴 Erro ao realizar login: {e}")
        raise

# Navega até a página do Carnê IPTU
def acessar_carnê_iptu(driver):
    """Acessa diretamente a página do Carnê IPTU."""
    try:
        print("🔗 Acessando página do Carnê IPTU...")
        driver.get(SELECTORS["pagina_consulta"])
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, SELECTORS["tabela_iptu"]))
        )
        print("🟢 Página do Carnê IPTU carregada.")
    except Exception as e:
        print(f"❌ Erro ao acessar Carnê IPTU: {e}")
        raise

# Extrai os dados da tabela de IPTU
def extrair_tabela_iptu(driver):
    """Extrai os dados da tabela de IPTU."""
    try:
        print("📋 Extraindo tabela de IPTU...")
        tabela = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, SELECTORS["tabela_iptu"]))
        )

        # Captura todas as linhas da tabela
        linhas = tabela.find_elements(By.XPATH, ".//tr")
        if not linhas:
            raise Exception("Nenhuma linha encontrada na tabela de IPTU.")

        print(f"🟢 {len(linhas)} linhas encontradas na tabela de IPTU.")

        dados = []
        for linha in linhas:
            colunas = linha.find_elements(By.XPATH, ".//td")  # Captura todas as células
            valores = [col.text.strip() for col in colunas]

            if valores:  # Ignora linhas vazias
                dados.append(valores)

        return dados  # Garante que estamos retornando uma lista de listas

    except Exception as e:
        print(f"❌ Erro ao extrair tabela IPTU: {e}")
        raise

