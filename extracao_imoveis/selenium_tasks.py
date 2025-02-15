from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from extracao_imoveis.config import DRIVER_PATH, SELECTORS, URL_LOGIN, SINGLE_IMOVEL_SELECTORS
from datetime import datetime
import time
from selenium.common.exceptions import TimeoutException

def iniciar_driver():
    """Inicia o driver do Selenium."""
    from selenium.webdriver.edge.service import Service
    from selenium.webdriver.edge.options import Options

    service = Service(executable_path=DRIVER_PATH)
    options = Options()
    options.add_argument("start-maximized")
    return webdriver.Edge(service=service, options=options)

def resolver_captcha(driver):
    """Resolve o CAPTCHA usando OCR."""
    try:
        print("🟡 Resolvendo CAPTCHA...")
        captcha_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, SELECTORS["captcha_image"]))
        )
        captcha_base64 = captcha_element.get_attribute("src").split(",")[-1]
        captcha_image = Image.open(BytesIO(base64.b64decode(captcha_base64)))
        reader = easyocr.Reader(['en'])
        result = reader.readtext(captcha_image, detail=0)
        captcha_text = result[0] if result else ""
        print(f"🟢 CAPTCHA resolvido: {captcha_text}")
        return captcha_text
    except Exception as e:
        print(f"🔴 Erro ao resolver CAPTCHA: {e}")
        return ""



def realizar_login(driver, cnpj_cpf, tipo_doc):
    """Realiza o login na tela inicial e verifica se foi bem-sucedido, resolvendo o CAPTCHA."""
    try:
        print(f"Tentando login com {cnpj_cpf} ({tipo_doc})")
        driver.get(URL_LOGIN)
        time.sleep(2)

        # Seleciona o tipo de documento
        seletor = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, SELECTORS["login_selector"]))
        )
        seletor.send_keys(tipo_doc)

        # Insere o CNPJ/CPF
        campo = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, SELECTORS["input_campo"]))
        )
        driver.execute_script("arguments[0].value = arguments[1];", campo, cnpj_cpf)

        # Resolver CAPTCHA
        captcha_text = resolver_captcha(driver)
        if not captcha_text:
            raise Exception("Falha ao resolver CAPTCHA")

        # Insere o CAPTCHA resolvido
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
        # (a) Mensagem de erro, (b) Tabela de imóveis ou (c) Indicador de imóvel único.
        WebDriverWait(driver, 10).until(
            lambda d: d.find_elements(By.XPATH, SELECTORS["mensagem_erro"]) or
                      d.find_elements(By.XPATH, SELECTORS["tabela_imoveis"]) or
                      d.find_elements(By.XPATH, SINGLE_IMOVEL_SELECTORS["codigo_imovel"])
        )

        # Verifica se há mensagem de erro (supondo que o elemento exista e esteja com texto significativo)
        erro_elems = driver.find_elements(By.XPATH, SELECTORS["mensagem_erro"])
        if erro_elems:
            erro_text = erro_elems[0].text.strip()
            if erro_text:
                print(f"Erro de login: {erro_text}")
                raise Exception(f"Erro de login: {erro_text}")

        # Se não houve erro, verifica se foi carregada a tabela ou a página de imóvel único
        if driver.find_elements(By.XPATH, SELECTORS["tabela_imoveis"]):
            print("🟢 Login realizado com sucesso! Tela 2 (tabela) detectada.")
        elif driver.find_elements(By.XPATH, SINGLE_IMOVEL_SELECTORS["codigo_imovel"]):
            print("🟢 Login realizado com sucesso! Imóvel único detectado.")
        else:
            raise Exception("Erro: Nenhum elemento de sucesso encontrado. Possível problema de conexão ou login.")

    except Exception as e:
        print(f"🔴 Erro ao realizar login: {e}")
        raise

def extrair_tabela_imoveis(driver, cnpj_cpf, aba_links, planilha, planilha_path):
    """
    Extrai dados da tabela de imóveis ou, se essa extração falhar, utiliza a lógica para um único imóvel.
    
    Os dados extraídos seguem a estrutura:
      [CNPJ/CPF, Código do Imóvel, Inscrição Imobiliária, Logradouro, Complemento,
       Bairro, Situação, URL do Imóvel, Status, Última Atualização]
       
    Essa função presume que o login já foi efetuado.
    """
    from selenium.common.exceptions import TimeoutException
    try:
        # Tenta extrair os dados da tabela de imóveis (cenário de múltiplos imóveis)
        tabela = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, SELECTORS["tabela_imoveis"]))
        )
        print("Tabela de imóveis localizada com sucesso.")
        linhas = tabela.find_elements(By.XPATH, SELECTORS["tabela_linhas"])
        if not linhas or len(linhas) == 0:
            raise Exception("Tabela encontrada, mas sem linhas.")
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
                    cnpj_cpf,               # CNPJ/CPF
                    codigo_imovel,          # Código do Imóvel
                    inscricao_imobiliaria,  # Inscrição Imobiliária
                    logradouro,             # Logradouro
                    complemento,            # Complemento
                    bairro,                 # Bairro
                    situacao,               # Situação
                    url_imovel,             # URL do Imóvel
                    "Em progresso",         # Status
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Última Atualização
                ])
                print(f"Imóvel {codigo_imovel} extraído com sucesso.")
            except Exception as e:
                print(f"Erro ao extrair dados de uma linha da tabela: {e}")
        planilha.save(planilha_path)
        print(f"Dados da tabela de imóveis salvos para o CNPJ/CPF {cnpj_cpf}.")
        
    except Exception as erro_tabela:
        # Se houver erro na extração via tabela, tenta a lógica de imóvel único
        print(f"Erro na extração via tabela: {erro_tabela}")
        print("Tentando a extração como imóvel único...")
        try:
            # Extração para imóvel único - usando get_attribute("value") para cada campo
            elemento_codigo = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, SINGLE_IMOVEL_SELECTORS["codigo_imovel"]))
            )
            codigo_imovel = elemento_codigo.get_attribute("value").strip()

            elemento_inscricao = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, SINGLE_IMOVEL_SELECTORS["inscricao_imobiliaria"]))
            )
            inscricao_imobiliaria = elemento_inscricao.get_attribute("value").strip()

            elemento_logradouro = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, SINGLE_IMOVEL_SELECTORS["logradouro"]))
            )
            logradouro = elemento_logradouro.get_attribute("value").strip()

            elemento_complemento = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, SINGLE_IMOVEL_SELECTORS["complemento"]))
            )
            complemento = elemento_complemento.get_attribute("value").strip()

            elemento_bairro = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, SINGLE_IMOVEL_SELECTORS["bairro"]))
            )
            bairro = elemento_bairro.get_attribute("value").strip()

            elemento_situacao = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, SINGLE_IMOVEL_SELECTORS["situacao"]))
            )
            situacao = elemento_situacao.get_attribute("value").strip()

            url_imovel = driver.current_url

            print("Imóvel único detectado - extraindo dados da tela.")
            aba_links.append([
                cnpj_cpf,
                codigo_imovel,
                inscricao_imobiliaria,
                logradouro,
                complemento,
                bairro,
                situacao,
                url_imovel,
                "Em progresso",
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ])
            planilha.save(planilha_path)
            print(f"Dados do imóvel único salvos para o CNPJ/CPF {cnpj_cpf}.")
        except Exception as erro_unico:
            print(f"Erro na extração do imóvel único: {erro_unico}")
            raise erro_unico
