import openpyxl
from datetime import datetime
from extracao_iptu.config import PLANILHA_PATH

# 🔹 Carrega a planilha de trabalho
def carregar_planilha():
    """Carrega a planilha Excel para leitura e escrita."""
    try:
        return openpyxl.load_workbook(PLANILHA_PATH)
    except Exception as e:
        print(f"❌ Erro ao carregar a planilha: {e}")
        raise

# 🔹 Salva a planilha após múltiplas operações
def salvar_planilha(planilha):
    """Salva a planilha para evitar perda de dados."""
    try:
        planilha.save(PLANILHA_PATH)
        print("💾 Planilha salva com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao salvar a planilha: {e}")
        raise

# 🔹 Atualiza o status na aba Consultar
def atualizar_status_consultar(aba, codigo_imovel, status):
    """Atualiza o status e a última atualização para um código de imóvel específico na aba Consultar."""
    try:
        for row in aba.iter_rows(min_row=2, values_only=False):
            if row[0].value == codigo_imovel:
                row[1].value = status  # Atualiza o status
                row[2].value = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Atualiza timestamp
                print(f"✅ Status atualizado para '{status}' no código do imóvel {codigo_imovel}.")
                return True
        return False
    except Exception as e:
        print(f"❌ Erro ao atualizar status: {e}")
        raise

# 🔹 Salva dados extraídos na aba "Banco de Dados"
def salvar_dados_na_aba(aba, dados, planilha):
    """Adiciona os dados extraídos na aba 'Banco de Dados' e salva tudo ao final."""
    try:
        dados_corrigidos = []
        for linha in dados:
            linha_corrigida = []
            for index, valor in enumerate(linha):
                if isinstance(valor, str):  # Se for string
                    valor = valor.strip()

                    # Mantém a inscrição imobiliária e descrições como string
                    if index in [0, 2]:  # Índices que não devem ser numéricos (exemplo: inscrição imobiliária e descrição da parcela)
                        linha_corrigida.append(valor)
                        continue

                    # Remover separador de milhar (.) e substituir vírgula decimal por ponto
                    valor_formatado = valor.replace(".", "").replace(",", ".")

                    # Verifica se o valor formatado é um número antes de converter
                    try:
                        valor = float(valor_formatado) if valor_formatado.replace(".", "").isdigit() else valor
                    except ValueError:
                        pass  # Mantém como string se não for conversível para float

                linha_corrigida.append(valor)
            dados_corrigidos.append(linha_corrigida)

        # 🔹 Insere todas as linhas na planilha de uma vez para otimizar desempenho
        for linha in dados_corrigidos:
            aba.append([""] + linha)  # Adiciona célula vazia na primeira coluna para manter alinhamento
        
        print(f"✅ {len(dados_corrigidos)} registros salvos na aba '{aba.title}'.")

        # 🔹 Salva a planilha ao final
        planilha.save(PLANILHA_PATH)
        print("💾 Planilha salva com sucesso.")

    except Exception as e:
        print(f"❌ Erro ao salvar dados na aba '{aba.title}': {e}")
        raise


# 🔹 Obtém linhas para processamento
def obter_linhas_para_processamento(aba):
    """Retorna os imóveis da aba 'Consultar' onde a coluna 'Processar' está marcada como 'Sim'."""
    linhas_processar = []
    try:
        for row in aba.iter_rows(min_row=2, values_only=True):
            codigo_imovel = row[0]
            processar = row[4]
            if processar and str(processar).strip().lower() == "sim":
                linhas_processar.append({"codigo_imovel": codigo_imovel})
        print(f"🔍 {len(linhas_processar)} imóveis identificados para processamento.")
        return linhas_processar
    except Exception as e:
        print(f"❌ Erro ao obter linhas para processamento: {e}")
        raise

# 🔹 Atualiza o status do IPTU na aba "Link de Imóveis"
def atualizar_status_iptu(aba, codigo_imovel, status):
    """Atualiza o status da extração do IPTU na aba 'Link de Imóveis' (Coluna L)."""
    try:
        for row in aba.iter_rows(min_row=2, values_only=False):
            if row[1].value == codigo_imovel:  # Código do imóvel está na coluna B (índice 1)
                row[11].value = status  # Coluna L (índice 11) recebe o status
                aba.parent.save(PLANILHA_PATH)
                print(f"✅ [DEBUG] Status atualizado para '{status}' no Código do Imóvel {codigo_imovel}.")
                return True
        print(f"⚠️ [DEBUG] Código do imóvel {codigo_imovel} não encontrado para atualização.")
        return False
    except Exception as e:
        print(f"❌ Erro ao atualizar status IPTU: {e}")
        raise

# 🔹 Atualiza dados do imóvel na aba "Link de Imóveis"
def atualizar_dados_imovel(aba, codigo_imovel, localizacao, tipologia, estrutura, utilizacao, proprietario):
    """Atualiza as colunas M, N, O, P e Q na aba 'Link de Imóveis'."""
    try:
        for row in aba.iter_rows(min_row=2, values_only=False):  
            if row[1].value == codigo_imovel:  # Código do imóvel na Coluna B (índice 1)
                
                # **Verifica se o imóvel é baldio e preenche automaticamente**
                if "baldio" in utilizacao.lower():
                    print(f"🏗️ Imóvel {codigo_imovel} identificado como BALDIO. Preenchendo automaticamente os dados...")
                    localizacao = tipologia = estrutura = utilizacao = proprietario = "Baldio s/uso"

                row[12].value = localizacao  # Coluna M (Localização)
                row[13].value = tipologia  # Coluna N (Tipologia)
                row[14].value = estrutura  # Coluna O (Estrutura)
                row[15].value = utilizacao  # Coluna P (Utilização)
                row[16].value = proprietario  # Coluna Q (Proprietário)

                print(f"✅ Dados do imóvel {codigo_imovel} atualizados na aba 'Link de Imóveis'.")

                # Salva apenas se for necessário (não a cada linha para otimizar desempenho)
                aba.parent.save(PLANILHA_PATH)
                return True

        print(f"⚠️ Código do imóvel {codigo_imovel} não encontrado na aba 'Link de Imóveis'.")
        return False

    except Exception as e:
        print(f"❌ Erro ao atualizar dados do imóvel {codigo_imovel}: {e}")
        raise

