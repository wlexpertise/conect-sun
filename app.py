import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="WL Expertise | Conectsol BI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🎨 DESIGN MINIMALISTA CORPORATIVO
st.markdown("""
    <style>
        .stApp { background-color: #f3f4f6 !important; }
        h1, h2, h3, p, label, .stMarkdown { color: #1f2937 !important; }
        [data-testid="stSidebar"] {
            background-color: rgba(19, 163, 181, 0.10) !important;
            border-right: 1px solid rgba(19, 163, 181, 0.20) !important;
        }
        [data-testid="stSidebar"] hr { border-color: rgba(19, 163, 181, 0.30) !important; }
        div[data-testid="stMetricValue"] > div { color: #0B5A60 !important; font-weight: 700; }
        .logo-box {
            background-color: #ffffff !important;
            padding: 15px !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important;
            text-align: center !important;
            display: block !important;
            margin-bottom: 10px !important;
        }
    </style>
""", unsafe_allow_html=True)

def formatar_brl(valor):
    if valor is None or pd.isna(valor) or valor == 0: return "-"
    if valor < 0: return f"(R$ {abs(valor):,.2f})".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_pct(valor):
    if valor is None or pd.isna(valor) or valor == 0: return "-"
    if valor < 0: return f"({abs(valor):.1f}%)".replace(".", ",")
    return f"{valor:.1f}%".replace(".", ",")

@st.cache_data
def carregar_dados():
    nome_do_arquivo = 'dados_conectsol.xlsx' 
    df = pd.read_excel(nome_do_arquivo)
    df.columns = df.columns.str.strip()
    
    col_data_pag = df.columns[4]
    col_contato = df.columns[7]
    col_categoria = df.columns[10]
    col_situacao = df.columns[11]
    col_valor = df.columns[12]
    col_grupo = df.columns[13]
    col_tipo_p = df.columns[15]
    
    df['situacao_limpa'] = df[col_situacao].astype(str).str.strip().str.lower()
    df = df[df['situacao_limpa'].isin(['conciliado', 'sem conciliação'])].copy()
    
    if df[col_valor].dtype == object:
        df[col_valor] = df[col_valor].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
    df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0)
    
    df[col_data_pag] = pd.to_datetime(df[col_data_pag], errors='coerce', dayfirst=True)
    df = df.dropna(subset=[col_data_pag])
    
    df['ano'] = df[col_data_pag].dt.year
    df['mes'] = df[col_data_pag].dt.month
    df['ano_mes_num'] = df[col_data_pag].dt.strftime('%Y%m')
    meses_pt = {1: 'jan', 2: 'fev', 3: 'mar', 4: 'abr', 5: 'mai', 6: 'jun', 7: 'jul', 8: 'ago', 9: 'set', 10: 'out', 11: 'nov', 12: 'dez'}
    df['mes_nome_pt'] = df['mes'].map(meses_pt)
    df['ano_mes_texto'] = df['mes_nome_pt'] + '/' + df['ano'].astype(str)
    
    df['tipo_p_limpo'] = df[col_tipo_p].astype(str).str.strip().str.upper()
    df['fluxo_limpo'] = 'ignorar'
    df.loc[df['tipo_p_limpo'] == 'VENDA', 'fluxo_limpo'] = 'entrada'
    df.loc[df['tipo_p_limpo'].isin(['CUSTO', 'DESPESA']), 'fluxo_limpo'] = 'saída'
    
    df = df[df['fluxo_limpo'].isin(['entrada', 'saída'])].copy()
    
    return df, col_data_pag, col_contato, col_categoria, col_valor, col_grupo

df_base, col_data_pag, col_contato, col_categoria, col_valor, col_grupo = carregar_dados()

st.sidebar.image("Logohorizontal.png", use_container_width=True)
st.sidebar.markdown("---")

pagina = st.sidebar.radio(
    "Navegação Estratégica:", 
    ["🚀 Visão Geral (YTD)", "📈 Análise de Entradas", "📉 Detalhe de Saídas", "👥 Gestão de Sócios", "🏗️ Custos na Prestação de Serviço"]
)

df_ordenado = df_base.sort_values('ano_mes_num')
meses_disponiveis = df_ordenado['ano_mes_texto'].unique().tolist()
mes_selecionado = st.sidebar.selectbox("Selecione o Mês de Referência:", options=meses_disponiveis, index=len(meses_disponiveis) - 1)

reg_ref = df_base[df_base['ano_mes_texto'] == mes_selecionado].iloc[0]
df_ytd = df_base[(df_base['ano'] == reg_ref['ano']) & (df_base['mes'] <= reg_ref['mes'])].copy()
df_mes = df_base[df_base['ano_mes_texto'] == mes_selecionado].copy()

header_col1, header_col2 = st.columns([4, 1])

# ==========================================
# ESTRUTURA DE NAVEGAÇÃO
# ==========================================

