from pathlib import Path
import sys
import ctypes
import threading
import time
from concurrent.futures import ThreadPoolExecutor

# Impede que o Windows suspenda o sistema enquanto o script estiver rodando.
# ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
if sys.platform == 'win32':
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001 | 0x00000002)

if __name__ == '__main__' and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from extracao_iptu.selenium_tasks import (
    iniciar_driver, realizar_login, acessar_carne_iptu,
    extrair_tabela_iptu, capturar_inscricao_imobiliaria,
    capturar_dados_adicionais, CaptchaCache, _pause_gate
)
from extracao_iptu.utils import (
    carregar_planilha, salvar_planilha, salvar_dados_na_aba,
    atualizar_status_iptu, atualizar_dados_imovel
)
from extracao_iptu.config import SETTINGS, PLANILHA_PATH, SELECTORS, EXECUTION

# ──────────────────────────────────────────────────────────────
# Lock global para operações na planilha (compartilhada entre workers)
# ──────────────────────────────────────────────────────────────
_planilha_lock = threading.Lock()

# Padrões que identificam erros de conectividade de rede
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
    """Classifica a exceção como erro de conexão ou de processamento."""
    msg = str(e).lower()
    if any(p in msg for p in _ERROS_CONEXAO):
        return "Erro de Conexão"
    return "Erro de Processamento"


# ──────────────────────────────────────────────────────────────
# Rastreador de progresso
# ──────────────────────────────────────────────────────────────

class ProgressTracker:
    """
    Barra de progresso visual com ETA e contadores por worker.
    Imprime a cada ciclo completo (1 ciclo = n_workers imóveis concluídos).

    Exemplo de saída:
    ──────────────────────────────────────────────────────────────
    [████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 250/3171 (7.9%)
    ✅ 237 OK  ❌ 13 erros  |  ETA: 7h18m  |  ⏱ 0h42m decorrido
    W1: 84/1057  W2: 83/1057  W3: 83/1057
    ──────────────────────────────────────────────────────────────
    """
    _BAR_WIDTH = 40

    def __init__(self, total: int, n_workers: int):
        self._lock = threading.Lock()
        self.total = total
        self.done = 0
        self.ok = 0
        self.erros = 0
        self._inicio = time.time()
        self._n_workers = n_workers
        self._worker_done = {i: 0 for i in range(1, n_workers + 1)}
        self._worker_total: dict[int, int] = {}

    def set_worker_total(self, worker_id: int, total: int):
        with self._lock:
            self._worker_total[worker_id] = total

    def update(self, worker_id: int, sucesso: bool = True):
        with self._lock:
            self.done += 1
            if sucesso:
                self.ok += 1
            else:
                self.erros += 1
            self._worker_done[worker_id] = self._worker_done.get(worker_id, 0) + 1
            # Imprime a cada ciclo completo (n_workers imóveis) ou ao final
            if self.done % self._n_workers == 0 or self.done == self.total:
                self._imprimir()

    def _imprimir(self):
        elapsed = time.time() - self._inicio
        pct = self.done / self.total * 100 if self.total else 0

        # Barra visual
        filled = int(pct / 100 * self._BAR_WIDTH)
        bar = "█" * filled + "░" * (self._BAR_WIDTH - filled)

        # ETA
        if self.done > 0 and self.done < self.total:
            eta_sec = elapsed / self.done * (self.total - self.done)
            h_eta, rem = divmod(int(eta_sec), 3600)
            eta_str = f"{h_eta}h{rem // 60:02d}m"
        elif self.done == self.total:
            eta_str = "concluído"
        else:
            eta_str = "--"

        # Tempo decorrido
        h_el, rem_el = divmod(int(elapsed), 3600)
        elapsed_str = f"{h_el}h{rem_el // 60:02d}m"

        # Workers
        workers_str = "  ".join(
            f"W{wid}:{self._worker_done.get(wid, 0)}/{self._worker_total.get(wid, '?')}"
            for wid in sorted(self._worker_total)
        )

        sep = "─" * 62
        print(f"\n{sep}")
        print(f"[{bar}] {self.done}/{self.total} ({pct:.1f}%)")
        print(f"✅ {self.ok} OK  ❌ {self.erros} erros  |  ETA: {eta_str}  |  ⏱ {elapsed_str} decorrido")
        if workers_str:
            print(f"{workers_str}")
        print(f"{sep}\n")


# ──────────────────────────────────────────────────────────────
# Processamento de um imóvel
# ──────────────────────────────────────────────────────────────

