import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Performance Financeira ConectSol",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Verifica se o arquivo de dados existe na pasta antes de prosseguir
if not os.path.exists("dados_conectsol.xlsx"):
    st.error("⚠️ O arquivo 'dados_conectsol.xlsx' não foi encontrado na pasta raiz.")
    st.stop()

# 2. FUNÇÕES DE FORMATAÇÃO (PADRÃO FINANCEIRO BRL E GRÁFICOS)
def formatar_brl(valor, mostrar_sinal=False):
    if pd.isna(valor) or valor is None:
        return "R$ 0,00"
    sinal = "+" if mostrar_sinal and valor > 0 else ""
    if valor < 0:
        return f"(R$ {abs(valor):,.2f})".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{sinal}R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_pct(valor):
    if pd.isna(valor) or valor is None:
        return "-"
    return f"{valor:+.1f}%".replace(".", ",")

def resumir_valor_grafico(v):
    if pd.isna(v) or v == 0:
        return ""
    if abs(v) >= 1_000_000:
        return f"{v/1_000_000:.1f}M".replace('.', ',')
    if abs(v) >= 1_000:
        return f"{v/1_000:.0f}K"
    return f"{v:.0f}"

# 3. CARREGAMENTO E RENOMEAÇÃO ROBUSTA DE COLUNAS DUPLICADAS
@st.cache_data
def carregar_dados():
    df = pd.read_excel("dados_conectsol.xlsx", sheet_name="DADOS")
    
    # Tratamento seguro para colunas com nomes idênticos ("Tipo")
    novas_colunas = []
    contador_tipo = 0
    for col in df.columns:
        if str(col).startswith('Tipo'):
            if contador_tipo == 0:
                novas_colunas.append('Tipo_Movimentacao') # Coluna de Entrada / Saída
                contador_tipo += 1
            else:
                novas_colunas.append('Tipo_Classificacao') # Coluna de VENDA / CUSTO / DESPESA
        else:
            novas_colunas.append(col)
    df.columns = novas_colunas
    
    df = df.dropna(subset=['Ano', 'Mês'])
    df['Mês'] = df['Mês'].astype(int)
    df['Ano'] = df['Ano'].astype(int)
    return df

df_raw = carregar_dados()

# 4. CONSTRUÇÃO DO FILTRO DINÂMICO DE DATAS
meses_pt = {1: 'jan', 2: 'fev', 3: 'mar', 4: 'abr', 5: 'mai', 6: 'jun',
            7: 'jul', 8: 'ago', 9: 'set', 10: 'out', 11: 'nov', 12: 'dez'}
meses_list_abrev = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']

# Agrupa e ordena cronologicamente os períodos disponíveis
periodos_unicos = df_raw[['Ano', 'Mês']].drop_duplicates().sort_values(by=['Ano', 'Mês'])
opcoes_filtro = [f"{meses_pt[row['Mês']]}/{row['Ano']}" for _, row in periodos_unicos.iterrows()]

# 5. BARRA LATERAL (SIDEBAR) COM SEU LOGO NO TOPO
if os.path.exists("Logohorizontal.png"):
    st.sidebar.image("Logohorizontal.png", use_container_width=True)
else:
    st.sidebar.markdown("### 🌐 WL EXPERTISE")

st.sidebar.markdown("---")

paginas = {
    "🚀 Visão Geral (YTD)": "visao_geral",
    "📈 Análise de Entradas": "entradas",
    "📉 Análise de Saídas": "saidas",
    "👥 Gestão de Sócios": "socios",
    "🛠️ Custos na Prestação de Serviço": "custos"
}
selecao_pagina = st.sidebar.radio("Selecione a tela:", list(paginas.keys()))

st.sidebar.markdown("---")
st.sidebar.markdown("**Mês de Referência:**")
mes_selecionado_str = st.sidebar.selectbox("Mês:", opcoes_filtro, index=len(opcoes_filtro)-1, label_visibility="collapsed")

st.sidebar.markdown("<br><br><br>", unsafe_allow_html=True)

# Decodifica a string do filtro em variáveis inteiras
mes_ref_str, ano_ref_str = mes_selecionado_str.split('/')
ano_atual = int(ano_ref_str)
mes_atual = [k for k, v in meses_pt.items() if v == mes_ref_str][0]

# 6. PROCESSAMENTO RESTRITO DAS REGRAS DE NEGÓCIO
# Saídas: Tudo da coluna de movimentação exceto o grupo TRANSFERÊNCIAS
df_saidas_validas = df_raw[df_raw['Grupo'] != 'TRANSFERÊNCIAS']

