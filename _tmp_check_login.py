from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options
url='https://tmi-apps.e-publica.net/cacador_eiptu/'
opts=Options(); opts.add_argument('start-maximized')
d=webdriver.Edge(options=opts)
try:
    d.get(url)
    WebDriverWait(d, 20).until(lambda x: x.execute_script('return document.readyState')=='complete')
    print('Title:', d.title)
    sel = WebDriverWait(d, 10).until(EC.presence_of_element_located((By.ID,'cbLogin')))
    print('Found select cbLogin. Options:', [o.text for o in sel.find_elements(By.TAG_NAME,'option')][:5])
    campo = d.find_element(By.XPATH, '//*[@id="inscri"]')
    print('Found input inscri.')
    print('OK login form present')
except Exception as e:
    print('Check failed:', e)
finally:
    d.quit()
