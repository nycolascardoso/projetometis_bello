from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
import time

driver = None  # Inicialize o driver como None para evitar NameError no finally

try:
    # Configurar o caminho do EdgeDriver
    service = Service(executable_path="C:/Users/ngcar/edgedriver_win64/msedgedriver.exe")

    # Configurar opções do Edge
    options = Options()
    options.add_argument("start-maximized")  # Abrir o navegador em tela cheia

    # Inicializar o driver
    driver = webdriver.Edge(service=service, options=options)

    # Testar o acesso a um site válido
    driver.get("https://www.example.com")
    print("Título da página:", driver.title)

    # Manter o navegador aberto por 15 segundos para observação
    time.sleep(15)

except Exception as e:
    print("Erro detectado:", e)

finally:
    # Verificar se o driver foi inicializado antes de tentar fechar
    if driver is not None:
        driver.quit()
