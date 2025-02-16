from extracao_iptu.selenium_tasks import iniciar_driver, realizar_login, acessar_carnê_iptu, extrair_tabela_iptu
from extracao_iptu.utils import carregar_planilha, salvar_dados_na_aba
from extracao_iptu.config import PLANILHA_PATH


def main():
    # Carrega a planilha
    try:
        planilha = carregar_planilha(PLANILHA_PATH)
        aba_banco_dados = planilha['Banco de Dados']
        print("📂 Planilha carregada com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao carregar a planilha: {e}")
        return

    # Inicia o WebDriver
    driver = iniciar_driver()
    try:
        # Substitua pelo código do imóvel que deseja testar
        codigo_imovel_teste = '1247'
        print(f"\n🏠 Iniciando teste para código do imóvel: {codigo_imovel_teste}")

        tentativas = 3  # Definir número máximo de tentativas para login
        sucesso = False

        for tentativa in range(1, tentativas + 1):
            try:
                print(f"🔄 Tentativa {tentativa}/{tentativas} para login com código do imóvel: {codigo_imovel_teste}")

                # Realiza login e navega até a página do Carnê IPTU
                realizar_login(driver, codigo_imovel_teste)
                acessar_carnê_iptu(driver)

                # Se chegou até aqui, login foi bem-sucedido
                sucesso = True
                break  # Sai do loop de tentativas

            except Exception as e:
                print(f"⚠️ Erro ao tentar login ({tentativa}/{tentativas}): {e}")
                if tentativa == tentativas:
                    print(f"❌ Falha ao realizar login após {tentativas} tentativas. Abortando...")
                    return

        if sucesso:
            # Extrai a tabela de IPTU
            dados_iptu = extrair_tabela_iptu(driver)

            # Salva os dados extraídos na aba "Banco de Dados", começando na segunda coluna
            for linha_dados in dados_iptu:
                if not isinstance(linha_dados, list):
                    linha_dados = [linha_dados]  # Garante que os dados sejam uma lista
                salvar_dados_na_aba(aba_banco_dados, [""] + linha_dados, PLANILHA_PATH)  # Adiciona uma coluna vazia no início
            
            print(f"🟢 Teste finalizado com sucesso para o imóvel {codigo_imovel_teste}")

    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
    
    finally:
        # Finaliza o WebDriver ao término da execução
        driver.quit()
        print("🛑 Driver encerrado.")


if __name__ == "__main__":
    main()


#python -m extracao_iptu.main_unique