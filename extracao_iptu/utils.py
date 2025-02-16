import openpyxl
from datetime import datetime

# Carrega a planilha de trabalho
def carregar_planilha(caminho):
    """
    Carrega a planilha Excel para leitura e escrita.
    """
    try:
        return openpyxl.load_workbook(caminho)
    except Exception as e:
        print(f"Erro ao carregar a planilha: {e}")
        raise

# Atualiza o status na aba Consultar
def atualizar_status_consultar(aba, codigo_imovel, status, caminho):
    """
    Atualiza o status e a última atualização para um código de imóvel específico
    na aba Consultar.
    """
    try:
        for row in aba.iter_rows(min_row=2, values_only=False):
            if row[0].value == codigo_imovel:
                row[1].value = status  # Atualiza o status
                row[2].value = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Atualiza o timestamp
                aba.parent.save(caminho)
                print(f"✅ Status atualizado para '{status}' no código do imóvel {codigo_imovel}.")
                break
    except Exception as e:
        print(f"❌ Erro ao atualizar status: {e}")
        raise

# Salva dados extraídos na aba Banco de Dados
def salvar_dados_na_aba(aba, dados, caminho):
    """
    Adiciona os dados extraídos na aba "Banco de Dados", garantindo que os valores
    sejam inseridos a partir da 2ª coluna.
    """
    try:
        linha = [""] + dados  # Adiciona uma célula vazia na 1ª coluna
        aba.append(linha)
        aba.parent.save(caminho)
        print(f"💾 Dados salvos na aba '{aba.title}': {linha}")
    except Exception as e:
        print(f"❌ Erro ao salvar dados na aba '{aba.title}': {e}")
        raise

# Lê as linhas que precisam ser processadas
def obter_linhas_para_processamento(aba):
    """
    Retorna as linhas da aba Consultar onde a coluna "Processar" está marcada como "Sim".
    """
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

def atualizar_status_iptu(aba, codigo_imovel, status, caminho):
    """
    Atualiza o status da extração do IPTU na aba 'Link de Imóveis' (Coluna L).
    """
    try:
        for row in aba.iter_rows(min_row=2, values_only=False):
            if row[1].value == codigo_imovel:  # Código do imóvel está na coluna B (índice 1)
                row[11].value = status  # Coluna L (índice 11) recebe o status
                aba.parent.save(caminho)
                print(f"✅ Status atualizado para '{status}' no Código do Imóvel {codigo_imovel}.")
                break
    except Exception as e:
        print(f"❌ Erro ao atualizar status IPTU: {e}")



def atualizar_dados_imovel(aba, codigo_imovel, localizacao, tipologia, estrutura, utilizacao, proprietario, caminho):
    """
    Atualiza as colunas M, N, O, P e Q para o código do imóvel na aba "Link de Imóveis".
    """
    try:
        for row in aba.iter_rows(min_row=2, values_only=False):  
            if row[1].value == codigo_imovel:  # Verifica se o código do imóvel está na coluna B
                row[12].value = localizacao  # Coluna M (Localização)
                row[13].value = tipologia  # Coluna N (Tipologia)
                row[14].value = estrutura  # Coluna O (Estrutura)
                row[15].value = utilizacao  # Coluna P (Utilização)
                row[16].value = proprietario  # Coluna Q (Proprietário)

                aba.parent.save(caminho)  # Salva a planilha
                print(f"✅ Dados do imóvel {codigo_imovel} atualizados na aba 'Link de Imóveis'.")
                return  
        
        print(f"⚠️ Código do imóvel {codigo_imovel} não encontrado na aba 'Link de Imóveis'.")
    
    except Exception as e:
        print(f"❌ Erro ao atualizar dados do imóvel {codigo_imovel}: {e}")