# Entradas: Apenas o que for "VENDA" na coluna de classificação
df_entradas_validas = df_raw[(df_raw['Tipo_Movimentacao'] == 'Entrada') & (df_raw['Tipo_Classificacao'] == 'VENDA')]

# Recortes Mensais Gerais
df_mes_entradas = df_entradas_validas[(df_entradas_validas['Ano'] == ano_atual) & (df_entradas_validas['Mês'] == mes_atual)]
df_mes_saidas = df_saidas_validas[(df_saidas_validas['Tipo_Movimentacao'] == 'Saída') & (df_saidas_validas['Ano'] == ano_atual) & (df_saidas_validas['Mês'] == mes_atual)]

entradas_mes = df_mes_entradas['Valor'].sum()
saidas_mes = df_mes_saidas['Valor'].sum()
resultado_mes = entradas_mes - saidas_mes
margem_mes = (resultado_mes / entradas_mes * 100) if entradas_mes > 0 else 0

# Recortes Acumulados Gerais (YTD)
df_ytd_entradas = df_entradas_validas[(df_entradas_validas['Ano'] == ano_atual) & (df_entradas_validas['Mês'] <= mes_atual)]
df_ytd_saidas = df_saidas_validas[(df_saidas_validas['Tipo_Movimentacao'] == 'Saída') & (df_saidas_validas['Ano'] == ano_atual) & (df_saidas_validas['Mês'] <= mes_atual)]

entradas_ytd = df_ytd_entradas['Valor'].sum()
saidas_ytd = df_ytd_saidas['Valor'].sum()
resultado_ytd = entradas_ytd - saidas_ytd
margem_ytd = (resultado_ytd / entradas_ytd * 100) if entradas_ytd > 0 else 0


# 7. FUNÇÕES GLOBAIS DE CABEÇALHO E VISUALIZAÇÃO DE INFORMAÇÕES
def renderizar_cabecalho_pagina(titulo, subtitulo):
    col_tit, col_log = st.columns([5, 1])
    with col_tit:
        st.title(titulo)
        if subtitulo:
            st.subheader(subtitulo)
    with col_log:
        if os.path.exists("conectlogo.png"):
            st.image("conectlogo.png", use_container_width=True)
    st.markdown("---")

def exibir_painel_cards_globais(compacto=False):
    if not compacto:
        st.markdown(f"#### 📅 Resumo Operacional do Mês ({mes_selecionado_str})")
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Entradas (Vendas)", formatar_brl(entradas_mes))
        c2.metric("💸 Saídas Operacionais", formatar_brl(saidas_mes))
        delta_mes_str = f"{margem_mes:+.1f}% Margem".replace('.', ',')
        c3.metric("📊 Resultado Líquido", formatar_brl(resultado_mes), delta=delta_mes_str)
        
        st.markdown("#### 🗂️ Resumo Acumulado do Ano (YTD)")
        cc1, cc2, cc3 = st.columns(3)
        cc1.metric("📈 Entradas Acumuladas", formatar_brl(entradas_ytd))
        cc2.metric("📉 Saídas Acumuladas", formatar_brl(saidas_ytd))
        delta_ytd_str = f"{margem_ytd:+.1f}% Margem".replace('.', ',')
        cc3.metric("⚖️ Resultado Líquido YTD", formatar_brl(resultado_ytd), delta=delta_ytd_str)
        st.markdown("---")
    else:
        cor_m = "#155724" if resultado_mes >= 0 else "#721c24"
        cor_y = "#155724" if resultado_ytd >= 0 else "#721c24"
        st.markdown(
            f"""
            <div style="background-color: #f8f9fa; padding: 10px 15px; border-radius: 6px; border-left: 4px solid #005a60; margin-bottom: 20px; font-size: 0.88rem; line-height: 1.4;">
                <b>📅 MÊS ({mes_selecionado_str.upper()}):</b> Entradas: {formatar_brl(entradas_mes)} | Saídas: {formatar_brl(saidas_mes)} | Líquido: <b>{formatar_brl(resultado_mes)}</b> <span style="color:{cor_m}; font-weight:bold;">({margem_mes:+.1f}%)</span>
                <br>
                <b>🗂️ ACUMULADO (YTD):</b> Entradas: {formatar_brl(entradas_ytd)} | Saídas: {formatar_brl(saidas_ytd)} | Líquido: <b>{formatar_brl(resultado_ytd)}</b> <span style="color:{cor_y}; font-weight:bold;">({margem_ytd:+.1f}%)</span>
            </div>
            """,
            unsafe_allow_html=True
        )

