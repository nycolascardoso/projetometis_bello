import openpyxl
from datetime import datetime
from config import PLANILHA_PATH

def carregar_planilha(caminho):
    """Carrega a planilha Excel."""
    try:
        return openpyxl.load_workbook(caminho)
    except Exception as e:
        print(f"Erro ao carregar a planilha: {e}")
        raise

def atualizar_status_consultar(aba, cnpj_cpf, status, caminho):
    """
    Atualiza o status e a última atualização na aba 'Consultar'.

    - aba: Aba "Consultar" da planilha.
    - cnpj_cpf: O CNPJ/CPF cujo status será atualizado.
    - status: Novo status (ex.: "Em progresso", "Finalizado", "Erro").
    - caminho: Caminho para salvar a planilha após a atualização.
    """
    try:
        for row in aba.iter_rows(min_row=2, values_only=False):
            if row[0].value == cnpj_cpf:  # Verifica se o CNPJ/CPF corresponde
                row[1].value = status  # Atualiza o status
                row[2].value = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Atualiza a última data/hora
                aba.parent.save(caminho)  # Salva a planilha
                print(f"Status atualizado para '{status}' no CNPJ/CPF {cnpj_cpf}.")
                break
    except Exception as e:
        print(f"Erro ao atualizar status: {e}")
        raise

def salvar_dados_na_aba(aba, dados):
    """
    Adiciona uma nova linha com os dados na aba fornecida.

    - aba: A aba onde os dados serão adicionados.
    - dados: Lista com os valores a serem adicionados como nova linha.
    """
    try:
        aba.append(dados)  # Adiciona os dados na aba
        aba.parent.save(PLANILHA_PATH)  # Salva as alterações na planilha
        print(f"Dados salvos na aba '{aba.title}': {dados}")
    except Exception as e:
        print(f"Erro ao salvar dados na aba '{aba.title}': {e}")
        raise

