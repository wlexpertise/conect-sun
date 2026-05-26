import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuração e Estilos
st.set_page_config(page_title="WL Expertise | Conectsol BI", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
    <style>
        .stApp { background-color: #f3f4f6 !important; }
        .logo-box { background-color: #ffffff !important; padding: 15px !important; border-radius: 12px !important; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); text-align: center; margin-bottom: 10px; }
        div[data-testid="stMetricValue"] > div { color: #0B5A60 !important; font-weight: 700; }
    </style>
""", unsafe_allow_html=True)

# Funções auxiliares
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
    
    col_data_pag, col_contato, col_categoria, col_situacao, col_valor, col_grupo, col_tipo_p = \
        df.columns[4], df.columns[7], df.columns[10], df.columns[11], df.columns[12], df.columns[13], df.columns[15]
    
    df = df[df[col_situacao].astype(str).str.strip().str.lower().isin(['conciliado', 'sem conciliação'])].copy()
    df[col_valor] = pd.to_numeric(df[col_valor].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0)
    df[col_data_pag] = pd.to_datetime(df[col_data_pag], errors='coerce', dayfirst=True)
    df = df.dropna(subset=[col_data_pag])
    
    df['ano'] = df[col_data_pag].dt.year
    df['mes'] = df[col_data_pag].dt.month
    df['ano_mes_texto'] = df[col_data_pag].dt.strftime('%b/%Y').str.lower()
    df['fluxo_limpo'] = 'ignorar'
    df.loc[df[col_tipo_p].astype(str).str.strip().str.upper() == 'VENDA', 'fluxo_limpo'] = 'entrada'
    df.loc[df[col_tipo_p].astype(str).str.strip().str.upper().isin(['CUSTO', 'DESPESA']), 'fluxo_limpo'] = 'saída'
    return df[df['fluxo_limpo'].isin(['entrada', 'saída'])].copy(), col_data_pag, col_contato, col_categoria, col_valor, col_grupo

df_base, col_data_pag, col_contato, col_categoria, col_valor, col_grupo = carregar_dados()

# Sidebar
st.sidebar.image("Logohorizontal.png", use_container_width=True)
pagina = st.sidebar.radio("Navegação Estratégica:", ["🚀 Visão Geral (YTD)", "📈 Análise de Entradas", "📉 Detalhe de Saídas", "👥 Gestão de Sócios", "🏗️ Custos na Prestação de Serviço"])
meses = df_base.sort_values('ano_mes_num')['ano_mes_texto'].unique().tolist()
mes_selecionado = st.sidebar.selectbox("Mês de Referência:", options=meses, index=len(meses)-1)

df_mes = df_base[df_base['ano_mes_texto'] == mes_selecionado]
df_ytd = df_base[(df_base['ano'] == df_mes['ano'].iloc[0]) & (df_base['mes'] <= df_mes['mes'].iloc[0])]

def exibir_resumo_mes():
    ent = df_mes[df_mes['fluxo_limpo'] == 'entrada'][col_valor].sum()
    sai = df_mes[df_mes['fluxo_limpo'] == 'saída'][col_valor].sum()
    m1, m2, m3 = st.columns(3)
    m1.metric(f"💰 Entradas ({mes_selecionado})", formatar_brl(ent))
    m2.metric(f"💸 Saídas ({mes_selecionado})", formatar_brl(sai))
    m3.metric(f"📊 Resultado ({mes_selecionado})", formatar_brl(ent - sai))
    st.markdown("---")

# Cabeçalho
header_col1, header_col2 = st.columns([4, 1])
with header_col2:
    st.markdown('<div class="logo-box">', unsafe_allow_html=True)
    st.image("conectlogo.png", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Lógica das Páginas
if pagina == "🚀 Visão Geral (YTD)":
    with header_col1: st.title("Performance Financeira"); st.subheader("Resumo YTD")
    exibir_resumo_mes()
    # ... (restante do código original da página)
    
elif pagina == "📈 Análise de Entradas":
    with header_col1: st.title("Análise de Entradas"); st.subheader(f"Competência: {mes_selecionado}")
    exibir_resumo_mes()
    # ... (restante do código original da página)

elif pagina == "📉 Detalhe de Saídas":
    with header_col1: st.title("Detalhe de Saídas"); st.subheader(f"Competência: {mes_selecionado}")
    exibir_resumo_mes()
    # ... (restante do código original da página)

elif pagina == "👥 Gestão de Sócios":
    with header_col1: st.title("Gestão de Sócios"); st.subheader(f"Competência: {mes_selecionado}")
    exibir_resumo_mes()
    # ... (restante do código original da página)

elif pagina == "🏗️ Custos na Prestação de Serviço":
    with header_col1: st.title("Custos Operacionais"); st.subheader(f"Competência: {mes_selecionado}")
    exibir_resumo_mes()
    # ... (restante do código original da página)