def construir_tabela_comparativa_df(df_filtrado):
    pivot = df_filtrado.pivot_table(index='Mês', columns='Ano', values='Valor', aggfunc='sum').reset_index()
    all_months = pd.DataFrame({'Mês': range(1, 13)})
    pivot = pd.merge(all_months, pivot, on='Mês', how='left')
    if 2025 not in pivot.columns: pivot[2025] = np.nan
    if 2026 not in pivot.columns: pivot[2026] = np.nan
    pivot['Mês / Referência'] = pivot['Mês'].map(lambda x: meses_list_abrev[x-1])
    return pivot.rename(columns={2025: 'Realizado 2025', 2026: 'Realizado 2026'})

def construir_tabela_comparativa(grupo_nome, contato_filtro=None):
    df_grupo = df_raw[df_raw['Grupo'] == grupo_nome]
    if contato_filtro and contato_filtro != "Todos os Sócios (Geral)":
        df_grupo = df_grupo[df_grupo['Contato'] == contato_filtro]
    return construir_tabela_comparativa_df(df_grupo)


# ==========================================
# TELA 1: VISÃO GERAL
# ==========================================
if paginas[selecao_pagina] == "visao_geral":
    renderizar_cabecalho_pagina("Performance Financeira ConectSol", f"Acumulado Estratégico (YTD) até {mes_selecionado_str.upper()}")
    exibir_painel_cards_globais(compacto=False)
    
    st.markdown("#### 📊 Histórico e Evolução do Resultado Líquido")
    
    df_ent_comp = construir_tabela_comparativa_df(df_entradas_validas)
    df_sai_comp = construir_tabela_comparativa_df(df_saidas_validas[df_saidas_validas['Tipo_Movimentacao'] == 'Saída'])
    
    df_liq_comp = pd.DataFrame({
        'Mês': range(1, 13),
        'Mês / Referência': meses_list_abrev,
        'Realizado 2025': df_ent_comp['Realizado 2025'].fillna(0) - df_sai_comp['Realizado 2025'].fillna(0),
        'Realizado 2026': df_ent_comp['Realizado 2026'].fillna(0) - df_sai_comp['Realizado 2026'].fillna(0)
    })
    
    df_liq_comp.loc[df_liq_comp['Mês'] > mes_atual, 'Realizado 2026'] = np.nan
    
    labels_liq_2025 = df_liq_comp['Realizado 2025'].apply(resumir_valor_grafico)
    labels_liq_2026 = df_liq_comp['Realizado 2026'].apply(resumir_valor_grafico)
    
    col_gv1, col_gv2 = st.columns([2, 1])
    with col_gv1:
        fig_bar_l = go.Figure()
        fig_bar_l.add_trace(go.Bar(
            x=df_liq_comp['Mês / Referência'], y=df_liq_comp['Realizado 2025'], name='2025', 
            marker_color='#a3d9c9', text=labels_liq_2025, textposition='outside'
        ))
        fig_bar_l.add_trace(go.Bar(
            x=df_liq_comp['Mês / Referência'], y=df_liq_comp['Realizado 2026'], name='2026', 
            marker_color='#006d4e', text=labels_liq_2026, textposition='outside'
        ))
        fig_bar_l.update_layout(title="Resultado Líquido Mensal (Ano x Ano)", barmode='group', height=370, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_bar_l, use_container_width=True)
        
    with col_gv2:
        ent_ytd_2025 = df_entradas_validas[(df_entradas_validas['Ano'] == 2025) & (df_entradas_validas['Mês'] <= mes_atual)]['Valor'].sum()
        sai_ytd_2025 = df_saidas_validas[(df_saidas_validas['Tipo_Movimentacao'] == 'Saída') & (df_saidas_validas['Ano'] == 2025) & (df_saidas_validas['Mês'] <= mes_atual)]['Valor'].sum()
        res_ytd_2025 = ent_ytd_2025 - sai_ytd_2025

        ent_ytd_2026 = df_entradas_validas[(df_entradas_validas['Ano'] == 2026) & (df_entradas_validas['Mês'] <= mes_atual)]['Valor'].sum()
        sai_ytd_2026 = df_saidas_validas[(df_saidas_validas['Tipo_Movimentacao'] == 'Saída') & (df_saidas_validas['Ano'] == 2026) & (df_saidas_validas['Mês'] <= mes_atual)]['Valor'].sum()
        res_ytd_2026 = ent_ytd_2026 - sai_ytd_2026
        
        fig_bar_ytd = go.Figure()
        fig_bar_ytd.add_trace(go.Bar(
            x=['Lucro YTD'], y=[res_ytd_2025], name='2025', 
            marker_color='#a3d9c9', text=[resumir_valor_grafico(res_ytd_2025)], textposition='outside'
        ))
        fig_bar_ytd.add_trace(go.Bar(
            x=['Lucro YTD'], y=[res_ytd_2026], name='2026', 
            marker_color='#006d4e', text=[resumir_valor_grafico(res_ytd_2026)], textposition='outside'
        ))
        fig_bar_ytd.update_layout(title="Comparativo do Lucro Acumulado (YTD)", barmode='group', height=370, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_bar_ytd, use_container_width=True)
        
    st.markdown("---")


