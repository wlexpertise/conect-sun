import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Performance Financeira ConectSol",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. FUNÇÕES DE FORMATAÇÃO CONFORME PADRÃO BRASILEIRO
def formatar_brl(valor, mostrar_sinal=False):
    if pd.isna(valor) or valor is None:
        return "-"
    sinal = "+" if mostrar_sinal and valor > 0 else ""
    if valor < 0:
        return f"({sinal}R$ {abs(valor):,.2f})".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{sinal}R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_pct(valor):
    if pd.isna(valor) or valor is None:
        return "-"
    return f"{valor:+.2f}%".replace(".", ")").replace(".", ",").replace(")", ".")

# 3. BASE DE DADOS (MOCKDATA DOS PRINTS)

# Dados da Visão Geral (YTD) por Mês de Referência
dados_visao_geral = {
    "mar/2026": {
        "entradas_mes": 167815.60, "saidas_mes": 218201.10, "res_mes": -50385.50, "margem_mes": "-30,0%",
        "entradas_ytd": 380193.32, "saidas_ytd": 476089.10, "res_ytd": -95895.78, "margem_ytd": "-25,2%"
    },
    "mai/2026": {
        "entradas_mes": 94431.26, "saidas_mes": 108605.33, "res_mes": -14174.07, "margem_mes": "-15,0%",
        "entradas_ytd": 747168.43, "saidas_ytd": 850659.59, "res_ytd": -103491.16, "margem_ytd": "-13,9%"
    }
}

# Dados de Custos na Prestação de Serviço (Mensalidades)
dados_custos = {
    'Mês / Referência': ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ'],
    'Realizado 2025': [34535.30, 76312.49, 74034.92, 56934.55, 72217.31, 50701.29, 330082.31, 121113.10, 47624.71, 139303.67, 76000.00, 59000.00],
    'Realizado 2026': [109972.91, 40181.19, 146580.95, 167061.17, 55860.45, None, None, None, None, None, None, None]
}
df_custos = pd.DataFrame(dados_custos)

# Dados de Gestão de Sócios (Retiradas)
dados_socios = {
    'Mês / Referência': ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ'],
    'Realizado 2025': [21000.00, 22000.00, 27000.00, 3000.00, 4000.00, 5000.00, 30000.00, 6000.00, 227.00, 2000.00, 10000.00, 8000.00],
    'Realizado 2026': [15000.00, 15000.00, 29000.00, 12000.00, 15000.00, None, None, None, None, None, None, None]
}
df_socios = pd.DataFrame(dados_socios)

# Extrato de Entradas (Print do Excel)
df_extrato_entradas = pd.DataFrame([
    {"Data de pagamento": "02/03/2026", "Contato": "HELIO DE SOUZA OLIVEIRA", "Descrição": "ENTRADA DO CLIENTE HELIO (ROTARY)", "Categoria": "Instalação Fotovoltaica", "Situação": "Conciliado", "Valor": 15000.00, "Instituição": "Sicoob"},
    {"Data de pagamento": "03/03/2026", "Contato": "MARCIA CRISTINA SILVA SANTOS", "Descrição": "TRANSFERENCIA DE CREDITO", "Categoria": "Serviços ConectSol", "Situação": "Conciliado", "Valor": 200.00, "Instituição": "Sicoob"},
    {"Data de pagamento": "03/03/2026", "Contato": "JOSE WALTER MENDES NOGUEIRA", "Descrição": "INFINITY - CLIENTE JUNIA VILACA", "Categoria": "Instalação Fotovoltaica", "Situação": "Sem conciliação", "Valor": 31000.00, "Instituição": "-"},
    {"Data de pagamento": "03/03/2026", "Contato": "FUNDACAO SAO VICENTE DE PAULO", "Descrição": "691-6", "Categoria": "Instalação Fotovoltaica", "Situação": "Conciliado", "Valor": 511.10, "Instituição": "Sicoob"},
    {"Data de pagamento": "05/03/2026", "Contato": "STANLEY DOUGLAS PIMENTEL PEREIRA", "Descrição": "RECIBO 377", "Categoria": "Instalação Fotovoltaica", "Situação": "Conciliado", "Valor": 10000.00, "Instituição": "Sicoob"},
    {"Data de pagamento": "05/03/2026", "Contato": "AGUA MINERAL VIVA LTDA", "Descrição": "BOLETO 202608", "Categoria": "Instalação Fotovoltaica", "Situação": "Conciliado", "Valor": 250.00, "Instituição": "Sicoob"},
    {"Data de pagamento": "09/03/2026", "Contato": "JANETE CAMPOS DE AZEVEDO ASSIS", "Descrição": "BOLETO 688-3", "Categoria": "Instalação Fotovoltaica", "Situação": "Conciliado", "Valor": 1000.00, "Instituição": "Sicoob"},
    {"Data de pagamento": "31/03/2026", "Contato": "ALEXANDRE FORNTUNA COTA", "Descrição": "RECEBIMENTO INTEGRAL", "Categoria": "Instalação Fotovoltaica", "Situação": "Conciliado", "Valor": 13000.00, "Instituição": "Sicoob"}
])

