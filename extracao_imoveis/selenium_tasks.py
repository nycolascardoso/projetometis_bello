import base64
import os
import tempfile
import numpy as np
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from extracao_imoveis.config import DRIVER_PATH, SELECTORS, URL_LOGIN, SINGLE_IMOVEL_SELECTORS
from datetime import datetime
import time


def iniciar_driver():
    """Inicia o driver do Selenium com configuração resiliente."""
    from selenium.webdriver.edge.options import Options
    options = Options()
    options.add_argument('start-maximized')
    try:
        return webdriver.Edge(options=options)
    except Exception:
        from selenium.webdriver.edge.service import Service
        service = Service(executable_path=DRIVER_PATH)
        return webdriver.Edge(service=service, options=options)


_EASYOCR_READER = None


def resolver_captcha(driver):
    """Resolve o CAPTCHA automaticamente utilizando OCR (lazy import)."""
    global _EASYOCR_READER
    try:
        print("🟡 Buscando a imagem do CAPTCHA...")
        captcha_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, SELECTORS["captcha_image"]))
        )

        print("📸 Capturando imagem do CAPTCHA...")
        captcha_base64 = captcha_element.get_attribute("src").split(",")[-1]
        captcha_bytes = base64.b64decode(captcha_base64)
        captcha_image = Image.open(BytesIO(captcha_bytes))

        captcha_temp = os.path.join(tempfile.gettempdir(), 'metis_captcha.png')
        captcha_image.save(captcha_temp)
        print(f"💾 CAPTCHA salvo temporariamente em '{captcha_temp}'")

        captcha_array = np.array(captcha_image.convert('L'))
        if _EASYOCR_READER is None:
            import easyocr
            _EASYOCR_READER = easyocr.Reader(['en'])
        result = _EASYOCR_READER.readtext(captcha_array, detail=0)

        captcha_text = result[0] if result else ""
        print(f"🟢 CAPTCHA resolvido: {captcha_text}")

        try:
            os.unlink(captcha_temp)
        except OSError:
            pass

        return captcha_text

    except Exception as e:
        print(f"❌ Erro ao resolver CAPTCHA: {e}")
        return ""


def realizar_login(driver, cnpj_cpf, tipo_doc):
    """Realiza login e trata CAPTCHA automaticamente."""
    try:
        print(f"Tentando login com {cnpj_cpf} ({tipo_doc})")
        driver.get(URL_LOGIN)
        print(f'Navegou para: {driver.current_url}')
        time.sleep(2)

        # Seleciona o tipo de documento
        sel_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, SELECTORS["login_selector"]))
        )
        try:
            Select(sel_elem).select_by_visible_text(tipo_doc)
        except Exception:
            options = [o.text.strip() for o in sel_elem.find_elements(By.TAG_NAME, 'option')]
            match = next((o for o in options if tipo_doc.lower() in o.lower()), None)
            if match:
                Select(sel_elem).select_by_visible_text(match)
            else:
                sel_elem.send_keys(tipo_doc)

        # Insere o CNPJ/CPF
        campo = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, SELECTORS["input_campo"]))
        )
        driver.execute_script("arguments[0].value = arguments[1];", campo, cnpj_cpf)

        # Resolve e insere o CAPTCHA
        captcha_text = resolver_captcha(driver)
        if not captcha_text:
            raise Exception("❌ Falha ao resolver CAPTCHA")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, SELECTORS["captcha_input"]))
        ).send_keys(captcha_text)
        print(f"⌨️ CAPTCHA inserido: {captcha_text}")

        time.sleep(3)

        # Clica no botão de login
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, SELECTORS["botao_login"]))
        ).click()

        # Aguarda resultado do login
        WebDriverWait(driver, 10).until(
            lambda d: d.find_elements(By.XPATH, SELECTORS["mensagem_erro"]) or
                      d.find_elements(By.XPATH, SELECTORS["tabela_imoveis"]) or
                      d.find_elements(By.XPATH, SINGLE_IMOVEL_SELECTORS["codigo_imovel"])
        )

        # Verifica se houve erro no login
        erro_elems = driver.find_elements(By.XPATH, SELECTORS["mensagem_erro"])
        if erro_elems:
            erro_text = erro_elems[0].text.strip()
            if erro_text:
                print(f"❌ Erro de login: {erro_text}")
                raise Exception(f"Erro de login: {erro_text}")

        if driver.find_elements(By.XPATH, SELECTORS["tabela_imoveis"]):
            print("🟢 Login realizado com sucesso! Tela de tabela de imóveis detectada.")
        elif driver.find_elements(By.XPATH, SINGLE_IMOVEL_SELECTORS["codigo_imovel"]):
            print("🟢 Login realizado com sucesso! Imóvel único detectado.")
        else:
            raise Exception("❌ Erro: Nenhum elemento de sucesso encontrado.")

    except Exception as e:
        print(f"🔴 Erro ao realizar login: {e}")
        raise


