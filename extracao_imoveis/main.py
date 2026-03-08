import json
from datetime import datetime
from extracao_imoveis.selenium_tasks import iniciar_driver, realizar_login, extrair_tabela_imoveis
from extracao_imoveis.utils import carregar_planilha, atualizar_status_consultar, salvar_dados_na_aba
from extracao_imoveis.config import PLANILHA_PATH, STATUS_PATH

_log_msgs = []

def _escrever_status(current, total, item, msg, running=True):
    """Grava progresso em runtime_status.json para o app Streamlit ler."""
    _log_msgs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    status = {
        "running": running,
        "module": "imoveis",
        "current": current,
        "total": total,
        "current_item": str(item),
        "log": _log_msgs[-50:],
    }
    try:
        with open(STATUS_PATH, 'w', encoding='utf-8') as f:
            json.dump(status, f, ensure_ascii=False)
    except Exception:
        pass

def main():
    driver = None
    planilha = None

    try:
        planilha = carregar_planilha(PLANILHA_PATH)
        aba_consultar = planilha['Consultar']
        aba_links = planilha['Link de Imóveis']
        print("📂 Planilha carregada com sucesso.")

        # Pré-coleta as linhas a processar para saber o total
        linhas_para_processar = [
            linha for linha in aba_consultar.iter_rows(min_row=2, min_col=1, max_col=5, values_only=True)
            if linha[0] and linha[3] and linha[4] and str(linha[4]).strip().lower() == "sim"
        ]
        total = len(linhas_para_processar)
        print(f"🔍 {total} CNPJ(s)/CPF(s) selecionados para extração.")
        _escrever_status(0, total, "", f"{total} registro(s) selecionados para processamento")

        driver = iniciar_driver()

        for idx, linha in enumerate(linhas_para_processar, start=1):
            cnpj_cpf, _, _, tipo_doc, processar_flag = linha
            tentativas = 3

            _escrever_status(idx - 1, total, cnpj_cpf, f"Iniciando: {cnpj_cpf} ({tipo_doc})")

            for tentativa in range(1, tentativas + 1):
                try:
                    print(f"\n🔄 Tentativa {tentativa}/{tentativas} para {cnpj_cpf} ({tipo_doc})")
                    _escrever_status(idx - 1, total, cnpj_cpf,
                                     f"Tentativa {tentativa}/{tentativas} — {cnpj_cpf}")

                    atualizar_status_consultar(aba_consultar, cnpj_cpf, "Em progresso")
                    realizar_login(driver, cnpj_cpf, tipo_doc)
                    extrair_tabela_imoveis(driver, cnpj_cpf, aba_links)
                    atualizar_status_consultar(aba_consultar, cnpj_cpf, "Finalizado")

                    _escrever_status(idx, total, cnpj_cpf, f"✅ Concluído: {cnpj_cpf}")
                    print(f"🟢 Processamento finalizado para {cnpj_cpf}")
                    break

                except Exception as e:
                    print(f"❌ Erro na tentativa {tentativa}: {e}")
                    _escrever_status(idx - 1, total, cnpj_cpf,
                                     f"❌ Erro tentativa {tentativa}: {str(e)[:120]}")
                    if tentativa == tentativas:
                        atualizar_status_consultar(aba_consultar, cnpj_cpf, f"Erro: {e}")
                        print(f"⛔ Login falhou após {tentativas} tentativas para {cnpj_cpf}")
                        _escrever_status(idx, total, cnpj_cpf,
                                         f"⛔ Falhou após {tentativas} tentativas: {cnpj_cpf}")

    except Exception as e:
        print(f"❌ Erro geral durante a execução: {e}")
        _escrever_status(0, 0, "", f"❌ Erro geral: {str(e)[:200]}", running=False)

    finally:
        if planilha:
            try:
                planilha.save(PLANILHA_PATH)
                print("✅ Planilha salva com sucesso!")
            except Exception as e:
                print(f"❌ Erro ao salvar planilha: {e}")

        if driver:
            try:
                driver.quit()
                print('Driver encerrado.')
            except Exception as e:
                print(f'Erro ao encerrar o driver: {e}')

        _escrever_status(0, 0, "", "Processamento de imóveis finalizado", running=False)

if __name__ == "__main__":
    main()

#python -m extracao_imoveis.main
