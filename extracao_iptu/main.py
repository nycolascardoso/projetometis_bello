from pathlib import Path
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

if __name__ == '__main__' and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from extracao_iptu.selenium_tasks import (
    iniciar_driver, realizar_login, acessar_carne_iptu,
    extrair_tabela_iptu, capturar_inscricao_imobiliaria,
    capturar_dados_adicionais, CaptchaCache
)
from extracao_iptu.utils import (
    carregar_planilha, salvar_planilha, salvar_dados_na_aba,
    atualizar_status_iptu, atualizar_dados_imovel
)
from extracao_iptu.config import SETTINGS, PLANILHA_PATH, SELECTORS, EXECUTION

# Lock global para operações na planilha (compartilhada entre workers)
_planilha_lock = threading.Lock()

# Palavras-chave que identificam erro de conectividade de rede
_ERROS_CONEXAO = [
    "err_connection_timed_out",
    "err_name_not_resolved",
    "err_internet_disconnected",
    "err_connection_refused",
    "err_network_changed",
    "err_empty_response",
    "err_connection_reset",
    "net::err_",
]


def classificar_erro(e):
    """Retorna o status adequado com base no tipo de exceção."""
    msg = str(e).lower()
    if any(padrao in msg for padrao in _ERROS_CONEXAO):
        return "Erro de Conexão"
    return "Erro de Processamento"


def processar_imovel(codigo_imovel, driver, captcha_cache, aba_link_imoveis, aba_banco_dados, planilha):
    """Processa um único imóvel: login → extração → gravação."""
    sucesso = False
    inscricao_imobiliaria = "N/A"
    dados_adicionais = None

    # ── Tentativas de login e extração ──────────────────────────
    for tentativa in range(1, SETTINGS["max_tentativas_login"] + 1):
        try:
            if not realizar_login(driver, codigo_imovel, captcha_cache):
                continue

            inscricao_imobiliaria = capturar_inscricao_imobiliaria(driver) or "N/A"

            ocupacao_elem = driver.find_element("xpath", SELECTORS["ocupacao"])
            ocupacao = ocupacao_elem.get_attribute("value").strip().lower()

            if "baldio" in ocupacao:
                dados_adicionais = {k: "Baldio s/uso" for k in
                                    ["localizacao", "tipologia", "estrutura", "utilizacao", "proprietario"]}
            else:
                dados_adicionais = capturar_dados_adicionais(driver)

            acessar_carne_iptu(driver)
            sucesso = True
            break

        except Exception as e:
            status_erro = classificar_erro(e)
            print(f"⚠️  [{codigo_imovel}] Erro tentativa {tentativa} ({status_erro}): {e}")
            if tentativa == SETTINGS["max_tentativas_login"]:
                with _planilha_lock:
                    atualizar_status_iptu(aba_link_imoveis, codigo_imovel, status_erro, planilha)

    if not sucesso:
        return

    # ── Extração e gravação ──────────────────────────────────────
    try:
        dados_iptu = extrair_tabela_iptu(driver)

        with _planilha_lock:
            atualizar_dados_imovel(
                aba_link_imoveis, codigo_imovel,
                dados_adicionais["localizacao"], dados_adicionais["tipologia"],
                dados_adicionais["estrutura"], dados_adicionais["utilizacao"],
                dados_adicionais["proprietario"], planilha
            )

        if not dados_iptu:
            print(f"⚠️  [{codigo_imovel}] Sem carnê IPTU — registrando.")
            with _planilha_lock:
                salvar_dados_na_aba(
                    aba_banco_dados,
                    [[inscricao_imobiliaria, "2025", "Sem Carnê IPTU", "", "", "",
                      "", "", "", "", "", "", codigo_imovel]],
                    planilha
                )
                atualizar_status_iptu(aba_link_imoveis, codigo_imovel, "Sem Lançamento IPTU", planilha)
            return

        dados_para_salvar = []
        for linha_dados in dados_iptu:
            descricao = linha_dados[1] if len(linha_dados) > 1 else ""
            if "Cota Única 20%" in descricao:
                tipo = "Cota Única 20%"
            elif "Cota Única 10%" in descricao:
                tipo = "Cota Única 10%"
            else:
                tipo = "Parcelado"
            dados_para_salvar.append([inscricao_imobiliaria] + linha_dados + [tipo, codigo_imovel])

        with _planilha_lock:
            salvar_dados_na_aba(aba_banco_dados, dados_para_salvar, planilha)
            atualizar_status_iptu(aba_link_imoveis, codigo_imovel, "Sim", planilha)

        print(f"🟢 [{codigo_imovel}] Dados salvos com sucesso!")

    except Exception as e:
        status_erro = classificar_erro(e)
        print(f"❌ [{codigo_imovel}] Erro ao processar ({status_erro}): {e}")
        with _planilha_lock:
            atualizar_status_iptu(aba_link_imoveis, codigo_imovel, status_erro, planilha)


def worker(worker_id, imoveis_chunk, planilha, aba_link_imoveis, aba_banco_dados):
    """Worker independente: abre seu próprio browser e processa seu chunk."""
    print(f"🚀 Worker {worker_id} iniciado — {len(imoveis_chunk)} imóveis.")
    driver = iniciar_driver(headless=EXECUTION["headless"])
    captcha_cache = CaptchaCache()
    try:
        for codigo_imovel in imoveis_chunk:
            processar_imovel(
                codigo_imovel, driver, captcha_cache,
                aba_link_imoveis, aba_banco_dados, planilha
            )
    finally:
        driver.quit()
        print(f"🛑 Worker {worker_id} encerrado.")


def main():
    # ── Carrega planilha ─────────────────────────────────────────
    try:
        planilha = carregar_planilha()
        aba_link_imoveis = planilha['Link de Imóveis']
        aba_banco_dados = planilha['Banco de Dados']
        print("📂 Planilha carregada com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao carregar a planilha: {e}")
        return

    # ── Coleta imóveis marcados para extração ────────────────────
    imoveis = [
        row[1] for row in aba_link_imoveis.iter_rows(min_row=2, values_only=True)
        if len(row) >= 11 and str(row[10]).strip().lower() == "sim"
    ]
    print(f"🔍 {len(imoveis)} imóveis selecionados para extração.")

    if not imoveis:
        print("⚠️ Nenhum imóvel marcado como 'Sim' na coluna K de 'Link de Imóveis'.")
        return

    # ── Divide e executa em paralelo ─────────────────────────────
    n = EXECUTION["n_workers"]
    chunks = [imoveis[i::n] for i in range(n)]
    print(f"⚡ Iniciando {n} workers em paralelo...")

    with ThreadPoolExecutor(max_workers=n) as executor:
        futures = [
            executor.submit(worker, i + 1, chunks[i], planilha, aba_link_imoveis, aba_banco_dados)
            for i in range(n)
        ]
        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"❌ Worker encerrou com exceção: {e}")

    try:
        salvar_planilha(planilha)
        print("💾 Planilha salva com sucesso!")
    except Exception as e:
        print(f"⚠️ Erro ao salvar a planilha: {e}")

    print("✅ Extração concluída.")


if __name__ == "__main__":
    main()
