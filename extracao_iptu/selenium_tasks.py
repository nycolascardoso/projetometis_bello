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
from extracao_iptu.config import DRIVER_PATH, SELECTORS, URL_LOGIN, SINGLE_IMOVEL_SELECTORS, PLANILHA_PATH, TABLE_SELECTORS

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
# Extrai os dados da tabela de IPTU
def extrair_tabela_iptu(driver):
    """Extrai a tabela de IPTU, removendo o cabeçalho e a última linha sem excluir dados importantes."""
    try:
        print("📋 Extraindo tabela de IPTU...")

        # Aguarda o carregamento da tabela
        tabela = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, TABLE_SELECTORS["tabela_iptu"]))
        )

        # Captura todas as linhas da tabela
        linhas = tabela.find_elements(By.XPATH, TABLE_SELECTORS["linhas_tabela_iptu"])

        if not linhas or len(linhas) < 2:
            print("⚠️ Nenhuma informação de carnê IPTU disponível para este imóvel.")
            return None  # Retorna None para indicar que não há carnê

        print(f"🟢 {len(linhas)} linhas encontradas na tabela de IPTU.")

        # Remove a primeira linha se for um cabeçalho
        primeira_linha = linhas[0].find_elements(By.XPATH, TABLE_SELECTORS["colunas_tabela_iptu"])
        if primeira_linha and all(coluna.text.strip().isalpha() for coluna in primeira_linha):
            print("🗑️ Cabeçalho detectado e removido.")
            linhas = linhas[1:]

        # Remove a última linha se for um resumo
        ultima_linha = linhas[-1].find_elements(By.XPATH, TABLE_SELECTORS["colunas_tabela_iptu"])
        if ultima_linha and any("Total" in coluna.text for coluna in ultima_linha):
            print("🗑️ Linha de resumo detectada e removida.")
            linhas = linhas[:-1]

        # Se após remoções não restar nenhuma linha, retorna como vazio
        if not linhas:
            print("⚠️ Nenhuma linha válida restante após limpeza da tabela.")
            return None

        dados = []
        tipo_pagamento = None  # Variável para identificar o tipo de pagamento

        for linha in linhas:
            colunas = linha.find_elements(By.XPATH, TABLE_SELECTORS["colunas_tabela_iptu"])
            valores = [coluna.text.strip() for coluna in colunas]

            if valores:
                descricao = valores[1]  # Presumindo que a segunda coluna contém a descrição da parcela

                # Determina o tipo de pagamento com base na descrição
                if "Cota Única 20%" in descricao:
                    tipo_pagamento = "Cota Única 20%"
                elif "Cota Única 10%" in descricao:
                    tipo_pagamento = "Cota Única 10%"
                elif "Parcela" in descricao:
                    tipo_pagamento = "Parcelamento Completo"

                valores.append(tipo_pagamento)  # Adiciona a categoria da parcela na última coluna
                dados.append(valores)

        print(f"✅ {len(dados)} linhas processadas após limpeza e categorização.")
        return dados

    except TimeoutException:
        print("⚠️ Nenhuma tabela de IPTU encontrada. Provavelmente o imóvel não tem carnê disponível.")
        return None  # Retorna None para indicar que não há carnê IPTU para este imóvel

    except Exception as e:
        print(f"❌ Erro ao extrair tabela IPTU: {e}")
        return None  # Retorna None para garantir que o erro não impeça a execução do restante do código


def capturar_inscricao_imobiliaria(driver):
    """Extrai a Inscrição Imobiliária na página pós-login."""
    try:
        print("🔍 Extraindo Inscrição Imobiliária...")
        
        inscricao_elemento = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, SELECTORS["inscricao_imobiliaria"]))
        )
        inscricao_imobiliaria = inscricao_elemento.get_attribute("value").strip()

        print(f"✅ Inscrição Imobiliária extraída: {inscricao_imobiliaria}")
        return inscricao_imobiliaria

    except Exception as e:
        print(f"❌ Erro ao capturar Inscrição Imobiliária: {e}")
        return None

def capturar_dados_adicionais(driver):
    """Captura Localização, Tipologia, Estrutura, Utilização e Proprietário na página pós-login."""
    try:
        print("🔍 Extraindo dados adicionais do imóvel...")

        dados = {}

        # Captura os campos de interesse
        for key, xpath in {
            "localizacao": '//*[@id="agrupador-area"]/div[2]/div[10]/div/div/table/tbody/tr[3]/td[6]/input',
            "tipologia": '//*[@id="agrupador-area"]/div[2]/div[10]/div/div/table/tbody/tr[2]/td[4]/input',
            "estrutura": '//*[@id="agrupador-area"]/div[2]/div[10]/div/div/table/tbody/tr[4]/td[2]/input',
            "utilizacao": '//*[@id="agrupador-area"]/div[2]/div[10]/div/div/table/tbody/tr[5]/td[4]/input',
            "proprietario": '//*[@id="agrupador-area"]/div[2]/div[2]/div/div/table/tbody/tr[1]/td[2]/input'
        }.items():
            try:
                elemento = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                dados[key] = elemento.get_attribute("value").strip() if elemento.get_attribute("value") else "N/A"
            except Exception:
                print(f"⚠️ Não foi possível capturar {key}.")
                dados[key] = "N/A"

        print(f"✅ Dados capturados: {dados}")
        return dados

    except Exception as e:
        print(f"❌ Erro ao capturar dados adicionais: {e}")
        return None