def processar_imovel(codigo_imovel, driver, captcha_cache,
                     aba_link_imoveis, aba_banco_dados, planilha,
                     progress: ProgressTracker = None, worker_id: int = None):
    """Login → captura de dados → extração do carnê → gravação (1 save por imóvel)."""
    sucesso = False
    inscricao_imobiliaria = "N/A"
    dados_adicionais = None

    # ── Tentativas de login ──────────────────────────────────────
    for tentativa in range(1, SETTINGS["max_tentativas_login"] + 1):
        try:
            if not realizar_login(driver, codigo_imovel, captcha_cache, worker_id=worker_id):
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
            print(f"⚠️  [{codigo_imovel}] Erro tentativa {tentativa}/{SETTINGS['max_tentativas_login']} "
                  f"({status_erro}): {e}")
            if tentativa == SETTINGS["max_tentativas_login"]:
                with _planilha_lock:
                    atualizar_status_iptu(aba_link_imoveis, codigo_imovel, status_erro)
                    salvar_planilha(planilha)
                if progress:
                    progress.update(worker_id, sucesso=False)
                return

    if not sucesso:
        if progress:
            progress.update(worker_id, sucesso=False)
        return

    # ── Extração do carnê IPTU ───────────────────────────────────
    try:
        dados_iptu = extrair_tabela_iptu(driver)

        # Prepara dados antes de adquirir o lock
        if dados_iptu:
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

        # ── Gravação em bloco único → 1 save por imóvel ──────────
        with _planilha_lock:
            atualizar_dados_imovel(
                aba_link_imoveis, codigo_imovel,
                dados_adicionais["localizacao"], dados_adicionais["tipologia"],
                dados_adicionais["estrutura"], dados_adicionais["utilizacao"],
                dados_adicionais["proprietario"]
            )
            if not dados_iptu:
                print(f"⚠️  [{codigo_imovel}] Sem carnê IPTU — registrando.")
                salvar_dados_na_aba(
                    aba_banco_dados,
                    [[inscricao_imobiliaria, "2025", "Sem Carnê IPTU", "", "", "",
                      "", "", "", "", "", "", codigo_imovel]]
                )
                atualizar_status_iptu(aba_link_imoveis, codigo_imovel, "Sem Lançamento IPTU")
            else:
                salvar_dados_na_aba(aba_banco_dados, dados_para_salvar)
                atualizar_status_iptu(aba_link_imoveis, codigo_imovel, "Sim")
            salvar_planilha(planilha)  # único save por imóvel

        print(f"🟢 [{codigo_imovel}] Concluído.")
        if progress:
            progress.update(worker_id, sucesso=True)

    except Exception as e:
        status_erro = classificar_erro(e)
        print(f"❌ [{codigo_imovel}] Erro ao processar ({status_erro}): {e}")
        with _planilha_lock:
            atualizar_status_iptu(aba_link_imoveis, codigo_imovel, status_erro)
            salvar_planilha(planilha)
        if progress:
            progress.update(worker_id, sucesso=False)


# ──────────────────────────────────────────────────────────────
# Worker e orquestrador principal
# ──────────────────────────────────────────────────────────────

def worker(worker_id, imoveis_chunk, planilha, aba_link_imoveis, aba_banco_dados,
           progress: ProgressTracker):
    """Worker independente: browser próprio, CaptchaCache próprio, processa seu chunk."""
    total = len(imoveis_chunk)
    progress.set_worker_total(worker_id, total)
    print(f"🚀 Worker {worker_id} iniciado — {total} imóveis.")
    driver = iniciar_driver(headless=EXECUTION["headless"])
    captcha_cache = CaptchaCache()
    try:
        for codigo_imovel in imoveis_chunk:
            _pause_gate.wait()  # aguarda se outro worker está pedindo CAPTCHA humano
            processar_imovel(
                codigo_imovel, driver, captcha_cache,
                aba_link_imoveis, aba_banco_dados, planilha,
                progress=progress, worker_id=worker_id
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
    except Exception as e:
        print(f"❌ Erro ao carregar a planilha: {e}")
        return

    # ── Coleta imóveis marcados para extração ────────────────────
    imoveis = [
        row[1] for row in aba_link_imoveis.iter_rows(min_row=2, values_only=True)
        if len(row) >= 11 and str(row[10]).strip().lower() == "sim"
    ]
    total = len(imoveis)
    print(f"🔍 {total} imóveis selecionados para extração.")

    if not imoveis:
        print("⚠️ Nenhum imóvel marcado como 'Sim' na coluna K de 'Link de Imóveis'.")
        return

    # ── Divide e executa em paralelo ─────────────────────────────
    n = EXECUTION["n_workers"]
    chunks = [imoveis[i::n] for i in range(n)]
    progress = ProgressTracker(total=total, n_workers=n)
    print(f"⚡ Iniciando {n} workers em paralelo...\n")

    with ThreadPoolExecutor(max_workers=n) as executor:
        futures = [
            executor.submit(
                worker, i + 1, chunks[i], planilha,
                aba_link_imoveis, aba_banco_dados, progress
            )
            for i in range(n)
        ]
        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"❌ Worker encerrou com exceção: {e}")

    print("✅ Extração concluída.")


if __name__ == "__main__":
    main()
