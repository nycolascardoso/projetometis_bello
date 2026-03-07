import openpyxl
import os
from datetime import datetime
from extracao_iptu.config import PLANILHA_PATH

# 🔹 Carrega a planilha com verificação de integridade
def carregar_planilha():
    """Carrega a planilha Excel garantindo que não esteja corrompida."""
    try:
        if not os.path.exists(PLANILHA_PATH):
            print(f"❌ Arquivo da planilha não encontrado: {PLANILHA_PATH}")
            return None

        planilha = openpyxl.load_workbook(PLANILHA_PATH)
        print("📂 Planilha carregada com sucesso.")
        return planilha
    except Exception as e:
        print(f"❌ Erro ao carregar a planilha: {e}")
        return None

def salvar_planilha(planilha):
    """Salva a planilha garantindo que não esteja fechada e evitando erro de I/O."""
    try:
        if planilha is None:
            print("⚠️ Planilha não está carregada. Tentando reabrir...")
            planilha = carregar_planilha()
        
        temp_path = PLANILHA_PATH.replace(".xlsx", "_temp.xlsx")  # Criar backup temporário antes de salvar
        
        # Evita erro de arquivo fechado
        try:
            planilha.save(temp_path)
        except ValueError:
            print("⚠️ Planilha fechada inesperadamente. Tentando reabrir antes de salvar...")
            planilha = carregar_planilha()
            planilha.save(temp_path)

        os.replace(temp_path, PLANILHA_PATH)  # Substitui a planilha original
        print("💾 Planilha salva com sucesso.")

    except Exception as e:
        print(f"❌ Erro ao salvar a planilha: {e}")



# 🔹 Atualiza o status na aba Consultar
def atualizar_status_consultar(aba, codigo_imovel, status, planilha):
    """Atualiza o status e a última atualização para um código de imóvel na aba Consultar."""
    try:
        for row in aba.iter_rows(min_row=2, values_only=False):
            if str(row[0].value) == str(codigo_imovel):
                row[1].value = status  # Atualiza o status
                row[2].value = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Atualiza timestamp
                print(f"✅ Status atualizado para '{status}' no código do imóvel {codigo_imovel}.")
                salvar_planilha(planilha)
                return True
        return False
    except Exception as e:
        print(f"❌ Erro ao atualizar status: {e}")

# 🔹 Salva dados extraídos na aba "Banco de Dados"
def salvar_dados_na_aba(aba, dados, planilha):
    """Adiciona os dados extraídos na aba 'Banco de Dados' e salva tudo ao final."""
    try:
        if not aba or not planilha:
            print("❌ Erro: Aba ou planilha inválida ao tentar salvar dados.")
            return

        for linha in dados:
            aba.append(linha)  # Remove a célula vazia antes do registro

        print(f"✅ {len(dados)} registros salvos na aba '{aba.title}'.")
        salvar_planilha(planilha)

    except Exception as e:
        print(f"❌ Erro ao salvar dados na aba '{aba.title}': {e}")

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

# 🔹 Atualiza status IPTU
def atualizar_status_iptu(aba, codigo_imovel, status, planilha):
    """Atualiza o status do imóvel na planilha."""
    try:
        for row in aba.iter_rows(min_row=2, values_only=False):
            if str(row[1].value) == str(codigo_imovel):
                row[10].value = status  # Atualiza a coluna de status
                print(f"✅ Status atualizado para '{status}' no Código do Imóvel {codigo_imovel}.")
                salvar_planilha(planilha)  # Salva apenas se houver alteração
                return True
        print(f"⚠️ Código do imóvel {codigo_imovel} não encontrado na aba 'Link de Imóveis'.")
        return False
    except Exception as e:
        print(f"❌ Erro ao atualizar status IPTU: {e}")

# 🔹 Atualiza dados do imóvel na aba "Link de Imóveis"
def atualizar_dados_imovel(aba, codigo_imovel, localizacao, tipologia, estrutura, utilizacao, proprietario, planilha):
    """Atualiza as colunas M, N, O, P e Q na aba 'Link de Imóveis'."""
    try:
        for row in aba.iter_rows(min_row=2, values_only=False):
            if str(row[1].value) == str(codigo_imovel):  # Código do imóvel na Coluna B (índice 1)

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
                salvar_planilha(planilha)
                return True

        print(f"⚠️ Código do imóvel {codigo_imovel} não encontrado na aba 'Link de Imóveis'.")
        return False

    except Exception as e:
        print(f"❌ Erro ao atualizar dados do imóvel {codigo_imovel}: {e}")
