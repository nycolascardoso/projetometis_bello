from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
import time
import csv

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
driver.execute_script("arguments[0].value = arguments[1];", campo, "50.136.653/0001-70")

# Clicar no botão "Login"
botao_login = driver.find_element(By.XPATH, '//*[@id="form_index_proprietario"]/table[2]/tbody/tr/td/input[1]')
botao_login.click()

# Esperar a página carregar
time.sleep(3)

# Navegar diretamente para o link
driver.get("https://nfse1.publica.inf.br/cacador_eiptu/jsp/debito/gerenciamento/index.jsp#")

time.sleep(1)

# Localizar o formulário pela ação
form_element = driver.find_element(By.XPATH, '//*[@id="frm_lista_debitos"]')

# Dentro do formulário, localizar a tabela pela classe ou pelo XPath completo
table = form_element.find_element(By.XPATH, './/table')

# Capturar todas as linhas do corpo da tabela
rows = table.find_elements(By.XPATH, './/tbody/tr')

# Criar uma lista para armazenar os dados
data = []

# Iterar pelas linhas da tabela e capturar os dados
for row in rows:
    cells = row.find_elements(By.TAG_NAME, 'td')
    # Extrair o texto de cada célula
    row_data = [cell.text.strip() for cell in cells]
    data.append(row_data)

# Definir o cabeçalho da tabela (pode ser personalizado ou extraído do <thead>)
header = [
    "Ano", "Descrição", "Nº parc.", "Sub. parc.", "Tipo Débito", "Dt. vcto.",
    "Vlr. parcela", "Desconto", "Vlr. juros", "Vlr. multa", "Vlr. correção",
    "Vlr. honorário", "Vlr. corrigido", "Pagamento", "Ações"
]

# Escrever os dados em um arquivo CSV
with open('tabela_iptu.csv', 'w', newline='', encoding='utf-8-sig') as file:
    writer = csv.writer(file, delimiter=';')  # Separador de campo
    writer.writerow(header)  # Escrever o cabeçalho
    writer.writerows(data)   # Escrever os dados da tabela

print("Dados exportados para 'tabela_iptu.csv' com sucesso.")


# Fecha o navegador
#driver.quit()

