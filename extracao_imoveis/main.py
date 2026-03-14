from pathlib import Path
import sys
import ctypes

# Impede que o Windows suspenda o sistema enquanto o script estiver rodando.
# ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
if sys.platform == 'win32':
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001 | 0x00000002)

if __name__ == '__main__' and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from extracao_imoveis.selenium_tasks import iniciar_driver, realizar_login, extrair_tabela_imoveis
from extracao_imoveis.utils import (
    carregar_planilha,
    atualizar_status_consultar,
    salvar_dados_na_aba,
    obter_linhas_para_processamento,
)
from extracao_imoveis.config import PLANILHA_PATH

try:
    # Carrega planilha e abas
    planilha = carregar_planilha(PLANILHA_PATH)
    aba_consultar = planilha['Consultar']
    aba_links = planilha['Link de Imóveis']
    print('📂 Planilha carregada com sucesso.')

    # Verifica linhas marcadas para processamento
    linhas_processar = obter_linhas_para_processamento(aba_consultar)
    print(f'🔎 Linhas a processar: {len(linhas_processar)}')

    if not linhas_processar:
        print("⚠️ Nenhuma linha marcada como 'Sim' na aba 'Consultar'.")
        print("Dica: Preencha CNPJ/CPF, 'Tipo de Doc.' e marque 'Processar' = 'Sim'.")
    else:
        driver = iniciar_driver()
        try:
            for item in linhas_processar:
                cnpj_cpf = item.get('cnpj_cpf')
                tipo_doc = item.get('tipo_doc')
                tentativas = 3

                for tentativa in range(1, tentativas + 1):
                    try:
                        print(f"\n🔧 Tentativa {tentativa}/{tentativas} para {cnpj_cpf} ({tipo_doc})")
                        atualizar_status_consultar(aba_consultar, cnpj_cpf, 'Em progresso')

                        realizar_login(driver, cnpj_cpf, tipo_doc)
                        extrair_tabela_imoveis(driver, cnpj_cpf, aba_links)

                        atualizar_status_consultar(aba_consultar, cnpj_cpf, 'Finalizado')
                        planilha.save(PLANILHA_PATH)
                        print(f'✅ Processamento finalizado para {cnpj_cpf}')
                        break

                    except Exception as e:
                        print(f"❌ Erro na tentativa {tentativa}: {e}")
                        if tentativa == tentativas:
                            atualizar_status_consultar(aba_consultar, cnpj_cpf, f'Erro: {e}')
                            print(f"⏭️ Login falhou após {tentativas} tentativas para {cnpj_cpf}")
        finally:
            try:
                driver.quit()
                print('🚪 Driver encerrado.')
            except Exception as e:
                print(f'⚠️ Erro ao encerrar o driver: {e}')

except Exception as e:
    print(f'❌ Erro ao carregar/operar a planilha: {e}')

finally:
    try:
        planilha.save(PLANILHA_PATH)
        print('💾 Planilha salva com sucesso!')
    except Exception as e:
        print(f'⚠️ Erro ao salvar a planilha: {e}')
