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

# Verifica se o arquivo existe na pasta antes de prosseguir
if not os.path.exists("dados_conectsol.xlsx"):
    st.error("⚠️ O arquivo 'dados_conectsol.xlsx' não foi encontrado na pasta raiz do projeto. Por favor, verifique o nome e local do arquivo.")
    st.stop()

# 2. FUNÇÕES DE FORMATÇÃO CONFORME PADRÃO FINANCEIRO BRASILEIRO
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

# 3. CARREGAMENTO DOS DADOS DIRETAMENTE DA PLANILHA
@st.cache_data
def carregar_dados():
    # Lê a aba 'DADOS' do arquivo Excel
    df = pd.read_excel("dados_conectsol.xlsx", sheet_name="DADOS")
    # Limpa linhas que não possuem informações de Ano ou Mês
    df = df.dropna(subset=['Ano', 'Mês'])
    df['Mês'] = df['Mês'].astype(int)
    df['Ano'] = df['Ano'].astype(int)
    return df

df_raw = carregar_dados()

# 4. MAPEAMENTO E CONSTRUÇÃO DO FILTRO DE DATAS DINÂMICO
meses_pt = {1: 'jan', 2: 'fev', 3: 'mar', 4: 'abr', 5: 'mai', 6: 'jun',
            7: 'jul', 8: 'ago', 9: 'set', 10: 'out', 11: 'nov', 12: 'dez'}
meses_list_abrev = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']

# Extrai e ordena de forma cronológica todos os anos e meses presentes na planilha
periodos_unicos = df_raw[['Ano', 'Mês']].drop_duplicates().sort_values(by=['Ano', 'Mês'])
opcoes_filtro = [f"{meses_pt[row['Mês']]}/{row['Ano']}" for _, row in periodos_unicos.iterrows()]

# 5. BARRA LATERAL (SIDEBAR)
st.sidebar.markdown("## 🌐 WL EXPERTISE")
st.sidebar.markdown("---")
st.sidebar.markdown("**Navegação Estratégica:**")

