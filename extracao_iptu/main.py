from extracao_iptu.selenium_tasks import (
    iniciar_driver,
    realizar_login,
    acessar_carne_iptu,
    extrair_tabela_iptu,
    capturar_inscricao_imobiliaria,
    capturar_dados_adicionais
)
from extracao_iptu.utils import (
    carregar_planilha,
    salvar_planilha,
    salvar_dados_na_aba,
    atualizar_status_iptu,
    atualizar_dados_imovel
)
from extracao_iptu.config import SETTINGS, PLANILHA_PATH, SELECTORS

def main():
    # Carrega a planilha e as abas necessárias
    try:
        planilha = carregar_planilha()
        aba_link_imoveis = planilha['Link de Imóveis']
        aba_banco_dados = planilha['Banco de Dados']
        print("📂 Planilha carregada com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao carregar a planilha: {e}")
        return

    # Obtém todos os imóveis que devem ser extraídos (Coluna K == "Sim")
    imoveis_para_processar = [
        row[1] for row in aba_link_imoveis.iter_rows(min_row=2, values_only=True)
        if len(row) >= 11 and str(row[10]).strip().lower() == "sim"
    ]

    print(f"🔍 {len(imoveis_para_processar)} imóveis selecionados para extração.")

    # Inicia o WebDriver
    driver = iniciar_driver()

    try:
        for idx, codigo_imovel in enumerate(imoveis_para_processar, start=1):
            print(f"\n🏠 Iniciando extração {idx}/{len(imoveis_para_processar)} - Código do imóvel: {codigo_imovel}")

            sucesso = False

            for tentativa in range(1, SETTINGS["max_tentativas_login"] + 1):
                try:
                    print(f"🔄 Tentativa {tentativa}/{SETTINGS['max_tentativas_login']} para login com código do imóvel: {codigo_imovel}")
                    
                    # Realiza login
                    if not realizar_login(driver, codigo_imovel):
                        continue  # Se falhar, tenta novamente

                    # Captura Inscrição Imobiliária
                    inscricao_imobiliaria = capturar_inscricao_imobiliaria(driver) or "N/A"

                    # Verifica se o imóvel é baldio antes de capturar os outros dados
                    ocupacao_elemento = driver.find_element("xpath", SELECTORS["ocupacao"])
                    ocupacao = ocupacao_elemento.get_attribute("value").strip().lower()

                    if "baldio" in ocupacao:
                        print("🏗️ Imóvel identificado como BALDIO. Preenchendo automaticamente os dados...")
                        dados_adicionais = {
                            "localizacao": "Baldio s/uso",
                            "tipologia": "Baldio s/uso",
                            "estrutura": "Baldio s/uso",
                            "utilizacao": "Baldio s/uso",
                            "proprietario": "Baldio s/uso"
                        }
                    else:
                        # Captura os demais dados
                        dados_adicionais = capturar_dados_adicionais(driver)

                    # Acessa a página do Carnê IPTU
                    acessar_carne_iptu(driver)
                    sucesso = True
                    break  # Sai do loop de tentativas

                except Exception as e:
                    print(f"⚠️ Erro ao tentar login ({tentativa}/{SETTINGS['max_tentativas_login']}): {e}")
                    if tentativa == SETTINGS["max_tentativas_login"]:
                        print(f"❌ Falha ao realizar login após {SETTINGS['max_tentativas_login']} tentativas. Pulando para o próximo imóvel.")
                        atualizar_status_iptu(aba_link_imoveis, codigo_imovel, "Erro de Processamento")
                        salvar_planilha(planilha)

            if sucesso:
                try:
                    # Extrai a tabela de IPTU
                    dados_iptu = extrair_tabela_iptu(driver)

                    # Atualiza a aba "Link de Imóveis" com os novos dados coletados
                    atualizar_dados_imovel(
                        aba_link_imoveis,
                        codigo_imovel,
                        dados_adicionais["localizacao"],
                        dados_adicionais["tipologia"],
                        dados_adicionais["estrutura"],
                        dados_adicionais["utilizacao"],
                        dados_adicionais["proprietario"],
                        planilha
                    )
                    salvar_planilha(planilha)

                    if not dados_iptu:
                        print(f"⚠️ Nenhum dado extraído para o imóvel {codigo_imovel}. Registrando como 'Sem Carnê IPTU'.")
                        salvar_dados_na_aba(
                            aba_banco_dados,
                            ["", [inscricao_imobiliaria, "2025", "Sem Carnê IPTU", "", "", "", "", "", "", "", "", "", codigo_imovel]],
                            planilha
                        )
                        atualizar_status_iptu(aba_link_imoveis, codigo_imovel, "Erro de Processamento", planilha)
                        salvar_planilha(planilha)
                        continue

                    # Salva os dados extraídos na aba "Banco de Dados"
                    dados_para_salvar = []
                    for linha_dados in dados_iptu:
                        descricao = linha_dados[1]  # A segunda coluna contém a descrição da parcela
                        tipo_pagamento = "Parcelado"

                        if "Cota Única 20%" in descricao:
                            tipo_pagamento = "Cota Única 20%"
                        elif "Cota Única 10%" in descricao:
                            tipo_pagamento = "Cota Única 10%"

                        linha_processada = [inscricao_imobiliaria] + linha_dados + [tipo_pagamento, codigo_imovel]
                        dados_para_salvar.append(linha_processada)

                    salvar_dados_na_aba(aba_banco_dados, dados_para_salvar, planilha)

                    atualizar_status_iptu(aba_link_imoveis, codigo_imovel, "Sim", planilha)
                    salvar_planilha(planilha)

                    print(f"🟢 Dados do imóvel {codigo_imovel} salvos com sucesso!")

                except Exception as e:
                    print(f"❌ Erro ao processar código do imóvel {codigo_imovel}: {e}")
                    atualizar_status_iptu(aba_link_imoveis, codigo_imovel, "Erro de Processamento")
                    salvar_planilha(planilha)

    finally:
        try:
            salvar_planilha(planilha)
            print("💾 Planilha salva com sucesso!")
        except Exception as e:
            print(f"⚠️ Erro ao salvar a planilha no final: {e}")

        driver.quit()
        print("🛑 Driver encerrado.")

if __name__ == "__main__":
    main()




#python -m extracao_iptu.main