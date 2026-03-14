import threading
import base64
import os
import tempfile
import numpy as np
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from extracao_iptu.config import (
    DRIVER_PATH, SELECTORS, SETTINGS, SINGLE_IMOVEL_SELECTORS, TABLE_SELECTORS, URL_CARNE_IPTU, URL_LOGIN
)


# ──────────────────────────────────────────────
# Cache de CAPTCHA
# ──────────────────────────────────────────────

class CaptchaCache:
    """
    Reutiliza o CAPTCHA após 2 logins bem-sucedidos consecutivos.
    A partir do 3º login, o site mantém o mesmo CAPTCHA — resolvemos
    uma única vez e reaproveitamos para todos os imóveis seguintes.
    """
    def __init__(self):
        self.text = None
        self._count = 0

    def update(self, text):
        self.text = text
        self._count += 1

    def invalidate(self):
        self.text = None
        self._count = 0

    @property
    def reusable(self):
        return self._count >= 2 and self.text is not None


# ──────────────────────────────────────────────
# WebDriver
# ──────────────────────────────────────────────

def iniciar_driver(headless=False):
    """Inicia o driver do Selenium (Selenium Manager com fallback)."""
    from selenium.webdriver.edge.options import Options
    options = Options()
    if headless:
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
    else:
        options.add_argument('start-maximized')
    try:
        return webdriver.Edge(options=options)
    except Exception:
        from selenium.webdriver.edge.service import Service
        service = Service(executable_path=DRIVER_PATH)
        return webdriver.Edge(service=service, options=options)


# ──────────────────────────────────────────────
# CAPTCHA
# ──────────────────────────────────────────────

_EASYOCR_READER = None
_EASYOCR_LOCK = threading.Lock()


def resolver_captcha(driver):
    """Resolve o CAPTCHA via OCR e retorna o texto."""
    global _EASYOCR_READER
    try:
        print("🟡 Capturando CAPTCHA...")
        captcha_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, SELECTORS["captcha_image"]))
        )

        captcha_base64 = captcha_element.get_attribute("src").split(",")[-1]
        captcha_bytes = base64.b64decode(captcha_base64)
        captcha_image = Image.open(BytesIO(captcha_bytes))

        captcha_temp = os.path.join(tempfile.gettempdir(), f'metis_captcha_{threading.get_ident()}.png')
        captcha_image.save(captcha_temp)

        captcha_array = np.array(Image.open(captcha_temp).convert("L"))

        with _EASYOCR_LOCK:
            if _EASYOCR_READER is None:
                import easyocr
                _EASYOCR_READER = easyocr.Reader(["en"])
            reader = _EASYOCR_READER

        result = reader.readtext(captcha_array, detail=0)
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


# ──────────────────────────────────────────────
# Login
# ──────────────────────────────────────────────

def _preencher_formulario(driver, codigo_imovel):
    """Navega para a tela de login e preenche tipo + código do imóvel (sem CAPTCHA)."""
    driver.get(URL_LOGIN)
    WebDriverWait(driver, SETTINGS["timeout_padrao"]).until(
        EC.presence_of_element_located((By.ID, SELECTORS["login_selector"]))
    ).send_keys("Cód. do imóvel")
    WebDriverWait(driver, SETTINGS["timeout_padrao"]).until(
        EC.presence_of_element_located((By.XPATH, SELECTORS["input_campo"]))
    ).send_keys(codigo_imovel)


def _submeter_e_verificar(driver):
    """
    Preenche o campo de CAPTCHA já capturado, clica em login e verifica resultado.
    Retorna (ok: bool, erro_text: str | None).
    """
    WebDriverWait(driver, SETTINGS["timeout_padrao"]).until(
        EC.element_to_be_clickable((By.XPATH, SELECTORS["botao_login"]))
    ).click()
    WebDriverWait(driver, SETTINGS["timeout_padrao"]).until(
        lambda d: d.find_elements(By.XPATH, SELECTORS["mensagem_erro"]) or
                  d.find_elements(By.XPATH, SINGLE_IMOVEL_SELECTORS["codigo_imovel"])
    )
    erro_elems = driver.find_elements(By.XPATH, SELECTORS["mensagem_erro"])
    if erro_elems and erro_elems[0].text.strip():
        return False, erro_elems[0].text.strip()
    return True, None