# --- PÁGINA 1: VISÃO GERAL (YTD) ---
if pagina == "🚀 Visão Geral (YTD)":
    with header_col1:
        st.title("Performance Financeira ConectSol")
        st.subheader(f"Dashboard Executivo: {mes_selecionado.upper()}")
    with header_col2:
        st.markdown('<div class="logo-box">', unsafe_allow_html=True)
        st.image("conectlogo.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.markdown("### 🗓️ Resumo do Mês Selecionado")
    ent_mes = df_mes[df_mes['fluxo_limpo'] == 'entrada'][col_valor].sum()
    sai_mes = df_mes[df_mes['fluxo_limpo'] == 'saída'][col_valor].sum()
    res_mes = ent_mes - sai_mes
    
    m1, m2, m3 = st.columns(3)
    m1.metric(f"💰 Entradas {mes_selecionado}", formatar_brl(ent_mes))
    m2.metric(f"💸 Saídas {mes_selecionado}", formatar_brl(sai_mes))
    m3.metric(f"📊 Resultado {mes_selecionado}", formatar_brl(res_mes))
    
    st.markdown("---")
    st.markdown("### 📈 Acumulado Estratégico (YTD)")
    ent_ytd = df_ytd[df_ytd['fluxo_limpo'] == 'entrada'][col_valor].sum()
    sai_ytd = df_ytd[df_ytd['fluxo_limpo'] == 'saída'][col_valor].sum()
    res_ytd = ent_ytd - sai_ytd
    margem_val = (res_ytd / ent_ytd * 100) if ent_ytd > 0 else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("📈 Entradas YTD", formatar_brl(ent_ytd))
    c2.metric("📉 Saídas YTD", formatar_brl(sai_ytd))
    c3.metric("📊 Resultado YTD", formatar_brl(res_ytd), delta=f"{formatar_pct(margem_val)} Margem")

    st.markdown("---")
    st.markdown(f"### 📊 Evolução Mensal do Resultado ({reg_ref['ano']})")
    
    df_ano_atual = df_base[df_base['ano'] == reg_ref['ano']].copy()
    base_meses = df_ano_atual[['ano_mes_num', 'ano_mes_texto']].drop_duplicates()
    df_ent_m = df_ano_atual[df_ano_atual['fluxo_limpo'] == 'entrada'].groupby('ano_mes_num')[col_valor].sum().reset_index(name='entrada')
    df_sai_m = df_ano_atual[df_ano_atual['fluxo_limpo'] == 'saída'].groupby('ano_mes_num')[col_valor].sum().reset_index(name='saída')
    df_hist = pd.merge(base_meses, df_ent_m, on='ano_mes_num', how='left').fillna(0)
    df_hist = pd.merge(df_hist, df_sai_m, on='ano_mes_num', how='left').fillna(0)
    df_hist['Resultado'] = df_hist['entrada'] - df_hist['saída']
    df_hist = df_hist.sort_values('ano_mes_num')
    
    textos_grafico = [formatar_brl(val) for val in df_hist['Resultado']]
    fig_evolucao = go.Figure()
    fig_evolucao.add_trace(go.Bar(
        x=df_hist['ano_mes_texto'], y=df_hist['Resultado'],
        marker_color=['#ef4444' if value < 0 else '#28B260' for value in df_hist['Resultado']],
        text=textos_grafico, textposition='auto'
    ))
    fig_evolucao.update_layout(template="plotly_white", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=25, b=15))
    st.plotly_chart(fig_evolucao, use_container_width=True)

# --- PÁGINA 2: ANÁLISE DE ENTRADAS ---
elif pagina == "📈 Análise de Entradas":
    with header_col1:
        st.title("Análise de Entradas")
        st.subheader(f"Mês de Referência: {mes_selecionado.upper()}")
    with header_col2:
        st.markdown('<div class="logo-box">', unsafe_allow_html=True)
        st.image("conectlogo.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.info("Espaço reservado para os gráficos e métricas de Entradas.")

# --- PÁGINA 3: DETALHE DE SAÍDAS ---
elif pagina == "📉 Detalhe de Saídas":
    with header_col1:
        st.title("Detalhe de Saídas")
        st.subheader(f"Mês de Referência: {mes_selecionado.upper()}")
    with header_col2:
        st.markdown('<div class="logo-box">', unsafe_allow_html=True)
        st.image("conectlogo.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.info("Espaço reservado para os gráficos e métricas de Saídas.")

# --- PÁGINA 4: GESTÃO DE SÓCIOS ---
elif pagina == "👥 Gestão de Sócios":
    with header_col1:
        st.title("Gestão de Sócios")
        st.subheader(f"Mês de Referência: {mes_selecionado.upper()}")
    with header_col2:
        st.markdown('<div class="logo-box">', unsafe_allow_html=True)
        st.image("conectlogo.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.info("Espaço reservado para análise financeira referente aos sócios.")

# --- PÁGINA 5: CUSTOS NA PRESTAÇÃO DE SERVIÇO ---
elif pagina == "🏗️ Custos na Prestação de Serviço":
    with header_col1:
        st.title("Custos na Prestação de Serviço")
        st.subheader(f"Mês de Referência: {mes_selecionado.upper()}")
    with header_col2:
        st.markdown('<div class="logo-box">', unsafe_allow_html=True)
        st.image("conectlogo.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.info("Espaço reservado para análise de custos diretos e indiretos.")
    