def extrair_tabela_imoveis(driver, cnpj_cpf, aba_links):
    """
    Extrai dados da tabela de imóveis ou, caso não encontre a tabela,
    tenta extrair como imóvel único.
    """
    try:
        tabela = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, SELECTORS["tabela_imoveis"]))
        )
        print("✅ Tabela de imóveis localizada.")
        linhas = tabela.find_elements(By.XPATH, SELECTORS["tabela_linhas"])

        if not linhas:
            raise Exception("❌ Nenhuma linha encontrada na tabela.")

        for linha in linhas:
            try:
                url_imovel = linha.find_element(By.XPATH, SELECTORS["tabela_celula_link"]).get_attribute('href')
                codigo_imovel = linha.find_element(By.XPATH, SELECTORS["tabela_celula_codigo"]).text.strip()
                inscricao_imobiliaria = linha.find_element(By.XPATH, SELECTORS["tabela_celula_inscricao"]).text.strip()
                logradouro = linha.find_element(By.XPATH, SELECTORS["tabela_celula_logradouro"]).text.strip()
                complemento = linha.find_element(By.XPATH, SELECTORS["tabela_celula_complemento"]).text.strip()
                bairro = linha.find_element(By.XPATH, SELECTORS["tabela_celula_bairro"]).text.strip()
                situacao = linha.find_element(By.XPATH, SELECTORS["tabela_celula_situacao"]).text.strip()

                aba_links.append([
                    cnpj_cpf, codigo_imovel, inscricao_imobiliaria, logradouro,
                    complemento, bairro, situacao, url_imovel, "Em progresso",
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ])
                print(f"✅ Imóvel {codigo_imovel} extraído com sucesso.")

            except NoSuchElementException:
                print("❌ Erro ao extrair dados de uma linha da tabela.")

    except TimeoutException:
        print("❌ Tabela não encontrada. Tentando extração como imóvel único...")

        try:
            codigo_imovel = driver.find_element(By.XPATH, SINGLE_IMOVEL_SELECTORS["codigo_imovel"]).get_attribute("value").strip()
            inscricao_imobiliaria = driver.find_element(By.XPATH, SINGLE_IMOVEL_SELECTORS["inscricao_imobiliaria"]).get_attribute("value").strip()
            logradouro = driver.find_element(By.XPATH, SINGLE_IMOVEL_SELECTORS["logradouro"]).get_attribute("value").strip()
            complemento = driver.find_element(By.XPATH, SINGLE_IMOVEL_SELECTORS["complemento"]).get_attribute("value").strip()
            bairro = driver.find_element(By.XPATH, SINGLE_IMOVEL_SELECTORS["bairro"]).get_attribute("value").strip()
            situacao = driver.find_element(By.XPATH, SINGLE_IMOVEL_SELECTORS["situacao"]).get_attribute("value").strip()

            aba_links.append([
                cnpj_cpf, codigo_imovel, inscricao_imobiliaria, logradouro,
                complemento, bairro, situacao, driver.current_url, "Em progresso",
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ])
            print(f"✅ Imóvel único extraído com sucesso: {codigo_imovel}")

        except NoSuchElementException:
            print("❌ Nenhum dado encontrado para imóvel único.")
            raise
