from selenium_tasks import iniciar_driver, realizar_login, extrair_tabela_imoveis
from utils import carregar_planilha, atualizar_status_consultar
from config import PLANILHA_PATH

# Flag para ativar o modo de teste unitário
TEST_MODE = False  # Altere para False para execução normal

if TEST_MODE:
    # Modo de teste: utiliza um CPF/CNPJ e Tipo de Documento de exemplo
    # Note que, neste exemplo, o primeiro valor é sobrescrito; portanto, será usado "005.056.569-90"
    
    tipo_doc_teste = "CPF proprietário"  
    cnpj_cpf_teste = "005.056.569-90"   # Valor final a ser usado (pode ser "CNPJ" se necessário)
    
    print("Modo de teste ativado.")
    
    try:
        # Carrega a planilha apenas para salvar os dados na aba "Link de Imóveis"
        planilha = carregar_planilha(PLANILHA_PATH)
        aba_links = planilha['Link de Imóveis']
        print("Planilha carregada com sucesso.")
    except Exception as e:
        print(f"Erro ao carregar a planilha: {e}")
        raise

    driver = iniciar_driver()

    try:
        print(f"\nIniciando teste de extração para CNPJ/CPF: {cnpj_cpf_teste}, Tipo de Documento: {tipo_doc_teste}")
        
        # Realiza o login; se o login não for bem-sucedido, a função já lançará exceção
        realizar_login(driver, cnpj_cpf_teste, tipo_doc_teste)
        
        # Extração dos dados (a função internamente decide se usa a lógica de tabela ou de imóvel único)
        extrair_tabela_imoveis(driver, cnpj_cpf_teste, aba_links, planilha, PLANILHA_PATH)
        
        print(f"Teste finalizado com sucesso para {cnpj_cpf_teste}")
    except Exception as e:
        print(f"Erro durante o teste de extração para {cnpj_cpf_teste}: {e}")
    finally:
        driver.quit()
        print("Driver encerrado no modo de teste.")

else:
    try:
        # Carrega a planilha e seleciona as abas "Consultar" e "Link de Imóveis"
        planilha = carregar_planilha(PLANILHA_PATH)
        aba_consultar = planilha['Consultar']
        aba_links = planilha['Link de Imóveis']
        print("Planilha carregada com sucesso.")
    except Exception as e:
        print(f"Erro ao carregar a planilha: {e}")
        raise

    driver = iniciar_driver()

    try:
        # Estrutura esperada na aba "Consultar": 
        # [CNPJ/CPF, Status, Última Atualização, Tipo de Doc., Processar]
        for linha in aba_consultar.iter_rows(min_row=2, min_col=1, max_col=5, values_only=True):
            cnpj_cpf = linha[0]
            tipo_doc = linha[3]
            processar_flag = linha[4]  # Valor da coluna "Processar"
            
            # Processa somente se "Processar" estiver marcado como "Sim"
            if cnpj_cpf and tipo_doc and processar_flag and processar_flag.strip().lower() == "sim":
                try:
                    print(f"\nIniciando processamento para CNPJ/CPF: {cnpj_cpf}, Tipo de Documento: {tipo_doc}")
                    
                    # Atualiza o status para "Em progresso" na aba "Consultar"
                    atualizar_status_consultar(aba_consultar, cnpj_cpf, "Em progresso", PLANILHA_PATH)
                    
                    # Realiza o login (caso o login falhe, uma exceção é lançada)
                    realizar_login(driver, cnpj_cpf, tipo_doc)
                    
                    # Extrai os dados (a função decide se é tabela ou imóvel único) e salva na aba "Link de Imóveis"
                    extrair_tabela_imoveis(driver, cnpj_cpf, aba_links, planilha, PLANILHA_PATH)
                    
                    # Atualiza o status para "Finalizado" e redefine "Processar" para "Não"
                    atualizar_status_consultar(aba_consultar, cnpj_cpf, "Finalizado", PLANILHA_PATH)
                    print(f"Processamento finalizado com sucesso para {cnpj_cpf}")
                except Exception as e:
                    # Em caso de erro, atualiza o status com a mensagem de erro e mantém o flag "Sim" para reprocessamento
                    atualizar_status_consultar(aba_consultar, cnpj_cpf, f"Erro: {e}", PLANILHA_PATH)
                    print(f"Erro ao processar CNPJ/CPF {cnpj_cpf}: {e}")
            else:
                print(f"Ignorando linha para CNPJ/CPF {cnpj_cpf}: 'Processar' não está marcado como 'Sim'.")
    except Exception as e:
        print(f"Erro geral durante a execução: {e}")
    finally:
        driver.quit()
        print("Driver encerrado.")

