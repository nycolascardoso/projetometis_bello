from extracao_iptu.selenium_tasks import iniciar_driver, realizar_login, acessar_carnê_iptu, extrair_tabela_iptu
from extracao_iptu.utils import carregar_planilha, atualizar_status_consultar, salvar_dados_na_aba
from extracao_iptu.config import PLANILHA_PATH

def main():
    # Carrega a planilha e seleciona as abas necessárias
    try:
        planilha = carregar_planilha(PLANILHA_PATH)
        aba_consultar = planilha['Consultar']
        aba_banco_dados = planilha['Banco de Dados']
        print("📂 Planilha carregada com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao carregar a planilha: {e}")
        return

    # Inicia o WebDriver
    driver = iniciar_driver()
    try:
        # Itera por cada linha da aba "Consultar" que deve ser processada
        for linha in aba_consultar.iter_rows(min_row=2, values_only=True):
            codigo_imovel = linha[0]
            status = linha[1]
            processar = linha[4]
            
            # Processa apenas se a coluna "Processar" está marcada como "Sim"
            if processar and processar.strip().lower() == "sim":
                print(f"\nIniciando processamento para código do imóvel: {codigo_imovel}")
                
                try:
                    # Atualiza status para "Em progresso"
                    atualizar_status_consultar(aba_consultar, codigo_imovel, "Em progresso", PLANILHA_PATH)
                    
                    # Realiza o login e navega até a página do Carnê IPTU
                    realizar_login(driver, codigo_imovel)
                    acessar_carnê_iptu(driver)
                    
                    # Extrai a tabela de IPTU
                    dados_iptu = extrair_tabela_iptu(driver)
                    
                    # Salva os dados extraídos na aba "Banco de Dados"
                    for linha_dados in dados_iptu:
                        salvar_dados_na_aba(aba_banco_dados, [codigo_imovel] + linha_dados)
                    
                    # Atualiza status para "Finalizado"
                    atualizar_status_consultar(aba_consultar, codigo_imovel, "Finalizado", PLANILHA_PATH)
                    print(f"🟢 Processamento finalizado para o imóvel {codigo_imovel}")

                except Exception as e:
                    # Em caso de erro, atualiza o status para "Erro" e mantém "Processar" como "Sim"
                    atualizar_status_consultar(aba_consultar, codigo_imovel, f"Erro: {e}", PLANILHA_PATH)
                    print(f"❌ Erro ao processar código do imóvel {codigo_imovel}: {e}")
    finally:
        # Finaliza o WebDriver ao término da execução
        driver.quit()
        print("🛑 Driver encerrado.")

if __name__ == "__main__":
    main()
