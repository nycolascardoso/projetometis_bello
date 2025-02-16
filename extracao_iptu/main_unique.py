from extracao_iptu.selenium_tasks import (
    iniciar_driver, 
    realizar_login, 
    acessar_carnê_iptu, 
    extrair_tabela_iptu, 
    capturar_inscricao_imobiliaria,
    capturar_dados_adicionais  
)
from extracao_iptu.utils import (
    carregar_planilha, 
    salvar_dados_na_aba, 
    atualizar_status_iptu, 
    atualizar_dados_imovel  
)
from extracao_iptu.config import PLANILHA_PATH

def main():
    # Carrega a planilha e as abas necessárias
    try:
        planilha = carregar_planilha(PLANILHA_PATH)
        aba_link_imoveis = planilha['Link de Imóveis']
        aba_banco_dados = planilha['Banco de Dados']
        print("📂 Planilha carregada com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao carregar a planilha: {e}")
        return

    # Obtém os primeiros 100 imóveis que devem ser extraídos (Coluna K == "Sim")
    imoveis_para_processar = []
    
    for row in aba_link_imoveis.iter_rows(min_row=2, max_row=101, values_only=True):
        if len(row) < 11:  # Certifica que a linha tem pelo menos 11 colunas
            print(f"⚠️ Linha incompleta detectada e ignorada: {row}")
            continue

        codigo_imovel, extrair_iptu = row[1], row[10]  # Coluna B (Código do Imóvel) e Coluna K ("Extrair IPTU?")
        
        if codigo_imovel and extrair_iptu and str(extrair_iptu).strip().lower() == "sim":
            imoveis_para_processar.append(codigo_imovel)

    print(f"🔍 {len(imoveis_para_processar)} imóveis selecionados para extração.")

    # Inicia o WebDriver
    driver = iniciar_driver()

    try:
        for idx, codigo_imovel in enumerate(imoveis_para_processar, start=1):
            print(f"\n🏠 Iniciando extração {idx}/{len(imoveis_para_processar)} - Código do imóvel: {codigo_imovel}")

            tentativas = 2  # Reduzindo o número de tentativas para login
            sucesso = False

            for tentativa in range(1, tentativas + 1):
                try:
                    print(f"🔄 Tentativa {tentativa}/{tentativas} para login com código do imóvel: {codigo_imovel}")

                    # Realiza login
                    realizar_login(driver, codigo_imovel)

                    # Captura Inscrição Imobiliária
                    inscricao_imobiliaria = capturar_inscricao_imobiliaria(driver)

                    # Captura os novos dados (Localização, Tipologia, Estrutura, Utilização, Proprietário)
                    dados_adicionais = capturar_dados_adicionais(driver)

                    # Acessa a página do Carnê IPTU
                    acessar_carnê_iptu(driver)

                    # Se chegou até aqui, login foi bem-sucedido
                    sucesso = True
                    break  # Sai do loop de tentativas

                except Exception as e:
                    print(f"⚠️ Erro ao tentar login ({tentativa}/{tentativas}): {e}")
                    if tentativa == tentativas:
                        print(f"❌ Falha ao realizar login após {tentativas} tentativas. Pulando para o próximo imóvel.")
                        atualizar_status_iptu(aba_link_imoveis, codigo_imovel, "Erro de Processamento", PLANILHA_PATH)
                        sucesso = False

            if sucesso:
                try:
                    # Extrai a tabela de IPTU
                    dados_iptu = extrair_tabela_iptu(driver)

                    # **Atualizar a aba "Link de Imóveis" com os novos dados**
                    atualizar_dados_imovel(
                        aba_link_imoveis, 
                        codigo_imovel, 
                        dados_adicionais["localizacao"], 
                        dados_adicionais["tipologia"], 
                        dados_adicionais["estrutura"], 
                        dados_adicionais["utilizacao"], 
                        dados_adicionais["proprietario"], 
                        PLANILHA_PATH
                    )

                    if not dados_iptu:  # Se retornou None, registra como "Sem Carnê IPTU"
                        print(f"⚠️ Nenhum dado extraído para o imóvel {codigo_imovel}. Registrando como 'Sem Carnê IPTU'.")
                        
                        salvar_dados_na_aba(
                            aba_banco_dados, 
                            [inscricao_imobiliaria] + ["2025"] + ["Sem Carnê IPTU"] + [""] * 8 + [codigo_imovel],  
                            PLANILHA_PATH
                        )
                        atualizar_status_iptu(aba_link_imoveis, codigo_imovel, "Não", PLANILHA_PATH)
                        continue  # Pula para o próximo imóvel

                    # Salva os dados extraídos na aba "Banco de Dados"
                    for linha_dados in dados_iptu:
                        if not isinstance(linha_dados, list):
                            linha_dados = [linha_dados]  # Garante que os dados sejam uma lista
                        
                        # Adiciona Inscrição Imobiliária na primeira coluna, Código do Imóvel na 10ª coluna
                        salvar_dados_na_aba(
                            aba_banco_dados, 
                            [inscricao_imobiliaria] + linha_dados + [codigo_imovel], 
                            PLANILHA_PATH
                        )

                    atualizar_status_iptu(aba_link_imoveis, codigo_imovel, "Sim", PLANILHA_PATH)
                    print(f"🟢 Dados do imóvel {codigo_imovel} salvos com sucesso!")

                except Exception as e:
                    print(f"❌ Erro ao processar código do imóvel {codigo_imovel}: {e}")
                    atualizar_status_iptu(aba_link_imoveis, codigo_imovel, "Erro de Processamento", PLANILHA_PATH)

    finally:
        driver.quit()
        print("🛑 Driver encerrado.")

if __name__ == "__main__":
    main()

#python -m extracao_iptu.main_unique