def realizar_login(driver, codigo_imovel, captcha_cache=None):
    """
    Realiza login no sistema com duas estratégias:

    Cache (>= 2 logins bem-sucedidos anteriores):
      - Tenta uma vez com o texto cacheado.
      - Se falhar → invalida o cache → próxima tentativa externa usa OCR.

    OCR (sem cache ou cache invalidado):
      - Loop interno de até max_tentativas_captcha tentativas.
      - Cada tentativa recarrega a página para obter um CAPTCHA novo.
      - Só conta como tentativa externa quando todas as tentativas de OCR esgotam.
    """
    for tentativa in range(1, SETTINGS["max_tentativas_login"] + 1):
        try:
            _preencher_formulario(driver, codigo_imovel)
            usar_cache = captcha_cache is not None and captcha_cache.reusable

            if usar_cache:
                # ── Caminho cache ────────────────────────────────────
                captcha_text = captcha_cache.text
                print(f"♻️  [{codigo_imovel}] Reutilizando CAPTCHA: {captcha_text}")
                WebDriverWait(driver, SETTINGS["timeout_padrao"]).until(
                    EC.presence_of_element_located((By.XPATH, SELECTORS["captcha_input"]))
                ).send_keys(captcha_text)
                ok, erro = _submeter_e_verificar(driver)
                if not ok:
                    print(f"⚠️  [{codigo_imovel}] Cache inválido ({erro}) — invalidando.")
                    captcha_cache.invalidate()
                    raise Exception(f"CAPTCHA cacheado rejeitado: {erro}")

            else:
                # ── Caminho OCR com loop interno ─────────────────────
                ok = False
                for captcha_try in range(1, SETTINGS["max_tentativas_captcha"] + 1):
                    if captcha_try > 1:
                        # Recarrega a página para obter CAPTCHA novo após falha
                        _preencher_formulario(driver, codigo_imovel)

                    captcha_text = resolver_captcha(driver)
                    if not captcha_text:
                        print(f"⚠️  [{codigo_imovel}] OCR retornou vazio "
                              f"(captcha {captcha_try}/{SETTINGS['max_tentativas_captcha']})")
                        continue

                    WebDriverWait(driver, SETTINGS["timeout_padrao"]).until(
                        EC.presence_of_element_located((By.XPATH, SELECTORS["captcha_input"]))
                    ).send_keys(captcha_text)

                    ok, erro = _submeter_e_verificar(driver)
                    if ok:
                        break
                    print(f"⚠️  [{codigo_imovel}] CAPTCHA '{captcha_text}' rejeitado: {erro} "
                          f"(captcha {captcha_try}/{SETTINGS['max_tentativas_captcha']})")

                if not ok:
                    raise Exception(
                        f"CAPTCHA falhou após {SETTINGS['max_tentativas_captcha']} tentativas de OCR"
                    )

            # ── Login bem-sucedido ───────────────────────────────────
            if captcha_cache is not None:
                captcha_cache.update(captcha_text)
            print(f"🟢 [{codigo_imovel}] Login OK (tentativa {tentativa}).")
            return True

        except Exception as e:
            print(f"⚠️  [{codigo_imovel}] Tentativa {tentativa}/{SETTINGS['max_tentativas_login']} falhou: {e}")

    print(f"❌ [{codigo_imovel}] Falha no login após {SETTINGS['max_tentativas_login']} tentativas.")
    return False


# ──────────────────────────────────────────────
# Extração de dados
# ──────────────────────────────────────────────

def capturar_inscricao_imobiliaria(driver):
    """Extrai a Inscrição Imobiliária na página pós-login."""
    try:
        elemento = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, SELECTORS["inscricao_imobiliaria"]))
        )
        valor = elemento.get_attribute("value").strip()
        print(f"✅ Inscrição Imobiliária: {valor}")
        return valor
    except Exception as e:
        print(f"❌ Erro ao capturar Inscrição Imobiliária: {e}")
        return None


def capturar_dados_adicionais(driver):
    """Captura Localização, Tipologia, Estrutura, Utilização e Proprietário."""
    try:
        ocupacao_texto = "N/A"
        try:
            ocupacao_elemento = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, SELECTORS["ocupacao"]))
            )
            ocupacao_texto = ocupacao_elemento.get_attribute("value").strip().lower()
        except TimeoutException:
            pass

        if "baldio" in ocupacao_texto:
            print("🏗️ Imóvel BALDIO — preenchendo automaticamente.")
            return {k: "Baldio s/uso" for k in ["localizacao", "tipologia", "estrutura", "utilizacao", "proprietario"]}

        dados = {}
        for key in ["localizacao", "tipologia", "estrutura", "utilizacao", "proprietario"]:
            try:
                elemento = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, SELECTORS[key]))
                )
                dados[key] = elemento.get_attribute("value").strip() or "N/A"
            except TimeoutException:
                dados[key] = "N/A"

        return dados

    except Exception as e:
        print(f"❌ Erro ao capturar dados adicionais: {e}")
        return None


def acessar_carne_iptu(driver):
    """Acessa a página do Carnê IPTU."""
    try:
        driver.get(URL_CARNE_IPTU)
        WebDriverWait(driver, SETTINGS["timeout_padrao"]).until(
            EC.presence_of_element_located((By.XPATH, TABLE_SELECTORS["elemento_tabela_iptu"]))
        )
        print("🟢 Página do Carnê IPTU carregada.")
    except Exception as e:
        print(f"❌ Erro ao acessar Carnê IPTU: {e}")
        raise


def extrair_tabela_iptu(driver):
    """Extrai e categoriza as parcelas da tabela de IPTU."""
    try:
        tabela = WebDriverWait(driver, SETTINGS["timeout_padrao"]).until(
            EC.presence_of_element_located((By.XPATH, TABLE_SELECTORS["elemento_tabela_iptu"]))
        )
        linhas = tabela.find_elements(By.XPATH, TABLE_SELECTORS["linhas_tabela_iptu"])

        if not linhas or len(linhas) < 2:
            print("⚠️ Nenhum carnê IPTU disponível para este imóvel.")
            return None

        if "Total" in linhas[-1].text:
            linhas.pop()

        dados = []
        for linha in linhas:
            colunas = linha.find_elements(By.XPATH, TABLE_SELECTORS["colunas_tabela_iptu"])
            valores = [col.text.strip() for col in colunas]
            if valores:
                descricao = valores[1] if len(valores) > 1 else ""
                if "Cota Única 20%" in descricao:
                    tipo = "Cota Única 20%"
                elif "Cota Única 10%" in descricao:
                    tipo = "Cota Única 10%"
                else:
                    tipo = "Parcelado"
                valores.append(tipo)
                dados.append(valores)

        print(f"✅ {len(dados)} parcelas extraídas.")
        return dados

    except TimeoutException:
        print("⚠️ Tabela de IPTU não encontrada.")
        return None
    except Exception as e:
        print(f"❌ Erro ao extrair tabela IPTU: {e}")
        return None
