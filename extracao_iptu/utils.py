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
    Adiciona uma nova linha de dados à aba Banco de Dados, garantindo que os dados sejam uma lista.
    """
    try:
        if not isinstance(dados, list):
            dados = [dados]  # Garante que os dados estejam em formato de lista
        aba.append(dados)
        aba.parent.save(caminho)
        print(f"💾 Dados salvos na aba '{aba.title}': {dados}")
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