paginas = {
    "🚀 Visão Geral (YTD)": "visao_geral",
    "📈 Análise de Entradas": "entradas",
    "👥 Gestão de Sócios": "socios",
    "🛠️ Custos na Prestação de Serviço": "custos"
}
selecao_pagina = st.sidebar.radio("Selecione a tela:", list(paginas.keys()), label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.markdown("**Selecione o Mês de Referência:**")
# Define o último mês disponível na planilha como a seleção padrão inicial
mes_selecionado_str = st.sidebar.selectbox("Mês:", opcoes_filtro, index=len(opcoes_filtro)-1, label_visibility="collapsed")

# Traduz a string selecionada (ex: 'mai/2026') de volta para inteiros de Mês e Ano
mes_ref_str, ano_ref_str = mes_selecionado_str.split('/')
ano_atual = int(ano_ref_str)
mes_atual = [k for k, v in meses_pt.items() if v == mes_ref_str][0]

# 6. PROCESSAMENTO DOS DADOS FILTRADOS (MÊS ATUAL E ACUMULADO YTD)
# Nota: Filtros padrão de finanças removem o grupo 'TRANSFERÊNCIAS' para evitar dupla contagem de movimentações internas
df_sem_transf = df_raw[df_raw['Grupo'] != 'TRANSFERÊNCIAS']

df_mes = df_sem_transf[(df_sem_transf['Ano'] == ano_atual) & (df_sem_transf['Mês'] == mes_atual)]
df_ytd = df_sem_transf[(df_sem_transf['Ano'] == ano_atual) & (df_sem_transf['Mês'] <= mes_atual)]

# Cálculos Mensais
entradas_mes = df_mes[df_mes['Tipo'] == 'Entrada']['Valor'].sum()
saidas_mes = df_mes[df_mes['Tipo'] == 'Saída']['Valor'].sum()
resultado_mes = entradas_mes - saidas_mes
margem_mes = (resultado_mes / entradas_mes * 100) if entradas_mes > 0 else 0

# Cálculos Acumulados (YTD)
entradas_ytd = df_ytd[df_ytd['Tipo'] == 'Entrada']['Valor'].sum()
saidas_ytd = df_ytd[df_ytd['Tipo'] == 'Saída']['Valor'].sum()
resultado_ytd = entradas_ytd - saidas_ytd
margem_ytd = (resultado_ytd / entradas_ytd * 100) if entradas_ytd > 0 else 0


# ==========================================
# PAG 1: VISÃO GERAL
# ==========================================
if paginas[selecao_pagina] == "visao_geral":
    st.title("Performance Financeira ConectSol")
    st.subheader(f"Acumulado Estratégico (YTD) até {mes_selecionado_str.upper()}")
    st.markdown("---")
    
    st.markdown(f"#### Resumo do Mês ({mes_selecionado_str})")
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Entradas no Mês", formatar_brl(entradas_mes))
    c2.metric("💸 Saídas no Mês", formatar_brl(saidas_mes))
    
    # O sinal de mais ou menos na string do delta controla nativamente a cor e seta do componente
    delta_mes_str = f"{margem_mes:+.1f}% Margem".replace('.', ',')
    c3.metric("📊 Resultado do Mês", formatar_brl(resultado_mes), delta=delta_mes_str)
    
    st.markdown("---")
    st.markdown("#### Resumo Acumulado (YTD)")
    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("📈 Entradas Acumuladas", formatar_brl(entradas_ytd))
    cc2.metric("📉 Saídas Acumuladas", formatar_brl(saidas_ytd))
    
    delta_ytd_str = f"{margem_ytd:+.1f}% Margem".replace('.', ',')
    cc3.metric("⚖️ Resultado Líquido YTD", formatar_brl(resultado_ytd), delta=delta_ytd_str)


# ==========================================
# PAG 2: ANÁLISE DE ENTRADAS
# ==========================================
elif paginas[selecao_pagina] == "entradas":
    st.title("📈 Análise de Entradas")
    st.subheader(f"Extrato de Lançamentos Recebidos — Referência {mes_selecionado_str.upper()}")
    st.markdown("---")
    
    # Filtra apenas registros de entradas reais da planilha para o mês e ano selecionados
    df_entradas_reais = df_raw[(df_raw['Tipo'] == 'Entrada') & (df_raw['Ano'] == ano_atual) & (df_raw['Mês'] == mes_atual)].copy()
    
    colunas_foco = ['Data de pagamento', 'Contato', 'Descrição', 'Categoria', 'Situação', 'Valor', 'Instituição']
    colunas_existentes = [c for c in colunas_foco if c in df_entradas_reais.columns]
    
    df_exibicao = df_entradas_reais[colunas_existentes].copy()
    
    if not df_exibicao.empty:
        # Formata a coluna de data caso esteja em formato datetime do pandas
        if 'Data de pagamento' in df_exibicao.columns:
            df_exibicao['Data de pagamento'] = pd.to_datetime(df_exibicao['Data de pagamento']).dt.strftime('%d/%m/%Y')
        
        # Formata os valores monetários na tabela
        df_exibicao['Valor'] = df_exibicao['Valor'].apply(lambda x: formatar_brl(x))
        st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
    else:
        st.info(f"Nenhum lançamento de Entrada encontrado para o período {mes_selecionado_str}.")


# ==========================================
# PAG 3: GESTÃO DE SÓCIOS
# ==========================================
elif paginas[selecao_pagina] == "socios":
    st.title("Gestão de Sócios")
    st.subheader(f"Retiradas Mensais — Consolidação de Todos os Sócios ({mes_selecionado_str.upper()})")
    st.markdown("---")
    
    # Função auxiliar interna para pivotar qualquer grupo de forma dinâmica
    def construir_tabela_comparativa(grupo_nome):
        df_grupo = df_raw[df_raw['Grupo'] == grupo_nome]
        pivot = df_grupo.pivot_table(index='Mês', columns='Ano', values='Valor', aggfunc='sum').reset_index()
        
        all_months = pd.DataFrame({'Mês': range(1, 13)})
        pivot = pd.merge(all_months, pivot, on='Mês', how='left')
        
        if 2025 not in pivot.columns: pivot[2025] = np.nan
        if 2026 not in pivot.columns: pivot[2026] = np.nan
        
        pivot['Mês / Referência'] = pivot['Mês'].map(lambda x: meses_list_abrev[x-1])
        return pivot.rename(columns={2025: 'Realizado 2025', 2026: 'Realizado 2026'})

    df_socios = construir_tabela_comparativa('DESPESAS DOS SÓCIOS')
    
    col_graf1, col_graf2 = st.columns([2, 1])
    
    with col_graf1:
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(x=df_socios['Mês / Referência'], y=df_socios['Realizado 2025'], name='2025', marker_color='#9fb1c2'))
        fig_bar.add_trace(go.Bar(x=df_socios['Mês / Referência'], y=df_socios['Realizado 2026'], name='2026', marker_color='#005a60'))
        fig_bar.update_layout(title="Comparativo Mensal de Retiradas", barmode='group', height=350, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col_graf2:
        # Calcula os valores acumulados (YTD) dinamicamente até o mês selecionado para o gráfico de rosca
        ytd_socios_2025 = df_raw[(df_raw['Grupo'] == 'DESPESAS DOS SÓCIOS') & (df_raw['Ano'] == 2025) & (df_raw['Mês'] <= mes_atual)]['Valor'].sum()
        ytd_socios_2026 = df_raw[(df_raw['Grupo'] == 'DESPESAS DOS SÓCIOS') & (df_raw['Ano'] == 2026) & (df_raw['Mês'] <= mes_atual)]['Valor'].sum()
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=['Acumulado 2025', 'Acumulado 2026'], 
            values=[ytd_socios_2025, ytd_socios_2026], 
            hole=.5,
            marker=dict(colors=['#9fb1c2', '#005a60']),
            textinfo='percent+value',
            textposition='inside'
        )])
        fig_pie.update_layout(title=f"Acumulado Retiradas (Até {meses_list_abrev[mes_atual-1]})", height=350, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_pie, use_container_width=True)
        
    st.markdown("---")
    st.markdown("#### Tabela Comparativa de Retiradas")
    
    # Cálculos matemáticos automáticos diretos do DataFrame
    df_socios['Diferença Absoluta'] = df_socios['Realizado 2026'] - df_socios['Realizado 2025']
    df_socios['Variação %'] = (df_socios['Diferença Absoluta'] / df_socios['Realizado 2025']) * 100
    
    df_show = df_socios.copy()
    df_show['Realizado 2025'] = df_show['Realizado 2025'].apply(lambda x: formatar_brl(x))
    df_show['Realizado 2026'] = df_show['Realizado 2026'].apply(lambda x: formatar_brl(x))
    df_show['Diferença Absoluta'] = df_show['Diferença Absoluta'].apply(lambda x: formatar_brl(x, mostrar_sinal=True))
    df_show['Variação %'] = df_show['Variação %'].apply(lambda x: formatar_pct(x))
    
    st.dataframe(df_show[['Mês / Referência', 'Realizado 2025', 'Realizado 2026', 'Diferença Absoluta', 'Variação %']], use_container_width=True, hide_index=True)


