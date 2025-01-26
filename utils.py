import openpyxl
import re
from datetime import datetime
from config import PLANILHA_PATH

# Carregar a planilha
def carregar_planilha(planilha_path=PLANILHA_PATH):
    """
    Carrega a planilha Excel e retorna o objeto de workbook.
    """
    return openpyxl.load_workbook(planilha_path)

# Função para selecionar uma aba específica
def selecionar_abas(planilha):
    """
    Retorna as abas necessárias da planilha.
    """
    aba_consultar = planilha['Consultar']
    aba_links = planilha['Link de Imóveis']
    aba_log = planilha['Log de Execução']
    aba_banco_dados = planilha['Banco de Dados']
    return aba_consultar, aba_links, aba_log, aba_banco_dados

# Geração de nomes de arquivo
def gerar_nome_arquivo(cnpj_cpf):
    """
    Gera um nome de arquivo seguro removendo caracteres inválidos.
    """
    return re.sub(r'[\\/:*?"<>|]', '_', cnpj_cpf)

# Registro de log
def registrar_log(aba_log, cnpj_cpf, tipo_doc, status, mensagem="", planilha_path=PLANILHA_PATH):
    """
    Registra informações na aba de log.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    aba_log.append([timestamp, cnpj_cpf, tipo_doc, status, mensagem])
    aba_log.parent.save(planilha_path)  # Salvar as alterações na planilha

# Atualizar o status na aba "Consultar"
def atualizar_status_consultar(aba_consultar, cnpj_cpf, status, planilha_path=PLANILHA_PATH):
    """
    Atualiza o status e a data de última atualização na aba "Consultar".
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for linha in aba_consultar.iter_rows(min_row=2, min_col=1, max_col=4):
        if linha[0].value == cnpj_cpf:
            linha[1].value = status  # Atualizar o status
            linha[2].value = timestamp  # Atualizar a última atualização
            aba_consultar.parent.save(planilha_path)
            break

# Salvar os links na aba "Link de Imóveis"
def salvar_links(aba_links, cnpj_cpf, links, planilha_path=PLANILHA_PATH):
    """
    Registra os links na aba "Link de Imóveis".
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for link in links:
        aba_links.append([cnpj_cpf, link['codigo_imovel'], link['inscricao_imobiliaria'], link['link'], "Pendente", timestamp])
    aba_links.parent.save(planilha_path)

# Salvar os dados na aba "Banco de Dados"
def salvar_dados_banco(aba_banco_dados, cnpj_cpf, codigo_imovel, dados, planilha_path=PLANILHA_PATH):
    """
    Salva os dados extraídos na aba "Banco de Dados".
    """
    for linha in dados:
        aba_banco_dados.append([cnpj_cpf, codigo_imovel] + linha)
    aba_banco_dados.parent.save(planilha_path)