# ==========================================
# TELA 2: ANÁLISE DE ENTRADAS
# ==========================================
elif paginas[selecao_pagina] == "entradas":
    renderizar_cabecalho_pagina("📈 Análise de Entradas", f"Detalhamento de Recebimentos (Vendas) — Referência {mes_selecionado_str.upper()}")
    exibir_painel_cards_globais(compacto=True)
    
    st.markdown(f"#### 💰 Destaques de Recebimentos ({mes_selecionado_str})")
    col_ent1, col_ent2 = st.columns(2)
    col_ent1.metric("💰 Total de Entradas no Mês", formatar_brl(entradas_mes))
    col_ent2.metric("📅 Entradas Acumuladas no Ano (YTD)", formatar_brl(entradas_ytd))
    st.markdown("---")
    
    st.markdown("#### 📊 Histórico e Evolução das Entradas")
    df_entradas_comp = construir_tabela_comparativa_df(df_entradas_validas)
    labels_entradas_2025 = df_entradas_comp['Realizado 2025'].apply(resumir_valor_grafico)
    labels_entradas_2026 = df_entradas_comp['Realizado 2026'].apply(resumir_valor_grafico)
    
    col_ge1, col_ge2 = st.columns([2, 1])
    with col_ge1:
        fig_bar_e = go.Figure()
        fig_bar_e.add_trace(go.Bar(
            x=df_entradas_comp['Mês / Referência'], y=df_entradas_comp['Realizado 2025'], name='2025', 
            marker_color='#9fb1c2', text=labels_entradas_2025, textposition='outside'
        ))
        fig_bar_e.add_trace(go.Bar(
            x=df_entradas_comp['Mês / Referência'], y=df_entradas_comp['Realizado 2026'], name='2026', 
            marker_color='#005a60', text=labels_entradas_2026, textposition='outside'
        ))
        fig_bar_e.update_layout(title="Comparativo Mensal de Recebidos (Ano x Ano)", barmode='group', height=370, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_bar_e, use_container_width=True)
        
    with col_ge2:
        ytd_ent_2025 = df_entradas_validas[(df_entradas_validas['Ano'] == 2025) & (df_entradas_validas['Mês'] <= mes_atual)]['Valor'].sum()
        ytd_ent_2026 = df_entradas_validas[(df_entradas_validas['Ano'] == 2026) & (df_entradas_validas['Mês'] <= mes_atual)]['Valor'].sum()
        fig_pie_e = go.Figure(data=[go.Pie(
            labels=['Acumulado 2025', 'Acumulado 2026'], values=[ytd_ent_2025, ytd_ent_2026], 
            hole=.5, marker=dict(colors=['#9fb1c2', '#005a60']), textinfo='percent+value', textposition='inside'
        )])
        fig_pie_e.update_layout(title=f"Recebimentos Acumulados (Até {meses_list_abrev[mes_atual-1]})", height=370, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_pie_e, use_container_width=True)
        
    st.markdown("---")
    
    st.markdown("#### 🔍 Listagem Analítica de Vendas do Mês")
    colunas_foco = ['Data de pagamento', 'Contato', 'Descrição', 'Categoria', 'Situação', 'Valor', 'Instituição']
    colunas_existentes = [c for c in colunas_foco if c in df_mes_entradas.columns]
    df_exibicao = df_mes_entradas[colunas_existentes].copy()
    
    if not df_exibicao.empty:
        if 'Data de pagamento' in df_exibicao.columns:
            df_exibicao['Data de pagamento'] = pd.to_datetime(df_exibicao['Data de pagamento']).dt.strftime('%d/%m/%Y')
        df_exibicao['Valor'] = df_exibicao['Valor'].apply(lambda x: formatar_brl(x))
        st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
    else:
        st.info(f"Nenhum lançamento de Venda encontrado para o período {mes_selecionado_str}.")
    
    st.markdown("---")
    
    st.markdown("#### 📋 Tabela de Evolução Analítica de Entradas")
    df_entradas_comp['Diferença Absoluta'] = df_entradas_comp['Realizado 2026'] - df_entradas_comp['Realizado 2025']
    df_entradas_comp['Variação %'] = (df_entradas_comp['Diferença Absoluta'] / df_entradas_comp['Realizado 2025']) * 100
    
    df_entradas_show = df_entradas_comp.copy()
    df_entradas_show['Realizado 2025'] = df_entradas_show['Realizado 2025'].apply(lambda x: formatar_brl(x))
    df_entradas_show['Realizado 2026'] = df_entradas_show['Realizado 2026'].apply(lambda x: formatar_brl(x))
    df_entradas_show['Diferença Absoluta'] = df_entradas_show['Diferença Absoluta'].apply(lambda x: formatar_brl(x, mostrar_sinal=True))
    df_entradas_show['Variação %'] = df_entradas_show['Variação %'].apply(lambda x: formatar_pct(x))
    st.dataframe(df_entradas_show[['Mês / Referência', 'Realizado 2025', 'Realizado 2026', 'Diferença Absoluta', 'Variação %']], use_container_width=True, hide_index=True)


