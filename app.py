"""
Metis — App Streamlit para extração de dados imobiliários.
Execute com: python -m streamlit run app.py
Ou use o atalho: iniciar.bat
"""
import sys
import os
import subprocess
import time

import streamlit as st
import pandas as pd

import app_utils as utils

# ---------------------------------------------------------------------------
# Configuração da página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Metis — Extração de Dados Imobiliários",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    /* Reduz padding do header */
    .block-container { padding-top: 1.5rem; }
    /* Métrica com borda */
    [data-testid="metric-container"] {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 12px 16px;
    }
    /* Badge de status */
    .status-ok    { color: #198754; font-weight: 600; }
    .status-erro  { color: #dc3545; font-weight: 600; }
    .status-prog  { color: #0d6efd; font-weight: 600; }
    .status-pend  { color: #6c757d; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Inicializa session state
# ---------------------------------------------------------------------------
if 'processo' not in st.session_state:
    st.session_state.processo = None
if 'ultimo_modulo' not in st.session_state:
    st.session_state.ultimo_modulo = None
if 'ultimo_resultado' not in st.session_state:
    st.session_state.ultimo_resultado = None  # 'ok' | 'erro' | None

# ---------------------------------------------------------------------------
# Verifica processo em andamento
# ---------------------------------------------------------------------------
processo_ativo = (
    st.session_state.processo is not None
    and st.session_state.processo.poll() is None
)

# Processo terminou desde o último rerun
if st.session_state.processo is not None and not processo_ativo:
    ret = st.session_state.processo.poll()
    st.session_state.ultimo_resultado = 'ok' if ret == 0 else 'erro'
    st.session_state.processo = None

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
col_title, col_status = st.columns([5, 1])
with col_title:
    st.title("🏢 Metis — Extração de Dados Imobiliários")

with col_status:
    if processo_ativo:
        st.markdown("🔄 **Rodando...**")
    else:
        st.markdown("⚡ **Pronto**")

# ---------------------------------------------------------------------------
# Banner de progresso (visível em qualquer tab enquanto extração roda)
# ---------------------------------------------------------------------------
if processo_ativo:
    status_rt = utils.ler_status_runtime()
    modulo_nome = "Imóveis" if status_rt.get("module") == "imoveis" else "IPTU"
    current = status_rt.get("current", 0)
    total = status_rt.get("total", 1)
    item_atual = status_rt.get("current_item", "")

    st.info(f"⏳ **Extração de {modulo_nome} em andamento** — {current}/{total}")
    pct = current / total if total > 0 else 0
    st.progress(pct, text=f"Processando: {item_atual}")

    logs = status_rt.get("log", [])
    if logs:
        with st.expander("Ver log da extração", expanded=True):
            st.text("\n".join(logs[-20:]))

    time.sleep(2)
    st.rerun()

# Resultado do último processo
if st.session_state.ultimo_resultado == 'ok':
    modulo = st.session_state.ultimo_modulo or 'extração'
    st.success(f"✅ {modulo.capitalize()} concluída com sucesso! Atualize a tabela para ver os novos status.")
    st.session_state.ultimo_resultado = None
elif st.session_state.ultimo_resultado == 'erro':
    st.error("❌ A extração terminou com erro. Verifique o log acima.")
    st.session_state.ultimo_resultado = None

# ---------------------------------------------------------------------------
# Tabs principais
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Painel",
    "📋 Consultar",
    "🏢 Imóveis",
    "📂 Banco de Dados",
    "📥 Exportar",
])

# ===========================================================================
# TAB 1 — PAINEL
# ===========================================================================
with tab1:
    st.subheader("📊 Painel Geral")

    df_consultar = utils.ler_consultar()
    df_imoveis = utils.ler_link_imoveis()
    df_banco = utils.ler_banco_dados()

    # Métricas: Consultar
    st.markdown("#### Proprietários (CNPJ/CPF)")
    c1, c2, c3, c4 = st.columns(4)
    total_cnpj = len(df_consultar)
    finalizados = (df_consultar['Status'].str.strip() == 'Finalizado').sum() if not df_consultar.empty else 0
    erros = df_consultar['Status'].str.startswith('Erro', na=False).sum() if not df_consultar.empty else 0
    pendentes = total_cnpj - finalizados - erros

    c1.metric("Total cadastrados", total_cnpj)
    c2.metric("✅ Finalizados", int(finalizados))
    c3.metric("⏳ Pendentes", int(pendentes))
    c4.metric("❌ Com erro", int(erros))

    st.divider()

    # Métricas: Imóveis
    st.markdown("#### Imóveis")
    i1, i2, i3, i4 = st.columns(4)
    total_imoveis = len(df_imoveis) if not df_imoveis.empty else 0

    if not df_imoveis.empty and 'Extrair IPTU?' in df_imoveis.columns:
        iptu_extraido = (df_imoveis['Extrair IPTU?'].str.strip() == 'Sim').sum()
        iptu_erro = df_imoveis['Extrair IPTU?'].str.startswith('Erro', na=False).sum()
    else:
        iptu_extraido = 0
        iptu_erro = 0

    total_parcelas = len(df_banco) if not df_banco.empty else 0

    i1.metric("Total imóveis", total_imoveis)
    i2.metric("✅ IPTU extraído", int(iptu_extraido))
    i3.metric("❌ Erros IPTU", int(iptu_erro))
    i4.metric("📋 Parcelas no banco", total_parcelas)

    st.divider()

    # Distribuição de status
    if not df_consultar.empty:
        st.markdown("#### Distribuição de Status (Proprietários)")
        status_counts = df_consultar['Status'].fillna('Pendente').value_counts()
        st.bar_chart(status_counts)

# ===========================================================================
# TAB 2 — CONSULTAR (Etapa 1: Extrair Imóveis)
# ===========================================================================
with tab2:
    st.subheader("📋 Consultar — Extração de Imóveis")
    st.caption("Selecione os CNPJ/CPFs que deseja processar e clique em **Extrair Imóveis**.")

    df_cons = utils.ler_consultar()

    if df_cons.empty:
        st.warning("Nenhum dado encontrado na aba 'Consultar'. Verifique o arquivo Excel.")
    else:
        # Filtros
        col_f1, col_f2 = st.columns([2, 3])
        with col_f1:
            opcoes_status = ["Todos", "Pendente / Não processado", "Finalizado", "Em progresso", "Erro"]
            filtro_status = st.selectbox("Filtrar por status:", opcoes_status, key="cons_filtro_status")
        with col_f2:
            busca = st.text_input("Buscar por CNPJ/CPF:", key="cons_busca", placeholder="Ex: 50.136.653/0001-70")

        df_exib = df_cons.copy()

        # Aplica filtro de status
        if filtro_status == "Pendente / Não processado":
            df_exib = df_exib[df_exib['Status'].isna() | (df_exib['Status'].str.strip() == '')]
        elif filtro_status == "Finalizado":
            df_exib = df_exib[df_exib['Status'].str.strip() == 'Finalizado']
        elif filtro_status == "Em progresso":
            df_exib = df_exib[df_exib['Status'].str.strip() == 'Em progresso']
        elif filtro_status == "Erro":
            df_exib = df_exib[df_exib['Status'].str.startswith('Erro', na=False)]

        # Aplica busca
        if busca:
            df_exib = df_exib[df_exib['CNPJ/CPF'].str.contains(busca, case=False, na=False)]

        # Tabela com seleção
        cols_exibir = ['CNPJ/CPF', 'Tipo de Doc.', 'Status', 'Última Atualização']
        df_exib_display = df_exib[cols_exibir].copy()

        st.caption(f"{len(df_exib_display)} registro(s) exibido(s)")

        sel_event = st.dataframe(
            df_exib_display,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="multi-row",
            key="cons_tabela"
        )

        # Linhas selecionadas
        rows_sel = sel_event.selection.rows if sel_event.selection else []
        cnpjs_sel = df_exib_display.iloc[rows_sel]['CNPJ/CPF'].tolist() if rows_sel else []

        col_info, col_btn = st.columns([4, 1])
        with col_info:
            if cnpjs_sel:
                st.info(f"**{len(cnpjs_sel)}** CNPJ(s)/CPF(s) selecionado(s)")
            else:
                st.caption("Selecione linhas na tabela acima para habilitar a extração.")

        with col_btn:
            btn_disabled = len(cnpjs_sel) == 0 or processo_ativo
            if st.button("▶ Extrair Imóveis", disabled=btn_disabled, type="primary", key="btn_extrair_imoveis"):
                try:
                    utils.marcar_para_processar(cnpjs_sel)
                    proc = subprocess.Popen(
                        [sys.executable, "-m", "extracao_imoveis.main"],
                        cwd=utils.BASE_DIR
                    )
                    st.session_state.processo = proc
                    st.session_state.ultimo_modulo = "extração de imóveis"
                    st.session_state.ultimo_resultado = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao iniciar extração: {e}")

# ===========================================================================
# TAB 3 — IMÓVEIS (Etapa 2: Extrair IPTU)
# ===========================================================================
with tab3:
    st.subheader("🏢 Imóveis — Extração de IPTU")
    st.caption("Selecione os imóveis para extrair o carnê de IPTU e clique em **Extrair IPTU**.")

    df_imov = utils.ler_link_imoveis()

    if df_imov.empty:
        st.info("Nenhum imóvel encontrado. Execute primeiro a **Etapa 1** na aba 'Consultar'.")
    else:
        # Filtros
        col_f1, col_f2, col_f3 = st.columns([2, 2, 3])
        with col_f1:
            opts_iptu = ["Todos", "Não extraído", "Extraído (Sim)", "Erro"]
            filtro_iptu = st.selectbox("Status IPTU:", opts_iptu, key="imov_filtro_iptu")
        with col_f2:
            cnpjs_disponiveis = ["Todos"] + sorted(df_imov['CNPJ/CPF'].dropna().unique().tolist())
            filtro_cnpj = st.selectbox("Filtrar por CNPJ/CPF:", cnpjs_disponiveis, key="imov_filtro_cnpj")
        with col_f3:
            busca_imov = st.text_input("Buscar por código ou inscrição:", key="imov_busca", placeholder="Ex: 1247")

        df_imov_exib = df_imov.copy()

        # Aplica filtro de IPTU
        if 'Extrair IPTU?' in df_imov_exib.columns:
            if filtro_iptu == "Não extraído":
                df_imov_exib = df_imov_exib[
                    df_imov_exib['Extrair IPTU?'].isna()
                    | ~df_imov_exib['Extrair IPTU?'].isin(['Sim', 'Erro de Processamento'])
                ]
            elif filtro_iptu == "Extraído (Sim)":
                df_imov_exib = df_imov_exib[df_imov_exib['Extrair IPTU?'].str.strip() == 'Sim']
            elif filtro_iptu == "Erro":
                df_imov_exib = df_imov_exib[df_imov_exib['Extrair IPTU?'].str.startswith('Erro', na=False)]

        # Filtro por CNPJ
        if filtro_cnpj != "Todos":
            df_imov_exib = df_imov_exib[df_imov_exib['CNPJ/CPF'] == filtro_cnpj]

        # Busca
        if busca_imov:
            mask = (
                df_imov_exib['Código do Imóvel'].str.contains(busca_imov, case=False, na=False)
                | df_imov_exib.get('Inscrição Imobiliária', pd.Series(dtype=str)).str.contains(busca_imov, case=False, na=False)
            )
            df_imov_exib = df_imov_exib[mask]

        # Colunas relevantes para exibição
        cols_imov = ['Código do Imóvel', 'Inscrição Imobiliária', 'Logradouro', 'Bairro',
                     'CNPJ/CPF', 'Situação', 'Extrair IPTU?']
        cols_imov = [c for c in cols_imov if c in df_imov_exib.columns]
        df_imov_display = df_imov_exib[cols_imov].copy()

        st.caption(f"{len(df_imov_display)} imóvel(is) exibido(s)")

        # Botão de seleção rápida
        col_sel_rapida, _ = st.columns([2, 6])
        with col_sel_rapida:
            st.caption("💡 Selecione as linhas na tabela abaixo")

        sel_imov_event = st.dataframe(
            df_imov_display,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="multi-row",
            key="imov_tabela"
        )

        rows_imov_sel = sel_imov_event.selection.rows if sel_imov_event.selection else []
        codigos_sel = df_imov_display.iloc[rows_imov_sel]['Código do Imóvel'].tolist() if rows_imov_sel else []

        col_info_imov, col_btn_imov = st.columns([4, 1])
        with col_info_imov:
            if codigos_sel:
                st.info(f"**{len(codigos_sel)}** imóvel(is) selecionado(s)")
            else:
                st.caption("Selecione imóveis na tabela para habilitar a extração de IPTU.")

        with col_btn_imov:
            btn_iptu_disabled = len(codigos_sel) == 0 or processo_ativo
            if st.button("▶ Extrair IPTU", disabled=btn_iptu_disabled, type="primary", key="btn_extrair_iptu"):
                try:
                    utils.marcar_para_extrair_iptu(codigos_sel)
                    proc = subprocess.Popen(
                        [sys.executable, "-m", "extracao_iptu.main"],
                        cwd=utils.BASE_DIR
                    )
                    st.session_state.processo = proc
                    st.session_state.ultimo_modulo = "extração de IPTU"
                    st.session_state.ultimo_resultado = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao iniciar extração de IPTU: {e}")

# ===========================================================================
# TAB 4 — BANCO DE DADOS
# ===========================================================================
with tab4:
    st.subheader("📂 Banco de Dados — IPTU Extraído")

    df_bd = utils.ler_banco_dados()

    if df_bd.empty:
        st.info("Nenhum dado de IPTU extraído ainda. Execute a Etapa 2 na aba 'Imóveis'.")
    else:
        cols_bd = df_bd.columns.tolist()

        # Filtros rápidos
        col_bd1, col_bd2, col_bd3 = st.columns(3)
        with col_bd1:
            # Tenta encontrar coluna de tipo de parcela (índice K ou similar)
            col_tipo = cols_bd[10] if len(cols_bd) > 10 else None
            if col_tipo:
                tipos_disponiveis = ["Todos"] + sorted(df_bd[col_tipo].dropna().unique().tolist())
                filtro_tipo = st.selectbox(f"Tipo de parcela ({col_tipo}):", tipos_disponiveis, key="bd_filtro_tipo")
            else:
                filtro_tipo = "Todos"

        with col_bd2:
            col_ano = cols_bd[2] if len(cols_bd) > 2 else None
            if col_ano:
                anos_disponiveis = ["Todos"] + sorted(df_bd[col_ano].dropna().unique().tolist(), reverse=True)
                filtro_ano = st.selectbox(f"Ano ({col_ano}):", anos_disponiveis, key="bd_filtro_ano")
            else:
                filtro_ano = "Todos"

        with col_bd3:
            busca_inscricao = st.text_input("Buscar por inscrição/código:", key="bd_busca")

        df_bd_exib = df_bd.copy()

        if filtro_tipo != "Todos" and col_tipo:
            df_bd_exib = df_bd_exib[df_bd_exib[col_tipo] == filtro_tipo]

        if filtro_ano != "Todos" and col_ano:
            df_bd_exib = df_bd_exib[df_bd_exib[col_ano] == filtro_ano]

        if busca_inscricao:
            mask_bd = df_bd_exib.apply(
                lambda row: row.astype(str).str.contains(busca_inscricao, case=False, na=False).any(),
                axis=1
            )
            df_bd_exib = df_bd_exib[mask_bd]

        st.caption(f"{len(df_bd_exib)} registro(s) exibido(s) de {len(df_bd)} total")
        st.dataframe(df_bd_exib, use_container_width=True, hide_index=True)

# ===========================================================================
# TAB 5 — EXPORTAR
# ===========================================================================
with tab5:
    st.subheader("📥 Exportar Dados")

    df_export_bd = utils.ler_banco_dados()
    df_export_imov = utils.ler_link_imoveis()

    st.markdown("#### 1. Planilha Completa de Imóveis")
    st.caption("Exporta a aba 'Link de Imóveis' com todos os dados extraídos.")

    if not df_export_imov.empty:
        excel_imov = utils.gerar_export_excel(df_export_imov)
        st.download_button(
            label="⬇ Baixar Imóveis (.xlsx)",
            data=excel_imov,
            file_name="metis_imoveis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_imoveis"
        )
    else:
        st.info("Nenhum dado de imóveis para exportar.")

    st.divider()

    st.markdown("#### 2. Banco de Dados IPTU")
    st.caption("Exporta todos os carnês IPTU extraídos.")

    if not df_export_bd.empty:
        col_exp1, col_exp2 = st.columns(2)

        with col_exp1:
            excel_bd = utils.gerar_export_excel(df_export_bd)
            st.download_button(
                label="⬇ Baixar Banco de Dados (.xlsx)",
                data=excel_bd,
                file_name="metis_banco_dados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_banco_xlsx"
            )

        with col_exp2:
            csv_importacao = utils.gerar_export_csv_importacao(df_export_bd)
            st.download_button(
                label="⬇ Baixar CSV de Importação (.csv)",
                data=csv_importacao,
                file_name="metis_importacao.csv",
                mime="text/csv",
                key="dl_banco_csv"
            )

        st.caption("O arquivo CSV de importação segue o formato padrão de importação da imobiliária (separador: `;`).")
    else:
        st.info("Nenhum dado de IPTU para exportar. Execute a extração primeiro.")

    st.divider()

    st.markdown("#### 3. Preview dos dados para exportação")
    preview_opcao = st.radio(
        "Visualizar:",
        ["Imóveis", "Banco de Dados IPTU"],
        horizontal=True,
        key="preview_opcao"
    )

    if preview_opcao == "Imóveis":
        st.dataframe(df_export_imov.head(50), use_container_width=True, hide_index=True)
        if len(df_export_imov) > 50:
            st.caption(f"Mostrando 50 de {len(df_export_imov)} registros.")
    else:
        st.dataframe(df_export_bd.head(50), use_container_width=True, hide_index=True)
        if len(df_export_bd) > 50:
            st.caption(f"Mostrando 50 de {len(df_export_bd)} registros.")
