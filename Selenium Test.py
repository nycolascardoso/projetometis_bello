from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
import time

# Configuração do EdgeDriver
service = Service(executable_path="C:/Users/ngcar/edgedriver_win64/msedgedriver.exe")
options = Options()
options.add_argument("start-maximized")  # Abrir navegador em tela cheia

driver = webdriver.Edge(service=service, options=options)

# Acessar o site
driver.get("https://nfse1.publica.inf.br/cacador_eiptu/")
time.sleep(2)  # Espera para o site carregar

# Selecionar "CNPJ proprietário"
seletor = driver.find_element(By.ID, "cbLogin")
seletor.send_keys("CNPJ proprietário")  # Simula a escolha da opção

# Inserir o código no campo ao lado
campo = driver.find_element(By.XPATH, '//*[@id="inscri"]')
driver.execute_script("arguments[0].value = arguments[1];", campo, "08958952000124")

# Clicar no botão "Login"
botao_login = driver.find_element(By.XPATH, '//*[@id="form_index_proprietario"]/table[2]/tbody/tr/td/input[1]')
botao_login.click()

# Esperar a página carregar
time.sleep(3)

# Navegar diretamente para o link
driver.get("https://nfse1.publica.inf.br/cacador_eiptu/jsp/debito/gerenciamento/index.jsp#")

time.sleep(5)

# Fecha o navegador
#driver.quit()