# ==========================================
# TELA 3: ANÁLISE DE SAÍDAS
# ==========================================
elif paginas[selecao_pagina] == "saidas":
    renderizar_cabecalho_pagina("📉 Análise de Saídas", f"Detalhamento de Saídas Operacionais — Referência {mes_selecionado_str.upper()}")
    exibir_painel_cards_globais(compacto=True)
    
    st.markdown(f"#### 💸 Destaques de Despesas e Saídas ({mes_selecionado_str})")
    col_sai1, col_sai2 = st.columns(2)
    col_sai1.metric("💸 Total de Saídas no Mês", formatar_brl(saidas_mes))
    col_sai2.metric("📅 Saídas Acumuladas no Ano (YTD)", formatar_brl(saidas_ytd))
    st.markdown("---")
    
    st.markdown("#### 📊 Histórico e Evolução das Saídas")
    df_saidas_analise = df_raw[(df_raw['Tipo_Movimentacao'] == 'Saída') & (df_raw['Grupo'] != 'TRANSFERÊNCIAS')]
    df_saidas_comp = construir_tabela_comparativa_df(df_saidas_analise)
    labels_saidas_2025 = df_saidas_comp['Realizado 2025'].apply(resumir_valor_grafico)
    labels_saidas_2026 = df_saidas_comp['Realizado 2026'].apply(resumir_valor_grafico)
    
    col_gs1, col_gs2 = st.columns([2, 1])
    with col_gs1:
        fig_bar_s = go.Figure()
        fig_bar_s.add_trace(go.Bar(
            x=df_saidas_comp['Mês / Referência'], y=df_saidas_comp['Realizado 2025'], name='2025', 
            marker_color='#ff9999', text=labels_saidas_2025, textposition='outside'
        ))
        fig_bar_s.add_trace(go.Bar(
            x=df_saidas_comp['Mês / Referência'], y=df_saidas_comp['Realizado 2026'], name='2026', 
            marker_color='#17a2b8', text=labels_saidas_2026, textposition='outside'
        ))
        fig_bar_s.update_layout(title="Comparativo Mensal de Saídas (Ano x Ano)", barmode='group', height=370, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_bar_s, use_container_width=True)
        
    with col_gs2:
        ytd_sai_2025 = df_saidas_analise[(df_saidas_analise['Ano'] == 2025) & (df_saidas_analise['Mês'] <= mes_atual)]['Valor'].sum()
        ytd_sai_2026 = df_saidas_analise[(df_saidas_analise['Ano'] == 2026) & (df_saidas_analise['Mês'] <= mes_atual)]['Valor'].sum()
        fig_pie_s = go.Figure(data=[go.Pie(
            labels=['Acumulado 2025', 'Acumulado 2026'], values=[ytd_sai_2025, ytd_sai_2026], 
            hole=.5, marker=dict(colors=['#ff9999', '#17a2b8']), textinfo='percent+value', textposition='inside'
        )])
        fig_pie_s.update_layout(title=f"Saídas Acumuladas (Até {meses_list_abrev[mes_atual-1]})", height=370, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_pie_s, use_container_width=True)
        
    st.markdown("---")
    
    st.markdown("#### 🔍 Listagem Analítica de Saídas do Mês")
    colunas_foco = ['Data de pagamento', 'Contato', 'Descrição', 'Categoria', 'Situação', 'Valor', 'Instituição']
    colunas_existentes = [c for c in colunas_foco if c in df_mes_saidas.columns]
    df_exibicao_saidas = df_mes_saidas[colunas_existentes].copy()
    
    if not df_exibicao_saidas.empty:
        if 'Data de pagamento' in df_exibicao_saidas.columns:
            df_exibicao_saidas['Data de pagamento'] = pd.to_datetime(df_exibicao_saidas['Data de pagamento']).dt.strftime('%d/%m/%Y')
        df_exibicao_saidas['Valor'] = df_exibicao_saidas['Valor'].apply(lambda x: formatar_brl(x))
        st.dataframe(df_exibicao_saidas, use_container_width=True, hide_index=True)
    else:
        st.info(f"Nenhum lançamento de Saída encontrado para o período {mes_selecionado_str}.")
        
    st.markdown("---")
    
    st.markdown("#### 📋 Tabela de Evolução Analítica de Saídas")
    df_saidas_comp['Diferença Absoluta'] = df_saidas_comp['Realizado 2026'] - df_saidas_comp['Realizado 2025']
    df_saidas_comp['Variação %'] = (df_saidas_comp['Diferença Absoluta'] / df_saidas_comp['Realizado 2025']) * 100
    
    df_saidas_show = df_saidas_comp.copy()
    df_saidas_show['Realizado 2025'] = df_saidas_show['Realizado 2025'].apply(lambda x: formatar_brl(x))
    df_saidas_show['Realizado 2026'] = df_saidas_show['Realizado 2026'].apply(lambda x: formatar_brl(x))
    df_saidas_show['Diferença Absoluta'] = df_saidas_show['Diferença Absoluta'].apply(lambda x: formatar_brl(x, mostrar_sinal=True))
    df_saidas_show['Variação %'] = df_saidas_show['Variação %'].apply(lambda x: formatar_pct(x))
    st.dataframe(df_saidas_show[['Mês / Referência', 'Realizado 2025', 'Realizado 2026', 'Diferença Absoluta', 'Variação %']], use_container_width=True, hide_index=True)


