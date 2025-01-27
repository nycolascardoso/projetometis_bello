from selenium_tasks import iniciar_driver, realizar_login, extrair_tabela_imoveis
from utils import carregar_planilha, atualizar_status_consultar
from config import PLANILHA_PATH

# Carregar a planilha e selecionar as abas
try:
    planilha = carregar_planilha(PLANILHA_PATH)
    aba_consultar = planilha['Consultar']
    aba_links = planilha['Link de Imóveis']
    print("Planilha carregada com sucesso.")
except Exception as e:
    print(f"Erro ao carregar a planilha: {e}")
    raise

# Iniciar o driver do Selenium
driver = iniciar_driver()

try:
    for linha in aba_consultar.iter_rows(min_row=2, min_col=1, max_col=4, values_only=True):
        cnpj_cpf, _, _, tipo_doc = linha

        if cnpj_cpf and tipo_doc:
            try:
                print(f"Iniciando processamento para CNPJ/CPF: {cnpj_cpf}, Tipo de Documento: {tipo_doc}")
                
                # Atualizar status para "Em progresso"
                atualizar_status_consultar(aba_consultar, cnpj_cpf, "Em progresso", PLANILHA_PATH)

                # Realizar login
                realizar_login(driver, cnpj_cpf, tipo_doc)

                # Extrair a tabela de imóveis e salvar na aba "Link de Imóveis"
                extrair_tabela_imoveis(driver, cnpj_cpf, aba_links, planilha, PLANILHA_PATH)

                # Atualizar status para "Finalizado"
                atualizar_status_consultar(aba_consultar, cnpj_cpf, "Finalizado", PLANILHA_PATH)
                print(f"Processamento finalizado com sucesso para {cnpj_cpf}")

            except Exception as e:
                # Registrar o erro diretamente no status
                atualizar_status_consultar(aba_consultar, cnpj_cpf, f"Erro: {e}", PLANILHA_PATH)
                print(f"Erro ao processar CNPJ/CPF {cnpj_cpf}: {e}")

except Exception as e:
    print(f"Erro geral durante a execução: {e}")
finally:
    # Fechar o driver ao final do processo
    driver.quit()
    print("Driver encerrado.")


