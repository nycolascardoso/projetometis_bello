import easyocr
import base64
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

print("🔵 Iniciando o script...")

def iniciar_driver():
    print("🟡 Inicializando o Selenium...")
    try:
        driver = webdriver.Edge()  # Se for Chrome, troque para webdriver.Chrome()
        print("🟢 Navegador aberto com sucesso!")
        return driver
    except Exception as e:
        print(f"🔴 Erro ao iniciar o WebDriver: {e}")
        return None

def resolver_captcha(driver):
    try:
        print("🟡 Buscando a imagem Base64 do CAPTCHA no HTML...")

        # Aguardar até que a imagem do CAPTCHA esteja visível
        captcha_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="form_index_proprietario"]/table[1]/tbody/tr[3]/td[1]/div/img'))
        )

        # Extrair o atributo "src", que contém a imagem Base64
        captcha_base64 = captcha_element.get_attribute("src").split(",")[1]

        print("🟡 Convertendo imagem Base64 para arquivo PNG...")
        captcha_path = "captcha_temp.png"

        # Converter Base64 para uma imagem e salvar como arquivo
        with open(captcha_path, "wb") as f:
            f.write(base64.b64decode(captcha_base64))

        print("🟡 Inicializando o EasyOCR...")
        reader = easyocr.Reader(["en"])

        print("🟡 Aplicando OCR na imagem...")
        result = reader.readtext(captcha_path, detail=0)

        captcha_text = result[0] if result else ""
        print(f"🟢 Texto extraído do CAPTCHA: {captcha_text}")

        return captcha_text.strip()
    
    except Exception as e:
        print(f"🔴 Erro ao resolver CAPTCHA: {e}")
        return ""

def realizar_login(driver, cnpj_cpf):
    try:
        print("🟡 Acessando a página de login...")
        driver.get("https://nfse1.publica.inf.br/cacador_eiptu/")
        time.sleep(2)

        print("🟡 Buscando campo de CNPJ/CPF...")
        input_campo = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="inscri"]'))
        )
        input_campo.clear()
        input_campo.send_keys(cnpj_cpf)
        print(f"🟢 CPF/CNPJ preenchido: {cnpj_cpf}")

        print("🟡 Resolvendo o CAPTCHA...")
        captcha_text = resolver_captcha(driver)

        if not captcha_text:
            print("🔴 Falha ao reconhecer o CAPTCHA.")
            return False

        print("🟡 Aguardando campo de CAPTCHA aparecer...")
        campo_captcha = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="cod"]'))
        )

        print("🟡 Preenchendo o CAPTCHA no formulário...")
        campo_captcha.clear()
        campo_captcha.send_keys(captcha_text)
        print(f"🟢 CAPTCHA preenchido: {captcha_text}")

        print("🟡 Aguardando 3 segundos antes de prosseguir...")
        time.sleep(3)  # Tempo extra para o usuário visualizar o preenchimento

        print("🟡 Clicando no botão de login...")
        botao_login = driver.find_element(By.XPATH, '//*[@id="form_index_proprietario"]/table[2]/tbody/tr/td/input[1]')
        botao_login.click()

        print("🟡 Aguardando resposta do login...")
        time.sleep(3)

        if "erro" in driver.page_source.lower():
            print("🔴 Erro ao logar: CAPTCHA pode estar incorreto.")
            return False
        else:
            print("🟢 Login realizado com sucesso!")
            return True

    except Exception as e:
        print(f"🔴 Erro no login: {e}")
        return False

# ========================== EXECUÇÃO ==========================
print("🟡 Iniciando fluxo principal...")

driver = iniciar_driver()
if driver:
    sucesso = realizar_login(driver, "005.056.569-90")  # Insira o CNPJ/CPF de teste
    driver.quit()
    print("🟢 Processo finalizado.")
else:
    print("🔴 O WebDriver não foi iniciado corretamente. Verifique o erro acima.")