# ==========================================
# TELA 4: GESTÃO DE SÓCIOS
# ==========================================
elif paginas[selecao_pagina] == "socios":
    renderizar_cabecalho_pagina("Gestão de Sócios", f"Retiradas Mensais — Consolidação e Detalhamento ({mes_selecionado_str.upper()})")
    exibir_painel_cards_globais(compacto=True)
    
    st.markdown("#### 👥 Seleção do Sócio para Análise")
    lista_socios = sorted(list(df_raw[df_raw['Grupo'] == 'DESPESAS DOS SÓCIOS']['Contato'].dropna().unique()))
    socio_selecionado = st.selectbox("Escolha uma opção para recalcular a página:", ["Todos os Sócios (Geral)"] + lista_socios)
    st.markdown("---")
    
    df_socios = construir_tabela_comparativa('DESPESAS DOS SÓCIOS', contato_filtro=socio_selecionado)
    labels_2025 = df_socios['Realizado 2025'].apply(resumir_valor_grafico)
    labels_2026 = df_socios['Realizado 2026'].apply(resumir_valor_grafico)
    
    col_graf1, col_graf2 = st.columns([2, 1])
    with col_graf1:
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=df_socios['Mês / Referência'], y=df_socios['Realizado 2025'], name='2025', 
            marker_color='#9fb1c2', text=labels_2025, textposition='outside'
        ))
        fig_bar.add_trace(go.Bar(
            x=df_socios['Mês / Referência'], y=df_socios['Realizado 2026'], name='2026', 
            marker_color='#005a60', text=labels_2026, textposition='outside'
        ))
        fig_bar.update_layout(title=f"Comparativo Mensal de Retiradas — {socio_selecionado}", barmode='group', height=370, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col_graf2:
        df_socios_filtrado = df_raw[df_raw['Grupo'] == 'DESPESAS DOS SÓCIOS']
        if socio_selecionado != "Todos os Sócios (Geral)":
            df_socios_filtrado = df_socios_filtrado[df_socios_filtrado['Contato'] == socio_selecionado]
            
        ytd_socios_2025 = df_socios_filtrado[(df_socios_filtrado['Ano'] == 2025) & (df_socios_filtrado['Mês'] <= mes_atual)]['Valor'].sum()
        ytd_socios_2026 = df_socios_filtrado[(df_socios_filtrado['Ano'] == 2026) & (df_socios_filtrado['Mês'] <= mes_atual)]['Valor'].sum()
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=['Acumulado 2025', 'Acumulado 2026'], values=[ytd_socios_2025, ytd_socios_2026], 
            hole=.5, marker=dict(colors=['#9fb1c2', '#005a60']), textinfo='percent+value', textposition='inside'
        )])
        fig_pie.update_layout(title=f"Acumulado Retiradas (Até {meses_list_abrev[mes_atual-1]})", height=370, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_pie, use_container_width=True)
        
    st.markdown("---")
    
    if socio_selecionado == "Todos os Sócios (Geral)":
        st.markdown(f"#### 📊 Resumo de Participação por Sócio no Mês ({mes_selecionado_str})")
        df_mes_socios_breakdown = df_raw[(df_raw['Grupo'] == 'DESPESAS DOS SÓCIOS') & (df_raw['Ano'] == ano_atual) & (df_raw['Mês'] == mes_atual)]
        
        if not df_mes_socios_breakdown.empty:
            df_bdown = df_mes_socios_breakdown.groupby('Contato')['Valor'].sum().reset_index().sort_values(by='Valor', ascending=False)
            df_bdown['Participação %'] = (df_bdown['Valor'] / df_bdown['Valor'].sum() * 100)
            df_bdown['Valor'] = df_bdown['Valor'].apply(lambda x: formatar_brl(x))
            df_bdown['Participação %'] = df_bdown['Participação %'].apply(lambda x: f"{x:.1f}%".replace('.', ','))
            st.dataframe(df_bdown, use_container_width=True, hide_index=True)
        else:
            st.info(f"Nenhum lançamento encontrado para gerar o resumo de participação em {mes_selecionado_str}.")
        st.markdown("---")
    
    st.markdown(f"#### 📋 Detalhamento de Gastos do Mês ({mes_selecionado_str}) — {socio_selecionado}")
    # FIX: Correção de digitacao de DESPADAS para DESPESAS abaixo
    df_detalhe_mes = df_raw[(df_raw['Grupo'] == 'DESPESAS DOS SÓCIOS') & (df_raw['Ano'] == ano_atual) & (df_raw['Mês'] == mes_atual)].copy()
    
    if socio_selecionado != "Todos os Sócios (Geral)":
        df_detalhe_mes = df_detalhe_mes[df_detalhe_mes['Contato'] == socio_selecionado]
        
    if not df_detalhe_mes.empty:
        colunas_pedidas = ['Data de pagamento', 'Contato', 'Valor', 'Descrição']
        colunas_disponiveis = [col for col in colunas_pedidas if col in df_detalhe_mes.columns]
        df_detalhe_show = df_detalhe_mes[colunas_disponiveis].copy()
        
        if 'Data de pagamento' in df_detalhe_show.columns:
            df_detalhe_show['Data de pagamento'] = pd.to_datetime(df_detalhe_show['Data de pagamento']).dt.strftime('%d/%m/%Y')
            df_detalhe_show = df_detalhe_show.sort_values(by='Data de pagamento')
            
        df_detalhe_show['Valor'] = df_detalhe_show['Valor'].apply(lambda x: formatar_brl(x))
        st.dataframe(df_detalhe_show, use_container_width=True, hide_index=True)
    else:
        st.info(f"Nenhum lançamento de gasto detalhado encontrado para '{socio_selecionado}' em {mes_selecionado_str}.")
        
    st.markdown("---")
    
    st.markdown(f"#### 📋 Tabela Comparativa Histórica — {socio_selecionado}")
    df_socios['Diferença Absoluta'] = df_socios['Realizado 2026'] - df_socios['Realizado 2025']
    df_socios['Variação %'] = (df_socios['Diferença Absoluta'] / df_socios['Realizado 2025']) * 100
    
    df_show = df_socios.copy()
    df_show['Realizado 2025'] = df_show['Realizado 2025'].apply(lambda x: formatar_brl(x))
    df_show['Realizado 2026'] = df_show['Realizado 2026'].apply(lambda x: formatar_brl(x))
    df_show['Diferença Absoluta'] = df_show['Diferença Absoluta'].apply(lambda x: formatar_brl(x, mostrar_sinal=True))
    df_show['Variação %'] = df_show['Variação %'].apply(lambda x: formatar_pct(x))
    st.dataframe(df_show[['Mês / Referência', 'Realizado 2025', 'Realizado 2026', 'Diferença Absoluta', 'Variação %']], use_container_width=True, hide_index=True)