# ==========================================
# PAG 4: CUSTOS NA PRESTAÇÃO DE SERVIÇO
# ==========================================
elif paginas[selecao_pagina] == "custos":
    st.title("Análise de Custos na Prestação de Serviço")
    st.subheader(f"Acompanhamento Analítico em {mes_selecionado_str.upper()}")
    st.markdown("---")
    
    # Exibe os mesmos KPIs do mês selecionado estruturados na visão de custos
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Entradas no Mês", formatar_brl(entradas_mes))
    c2.metric("💸 Saídas no Mês", formatar_brl(saiders_mes if 'saiders_mes' in locals() else saidas_mes))
    delta_c_str = f"{margem_mes:+.1f}% Margem".replace('.', ',')
    c3.metric("📊 Resultado do Mês", formatar_brl(resultado_mes), delta=delta_c_str)
        
    st.markdown("---")
    st.markdown("#### Custos na Prestação de Serviço — Mensalidades")
    
    df_custos = construir_tabela_comparativa('CUSTOS NA PRESTAÇÃO DE SERVIÇO')
    
    col_g1, col_g2 = st.columns([2, 1])
    
    with col_g1:
        fig_bar_c = go.Figure()
        fig_bar_c.add_trace(go.Bar(x=df_custos['Mês / Referência'], y=df_custos['Realizado 2025'], name='2025', marker_color='#ff9999'))
        fig_bar_c.add_trace(go.Bar(x=df_custos['Mês / Referência'], y=df_custos['Realizado 2026'], name='2026', marker_color='#17a2b8'))
        fig_bar_c.update_layout(title="Histórico Mensal de Custos", barmode='group', height=350, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_bar_c, use_container_width=True)
        
    with col_g2:
        # Calcula os custos acumulados YTD dinamicamente
        ytd_custos_2025 = df_raw[(df_raw['Grupo'] == 'CUSTOS NA PRESTAÇÃO DE SERVIÇO') & (df_raw['Ano'] == 2025) & (df_raw['Mês'] <= mes_atual)]['Valor'].sum()
        ytd_custos_2026 = df_raw[(df_raw['Grupo'] == 'CUSTOS NA PRESTAÇÃO DE SERVIÇO') & (df_raw['Ano'] == 2026) & (df_raw['Mês'] <= mes_atual)]['Valor'].sum()
        
        fig_pie_c = go.Figure(data=[go.Pie(
            labels=['Acumulado 2025', 'Acumulado 2026'], 
            values=[ytd_custos_2025, ytd_custos_2026], 
            hole=.5,
            marker=dict(colors=['#ff9999', '#17a2b8']),
            textinfo='percent+value',
            textposition='inside'
        )])
        fig_pie_c.update_layout(title=f"Custos Acumulados (Até {meses_list_abrev[mes_atual-1]})", height=350, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_pie_c, use_container_width=True)
        
    st.markdown("---")
    st.markdown("#### Tabela de Evolução Analítica")
    
    df_custos['Diferença Absoluta'] = df_custos['Realizado 2026'] - df_custos['Realizado 2025']
    df_custos['Variação %'] = (df_custos['Diferença Absoluta'] / df_custos['Realizado 2025']) * 100
    
    df_custos_show = df_custos.copy()
    df_custos_show['Realizado 2025'] = df_custos_show['Realizado 2025'].apply(lambda x: formatar_brl(x))
    df_custos_show['Realizado 2026'] = df_custos_show['Realizado 2026'].apply(lambda x: formatar_brl(x))
    df_custos_show['Diferença Absoluta'] = df_custos_show['Diferença Absoluta'].apply(lambda x: formatar_brl(x, mostrar_sinal=True))
    df_custos_show['Variação %'] = df_custos_show['Variação %'].apply(lambda x: formatar_pct(x))
    
    st.dataframe(df_custos_show[['Mês / Referência', 'Realizado 2025', 'Realizado 2026', 'Diferença Absoluta', 'Variação %']], use_container_width=True, hide_index=True)
    