# 4. BARRA LATERAL (SIDEBAR)
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
mes_ref = st.sidebar.selectbox("Mês:", ["mar/2026", "mai/2026"], label_visibility="collapsed")

# Carrega contexto do mês selecionado
contexto = dados_visao_geral[mes_ref]


# ==========================================
# PAG 1: VISÃO GERAL
# ==========================================
if paginas[selecao_pagina] == "visao_geral":
    st.title("Performance Financeira ConectSol")
    st.subheader(f"Acumulado Estratégico (YTD) até {mes_ref.upper()}")
    st.markdown("---")
    
    st.markdown(f"#### Resumo do Mês ({mes_ref})")
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Entradas no Mês", formatar_brl(contexto["entradas_mes"]))
    c2.metric("💸 Saídas no Mês", formatar_brl(contexto["saidas_mes"]))
    
    # CORREÇÃO: O sinal de menos (-) força a cor vermelha e seta para baixo nativamente
    c3.metric("📊 Resultado do Mês", formatar_brl(contexto["res_mes"]), delta=f"{contexto['margem_mes']} Margem")
    
    st.markdown("---")
    st.markdown("#### Resumo Acumulado (YTD)")
    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("📈 Entradas Acumuladas", formatar_brl(contexto["entradas_ytd"]))
    cc2.metric("📉 Saídas Acumuladas", formatar_brl(contexto["saidas_ytd"]))
    
    # CORREÇÃO: Sinal de menos (-) no delta garante a exibição correta da margem acumulada
    cc3.metric("⚖️ Resultado Líquido YTD", formatar_brl(contexto["res_ytd"]), delta=f"{contexto['margem_ytd']} Margem")


# ==========================================
# PAG 2: ANÁLISE DE ENTRADAS
# ==========================================
elif paginas[selecao_pagina] == "entradas":
    st.title("📈 Análise de Entradas")
    st.subheader(f"Extrato de Lançamentos Recebidos — Referência {mes_ref.upper()}")
    st.markdown("---")
    
    df_exibicao_entradas = df_extrato_entradas.copy()
    df_exibicao_entradas["Valor"] = df_exibicao_entradas["Valor"].apply(lambda x: formatar_brl(x))
    
    st.dataframe(df_exibicao_entradas, use_container_width=True, hide_index=True)