# ==========================================
# TELA 5: CUSTOS NA PRESTAÇÃO DE SERVIÇO
# ==========================================
elif paginas[selecao_pagina] == "custos":
    renderizar_cabecalho_pagina("Análise de Custos na Prestação de Serviço", f"Acompanhamento Analítico em {mes_selecionado_str.upper()}")
    exibir_painel_cards_globais(compacto=True)
    
    df_mes_custos = df_raw[(df_raw['Grupo'] == 'CUSTOS NA PRESTAÇÃO DE SERVIÇO') & (df_raw['Ano'] == ano_atual) & (df_raw['Mês'] == mes_atual)]
    custos_mes_atual = df_mes_custos['Valor'].sum()
    
    df_ytd_custos = df_raw[(df_raw['Grupo'] == 'CUSTOS NA PRESTAÇÃO DE SERVIÇO') & (df_raw['Ano'] == ano_atual) & (df_raw['Mês'] <= mes_atual)]
    custos_ytd_atual = df_ytd_custos['Valor'].sum()
    
    st.markdown(f"#### 🛠️ Resumo de Custos Operacionais ({mes_selecionado_str})")
    col_c1, col_c2 = st.columns(2)
    col_c1.metric("📉 Custo no Mês Selecionado", formatar_brl(custos_mes_atual))
    col_c2.metric("📅 Custo Acumulado no Ano (YTD)", formatar_brl(custos_ytd_atual))
    st.markdown("---")
        
    st.markdown("#### 📊 Histórico e Evolução do Custo na Prestação de Serviço")
    df_custos = construir_tabela_comparativa('CUSTOS NA PRESTAÇÃO DE SERVIÇO')
    labels_custos_2025 = df_custos['Realizado 2025'].apply(resumir_valor_grafico)
    labels_custos_2026 = df_custos['Realizado 2026'].apply(resumir_valor_grafico)
    
    col_g1, col_g2 = st.columns([2, 1])
    with col_g1:
        fig_bar_c = go.Figure()
        fig_bar_c.add_trace(go.Bar(
            x=df_custos['Mês / Referência'], y=df_custos['Realizado 2025'], name='2025', 
            marker_color='#ff9999', text=labels_custos_2025, textposition='outside'
        ))
        fig_bar_c.add_trace(go.Bar(
            x=df_custos['Mês / Referência'], y=df_custos['Realizado 2026'], name='2026', 
            marker_color='#17a2b8', text=labels_custos_2026, textposition='outside'
        ))
        fig_bar_c.update_layout(title="Histórico Mensal de Custos (Ano x Ano)", barmode='group', height=370, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_bar_c, use_container_width=True)
        
    with col_g2:
        ytd_custos_2025 = df_raw[(df_raw['Grupo'] == 'CUSTOS NA PRESTAÇÃO DE SERVIÇO') & (df_raw['Ano'] == 2025) & (df_raw['Mês'] <= mes_atual)]['Valor'].sum()
        ytd_custos_2026 = df_raw[(df_raw['Grupo'] == 'CUSTOS NA PRESTAÇÃO DE SERVIÇO') & (df_raw['Ano'] == 2026) & (df_raw['Mês'] <= mes_atual)]['Valor'].sum()
        
        fig_pie_c = go.Figure(data=[go.Pie(
            labels=['Acumulado 2025', 'Acumulado 2026'], values=[ytd_custos_2025, ytd_custos_2026], 
            hole=.5, marker=dict(colors=['#ff9999', '#17a2b8']), textinfo='percent+value', textposition='inside'
        )])
        fig_pie_c.update_layout(title=f"Custos Acumulados (Até {meses_list_abrev[mes_atual-1]})", height=370, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_pie_c, use_container_width=True)
        
    st.markdown("---")
    
    st.markdown(f"#### 🔍 Detalhamento dos Custos do Mês ({mes_selecionado_str})")
    colunas_detalhe = ['Data de pagamento', 'Contato', 'Descrição', 'Categoria', 'Valor']
    colunas_disponiveis_c = [c for c in colunas_detalhe if c in df_mes_custos.columns]
    df_detalhe_custos = df_mes_custos[colunas_disponiveis_c].copy()
    
    if not df_detalhe_custos.empty:
        if 'Data de pagamento' in df_detalhe_custos.columns:
            df_detalhe_custos['Data de pagamento'] = pd.to_datetime(df_detalhe_custos['Data de pagamento']).dt.strftime('%d/%m/%Y')
        df_detalhe_custos['Valor'] = df_detalhe_custos['Valor'].apply(lambda x: formatar_brl(x))
        st.dataframe(df_detalhe_custos, use_container_width=True, hide_index=True)
    else:
        st.info(f"Nenhum custo detalhado encontrado para o período {mes_selecionado_str}.")
        
    st.markdown("---")
    
    st.markdown("#### 📋 Tabela de Evolução Analítica")
    df_custos['Diferença Absoluta'] = df_custos['Realizado 2026'] - df_custos['Realizado 2025']
    df_custos['Variação %'] = (df_custos['Diferença Absoluta'] / df_custos['Realizado 2025']) * 100
    
    df_custos_show = df_custos.copy()
    df_custos_show['Realizado 2025'] = df_custos_show['Realizado 2025'].apply(lambda x: formatar_brl(x))
    df_custos_show['Realizado 2026'] = df_custos_show['Realizado 2026'].apply(lambda x: formatar_brl(x))
    df_custos_show['Diferença Absoluta'] = df_custos_show['Diferença Absoluta'].apply(lambda x: formatar_brl(x, mostrar_sinal=True))
    df_custos_show['Variação %'] = df_custos_show['Variação %'].apply(lambda x: formatar_pct(x))
    
    st.dataframe(df_custos_show[['Mês / Referência', 'Realizado 2025', 'Realizado 2026', 'Diferença Absoluta', 'Variação %']], use_container_width=True, hide_index=True)
