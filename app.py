import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="WL Expertise | Conectsol BI", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# 🎨 DESIGN MINIMALISTA
st.markdown("""
    <style>
        .stApp { background-color: #f3f4f6 !important; }
        h1, h2, h3, p, label, .stMarkdown { color: #1f2937 !important; }
        [data-testid="stSidebar"] { background-color: rgba(19, 163, 181, 0.10) !important; border-right: 1px solid rgba(19, 163, 181, 0.20) !important; }
        div[data-testid="stMetricValue"] > div { color: #0B5A60 !important; font-weight: 700; }
        .logo-box { background-color: #ffffff !important; padding: 15px !important; border-radius: 12px !important; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); text-align: center; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

def formatar_brl(valor):
    if valor is None or pd.isna(valor) or valor == 0: return "-"
    if valor < 0: return f"(R$ {abs(valor):,.2f})".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_pct(valor):
    if valor is None or pd.isna(valor) or valor == 0: return "-"
    return f"{valor:.1f}%".replace(".", ",")

@st.cache_data
def carregar_dados():
    df = pd.read_excel('dados_conectsol.xlsx')
    df.columns = df.columns.str.strip()
    
    col_data_pag = df.columns[4]
    col_contato = df.columns[7]
    col_categoria = df.columns[10]
    col_situacao = df.columns[11]
    col_valor = df.columns[12]
    col_grupo = df.columns[13]
    col_tipo_p = df.columns[15] # Coluna P
    
    # Filtro de Situação (Obrigatório para todas as páginas)
    df['situacao_limpa'] = df[col_situacao].astype(str).str.strip().str.lower()
    df = df[df['situacao_limpa'].isin(['conciliado', 'sem conciliação'])].copy()
    
    # Tratamento de Valores
    df[col_valor] = pd.to_numeric(df[col_valor].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.'), errors='coerce').fillna(0)
    df[col_data_pag] = pd.to_datetime(df[col_data_pag], errors='coerce', dayfirst=True)
    df = df.dropna(subset=[col_data_pag])
    
    # Colunas auxiliares
    df['ano'] = df[col_data_pag].dt.year
    df['mes'] = df[col_data_pag].dt.month
    df['ano_mes_num'] = df[col_data_pag].dt.strftime('%Y%m')
    df['ano_mes_texto'] = df[col_data_pag].dt.strftime('%b/%Y').str.lower()
    
    # Mapeamento de fluxo (Venda/Custo/Despesa)
    df['tipo_p_limpo'] = df[col_tipo_p].astype(str).str.strip().str.upper()
    df['fluxo_limpo'] = 'outros'
    df.loc[df['tipo_p_limpo'] == 'VENDA', 'fluxo_limpo'] = 'entrada'
    df.loc[df['tipo_p_limpo'].isin(['CUSTO', 'DESPESA']), 'fluxo_limpo'] = 'saída'
    
    return df, col_data_pag, col_contato, col_categoria, col_valor, col_grupo, col_grupo

df_base, col_data_pag, col_contato, col_categoria, col_valor, col_grupo, col_grupo_nome = carregar_dados()

# Sidebar
st.sidebar.image("Logohorizontal.png", use_container_width=True)
pagina = st.sidebar.radio("Navegação Estratégica:", ["🚀 Visão Geral (YTD)", "📈 Análise de Entradas", "📉 Detalhe de Saídas", "👥 Gestão de Sócios", "🏗️ Custos na Prestação de Serviço"])

meses_disponiveis = df_base.sort_values('ano_mes_num')['ano_mes_texto'].unique().tolist()
mes_selecionado = st.sidebar.selectbox("Selecione o Mês:", options=meses_disponiveis, index=len(meses_disponiveis) - 1)

df_mes = df_base[df_base['ano_mes_texto'] == mes_selecionado].copy()
df_ytd = df_base[(df_base['ano'] == int(mes_selecionado[-4:])) & (df_base['ano_mes_num'] <= df_base[df_base['ano_mes_texto'] == mes_selecionado]['ano_mes_num'].iloc[0])].copy()

# Renderização
header_col1, header_col2 = st.columns([4, 1])
with header_col2: st.image("conectlogo.png", width=150)

if pagina == "🚀 Visão Geral (YTD)":
    st.title("Performance Financeira")
    st.subheader(f"Dashboard: {mes_selecionado.upper()}")
    
    # Métricas Mês
    m1, m2, m3 = st.columns(3)
    m1.metric("💰 Entradas Mês", formatar_brl(df_mes[df_mes['fluxo_limpo'] == 'entrada'][col_valor].sum()))
    m2.metric("💸 Saídas Mês", formatar_brl(df_mes[df_mes['fluxo_limpo'] == 'saída'][col_valor].sum()))
    m3.metric("📊 Res. Líquido Mês", formatar_brl(df_mes[df_mes['fluxo_limpo'] == 'entrada'][col_valor].sum() - df_mes[df_mes['fluxo_limpo'] == 'saída'][col_valor].sum()))
    
    st.markdown("---")
    
    # Acumulado
    ent_ytd = df_ytd[df_ytd['fluxo_limpo'] == 'entrada'][col_valor].sum()
    sai_ytd = df_ytd[df_ytd['fluxo_limpo'] == 'saída'][col_valor].sum()
    st.subheader("Acumulado Estratégico (YTD)")
    c1, c2, c3 = st.columns(3)
    c1.metric("📈 Entradas YTD", formatar_brl(ent_ytd))
    c2.metric("📉 Saídas YTD", formatar_brl(sai_ytd))
    c3.metric("📊 Resultado YTD", formatar_brl(ent_ytd - sai_ytd))

elif pagina == "📈 Análise de Entradas":
    st.title("Análise de Entradas")
    df_ent = df_mes[df_mes['fluxo_limpo'] == 'entrada']
    st.plotly_chart(px.bar(df_ent.groupby(col_contato)[col_valor].sum().reset_index(), x=col_valor, y=col_contato, orientation='h'), use_container_width=True)

elif pagina == "📉 Detalhe de Saídas":
    st.title("Distribuição de Saídas")
    df_sai = df_mes[df_mes['fluxo_limpo'] == 'saída']
    st.plotly_chart(px.bar(df_sai.groupby(col_grupo)[col_valor].sum().reset_index(), x=col_valor, y=col_grupo, orientation='h'), use_container_width=True)

elif pagina == "👥 Gestão de Sócios":
    st.title("Controle de Sócios")
    st.dataframe(df_mes[df_mes[col_grupo].str.contains('SÓCIO', na=False, case=False)], use_container_width=True)

elif pagina == "🏗️ Custos na Prestação de Serviço":
    st.title("Custos na Prestação de Serviço")
    st.dataframe(df_mes[df_mes[col_grupo].str.contains('CUSTOS NA PRESTAÇÃO DE SERVIÇO', na=False, case=False)], use_container_width=True)
