from selenium_tasks import iniciar_driver, consultar_imovel
from utils import carregar_planilha, atualizar_status_consultar
from config import PLANILHA_PATH

# Carregar a planilha e selecionar as abas
planilha = carregar_planilha(PLANILHA_PATH)
aba_consultar = planilha['Consultar']
aba_links = planilha['Link de Imóveis']
aba_banco_dados = planilha['Banco de Dados']
aba_log = planilha['Log de Execução']

# Iniciar o driver do Selenium
driver = iniciar_driver()

# Processar os CNPJs/CPFs na aba "Consultar"
for linha in aba_consultar.iter_rows(min_row=2, min_col=1, max_col=4, values_only=True):
    cnpj_cpf, _, _, tipo_doc = linha

    if cnpj_cpf and tipo_doc:
        try:
            # Atualizar o status na aba "Consultar" para "Em progresso"
            atualizar_status_consultar(aba_consultar, cnpj_cpf, "Em progresso", PLANILHA_PATH)

            # Consultar o imóvel (login, extração de links e débitos)
            consultar_imovel(driver, cnpj_cpf, tipo_doc, planilha, aba_links, aba_banco_dados, aba_log)

            # Atualizar o status na aba "Consultar" para "Finalizado"
            atualizar_status_consultar(aba_consultar, cnpj_cpf, "Finalizado", PLANILHA_PATH)

        except Exception as e:
            # Atualizar o status na aba "Consultar" para "Erro" e registrar o erro
            atualizar_status_consultar(aba_consultar, cnpj_cpf, f"Erro: {str(e)}", PLANILHA_PATH)

# Fechar o driver
driver.quit()

print("Processo concluído com sucesso.")


