from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import DRIVER_PATH, SELECTORS, URL_LOGIN
from datetime import datetime
import time


def iniciar_driver():
    """Inicia o driver do Selenium."""
    from selenium.webdriver.edge.service import Service
    from selenium.webdriver.edge.options import Options

    service = Service(executable_path=DRIVER_PATH)
    options = Options()
    options.add_argument("start-maximized")
    return webdriver.Edge(service=service, options=options)

def realizar_login(driver, cnpj_cpf, tipo_doc):
    """Realiza o login na tela inicial e verifica se foi bem-sucedido."""
    try:
        print(f"Tentando login com {cnpj_cpf} ({tipo_doc})")
        driver.get(URL_LOGIN)
        time.sleep(2)

        # Selecionar o tipo de documento
        seletor = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, SELECTORS["login_selector"]))
        )
        seletor.send_keys(tipo_doc)

        # Inserir o CNPJ/CPF
        campo = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, SELECTORS["input_campo"]))
        )
        driver.execute_script("arguments[0].value = arguments[1];", campo, cnpj_cpf)

        # Clicar no botão de login
        botao_login = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, SELECTORS["botao_login"]))
        )
        botao_login.click()
     
        # Verificar se há mensagem de erro de login
        try:
            mensagem_erro = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, SELECTORS["mensagem_erro"]))
            )
            print(f"Erro de login detectado: {mensagem_erro.text.strip()}")
            raise Exception(mensagem_erro.text.strip())
        except Exception:
            print("Nenhuma mensagem de erro encontrada, continuando...")

        # Verificar presença de elemento da tela 2 (como tabela de imóveis)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, SELECTORS["tabela_imoveis"]))
            )
            print("Login realizado com sucesso! Tela 2 detectada.")
        except Exception:
            raise Exception("Elemento da tela 2 não encontrado. O login pode ter falhado.")

    except Exception as e:
        print(f"Erro ao realizar login: {e}")
        raise

def extrair_tabela_imoveis(driver, cnpj_cpf, aba_links, planilha, planilha_path):
    """Extrai dados da tabela de imóveis e os salva na aba 'Link de Imóveis'."""
    try:
        # Localizar a tabela
        tabela = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, SELECTORS["tabela_imoveis"]))
        )
        print("Tabela de imóveis localizada com sucesso.")

        linhas = tabela.find_elements(By.XPATH, SELECTORS["tabela_linhas"])

        # Extrair dados de cada linha
        for linha in linhas:
            try:
                # Extrair dados das colunas usando SELECTORS
                url_imovel = linha.find_element(By.XPATH, SELECTORS["tabela_celula_link"]).get_attribute('href')
                codigo_imovel = linha.find_element(By.XPATH, SELECTORS["tabela_celula_codigo"]).text.strip()
                inscricao_imobiliaria = linha.find_element(By.XPATH, SELECTORS["tabela_celula_inscricao"]).text.strip()
                logradouro = linha.find_element(By.XPATH, SELECTORS["tabela_celula_logradouro"]).text.strip()
                complemento = linha.find_element(By.XPATH, SELECTORS["tabela_celula_complemento"]).text.strip()
                bairro = linha.find_element(By.XPATH, SELECTORS["tabela_celula_bairro"]).text.strip()
                situacao = linha.find_element(By.XPATH, SELECTORS["tabela_celula_situacao"]).text.strip()

                # Adicionar dados na aba "Link de Imóveis"
                aba_links.append([
                    cnpj_cpf,  # CNPJ/CPF
                    codigo_imovel,  # Código do Imóvel
                    inscricao_imobiliaria,  # Inscrição Imobiliária
                    logradouro,  # Logradouro
                    complemento,  # Complemento
                    bairro,  # Bairro
                    situacao,  # Situação
                    url_imovel,  # URL do Imóvel
                    "Em progresso",  # Status
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Última Atualização
                ])
                print(f"Imóvel {codigo_imovel} extraído com sucesso.")

            except Exception as e:
                print(f"Erro ao extrair dados da linha: {e}")

        # Salvar alterações na planilha
        planilha.save(planilha_path)
        print(f"Dados da tabela de imóveis salvos para o CNPJ/CPF {cnpj_cpf}.")

    except Exception as e:
        print(f"Erro ao localizar tabela de imóveis: {e}")
        raise