# ==========================================
# PAG 3: GESTÃO DE SÓCIOS
# ==========================================
elif paginas[selecao_pagina] == "socios":
    st.title("Gestão de Sócios")
    st.subheader(f"Retiradas Mensais — Consolidação de Todos os Sócios ({mes_ref.upper()})")
    st.markdown("---")
    
    col_graf1, col_graf2 = st.columns([2, 1])
    
    with col_graf1:
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(x=df_socios['Mês / Referência'], y=df_socios['Realizado 2025'], name='2025', marker_color='#9fb1c2'))
        fig_bar.add_trace(go.Bar(x=df_socios['Mês / Referência'], y=df_socios['Realizado 2026'], name='2026', marker_color='#005a60'))
        fig_bar.update_layout(title="Comparativo Mensal de Retiradas", barmode='group', height=350, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col_graf2:
        # CORREÇÃO: textinfo='percent+value' força a exibição do % e do valor na rosca
        fig_pie = go.Figure(data=[go.Pie(
            labels=['2025', '2026'], 
            values=[138000, 86000], 
            hole=.5,
            marker=dict(colors=['#9fb1c2', '#005a60']),
            textinfo='percent+value',
            textposition='inside'
        )])
        fig_pie.update_layout(title="Acumulado Retiradas", height=350, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_pie, use_container_width=True)
        
    st.markdown("---")
    st.markdown("#### Tabela Comparativa de Retiradas")
    
    # CORREÇÃO: Cálculos matemáticos automáticos das colunas faltantes
    df_socios['Diferença Absoluta'] = df_socios['Realizado 2026'] - df_socios['Realizado 2025']
    df_socios['Variação %'] = (df_socios['Diferença Absoluta'] / df_socios['Realizado 2025']) * 100
    
    df_show = df_socios.copy()
    df_show['Realizado 2025'] = df_show['Realizado 2025'].apply(lambda x: formatar_brl(x))
    df_show['Realizado 2026'] = df_show['Realizado 2026'].apply(lambda x: formatar_brl(x))
    df_show['Diferença Absoluta'] = df_show['Diferença Absoluta'].apply(lambda x: formatar_brl(x, mostrar_sinal=True))
    df_show['Variação %'] = df_show['Variação %'].apply(lambda x: formatar_pct(x))
    
    st.dataframe(df_show, use_container_width=True, hide_index=True)


# ==========================================
# PAG 4: CUSTOS NA PRESTAÇÃO DE SERVIÇO
# ==========================================
elif paginas[selecao_pagina] == "custos":
    st.title("Análise de Custos na Prestação de Serviço")
    st.subheader(f"Acompanhamento Analítico em {mes_ref.upper()}")
    st.markdown("---")
    
    # KPIs Dinâmicos de Custos
    c1, c2, c3 = st.columns(3)
    if mes_ref == "mai/2026":
        c1.metric("💰 Entradas no Mês", "R$ 91.431,26")
        c2.metric("💸 Saídas no Mês", "R$ 108.605,33")
        # CORREÇÃO: Alinhado para vermelho/baixo
        c3.metric("📊 Resultado do Mês", "(R$ 17.174,07)", delta="-18,8% Margem")
    else:
        c1.metric("💰 Entradas no Mês", "R$ 167.815,60")
        c2.metric("💸 Saídas no Mês", "R$ 218.201,10")
        c3.metric("📊 Resultado do Mês", "(R$ 50.385,50)", delta="-30,0% Margem")
        
    st.markdown("---")
    st.markdown("#### Custos na Prestação de Serviço — Mensalidades")
    
    col_g1, col_g2 = st.columns([2, 1])
    
    with col_g1:
        fig_bar_c = go.Figure()
        fig_bar_c.add_trace(go.Bar(x=df_custos['Mês / Referência'], y=df_custos['Realizado 2025'], name='2025', marker_color='#ff9999'))
        fig_bar_c.add_trace(go.Bar(x=df_custos['Mês / Referência'], y=df_custos['Realizado 2026'], name='2026', marker_color='#17a2b8'))
        fig_bar_c.update_layout(title="Histórico Mensal de Custos", barmode='group', height=350, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_bar_c, use_container_width=True)
        
    with col_g2:
        # CORREÇÃO: textinfo='percent+value' adicionado para exibir os percentuais corrigindo o gráfico
        fig_pie_c = go.Figure(data=[go.Pie(
            labels=['Realizado 2025', 'Realizado 2026'], 
            values=[1138000, 520000], 
            hole=.5,
            marker=dict(colors=['#ff9999', '#17a2b8']),
            textinfo='percent+value',
            textposition='inside'
        )])
        fig_pie_c.update_layout(title="Divisão de Custos Acumulados", height=350, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_pie_c, use_container_width=True)
        
    st.markdown("---")
    st.markdown("#### Tabela de Evolução Analítica")
    
    # CORREÇÃO: Cálculos matemáticos das colunas de Diferença e Variação % aplicados de forma dinâmica
    df_custos['Diferença Absoluta'] = df_custos['Realizado 2026'] - df_custos['Realizado 2025']
    df_custos['Variação %'] = (df_custos['Diferença Absoluta'] / df_custos['Realizado 2025']) * 100
    
    df_custos_show = df_custos.copy()
    df_custos_show['Realizado 2025'] = df_custos_show['Realizado 2025'].apply(lambda x: formatar_brl(x))
    df_custos_show['Realizado 2026'] = df_custos_show['Realizado 2026'].apply(lambda x: formatar_brl(x))
    df_custos_show['Diferença Absoluta'] = df_custos_show['Diferença Absoluta'].apply(lambda x: formatar_brl(x, mostrar_sinal=True))
    df_custos_show['Variação %'] = df_custos_show['Variação %'].apply(lambda x: formatar_pct(x))
    
    st.dataframe(df_custos_show, use_container_width=True, hide_index=True)
