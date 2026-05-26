import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuração e Estilos (O SEU LAYOUT ORIGINAL)
st.set_page_config(page_title="WL Expertise | Conectsol BI", layout="wide", initial_sidebar_state="expanded")
st.markdown("""<style>.stApp { background-color: #f3f4f6 !important; } .logo-box { background-color: #ffffff; padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); text-align: center; margin-bottom: 10px; }</style>""", unsafe_allow_html=True)

# Função de carga sem filtros restritivos globais
@st.cache_data
def carregar_dados():
    df = pd.read_excel('dados_conectsol.xlsx')
    df.columns = df.columns.str.strip()
    
    # Tratamento básico de colunas
    df['valor_num'] = pd.to_numeric(df.iloc[:, 12].astype(str).str.replace(r'[R$\s.]', '', regex=True).str.replace(',', '.'), errors='coerce').fillna(0)
    df['data_pag'] = pd.to_datetime(df.iloc[:, 4], errors='coerce', dayfirst=True)
    
    # Criar colunas auxiliares sem filtrar o DF original
    df['ano_mes_texto'] = df['data_pag'].dt.strftime('%b/%Y').str.lower()
    df['grupo_limpo'] = df.iloc[:, 13].astype(str).str.upper()
    df['fluxo'] = 'ignorar'
    df.loc[df.iloc[:, 15].astype(str).str.upper() == 'VENDA', 'fluxo'] = 'entrada'
    df.loc[df.iloc[:, 15].astype(str).str.upper().isin(['CUSTO', 'DESPESA']), 'fluxo'] = 'saída'
    
    return df

df = carregar_dados()

# Sidebar
st.sidebar.image("Logohorizontal.png", use_container_width=True)
pagina = st.sidebar.radio("Navegação:", ["🚀 Visão Geral (YTD)", "📈 Análise de Entradas", "📉 Detalhe de Saídas", "👥 Gestão de Sócios", "🏗️ Custos na Prestação de Serviço"])
meses = df['ano_mes_texto'].unique().tolist()
mes_selecionado = st.sidebar.selectbox("Mês:", meses, index=len(meses)-1)

# Filtro local (apenas para a página atual)
df_mes = df[df['ano_mes_texto'] == mes_selecionado]

# Renderização
if pagina == "🚀 Visão Geral (YTD)":
    st.title("Performance Financeira")
    ent = df_mes[df_mes['fluxo'] == 'entrada']['valor_num'].sum()
    sai = df_mes[df_mes['fluxo'] == 'saída']['valor_num'].sum()
    m1, m2, m3 = st.columns(3)
    m1.metric("Entradas", f"R$ {ent:,.2f}")
    m2.metric("Saídas", f"R$ {sai:,.2f}")
    m3.metric("Resultado", f"R$ {ent-sai:,.2f}")

elif pagina == "👥 Gestão de Sócios":
    st.title("Gestão de Sócios")
    st.dataframe(df_mes[df_mes['grupo_limpo'].str.contains('SÓCIO', na=False)])

# (Adicione os outros elifs aqui...)
