import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(page_title="WL Expertise | Conectsol BI", layout="wide")

@st.cache_data
def carregar_dados():
    try:
        df = pd.read_excel('dados_conectsol.xlsx')
        df.columns = df.columns.str.strip()
        
        # Validação básica de colunas
        if len(df.columns) < 16:
            st.error("Erro: A planilha parece não ter o número esperado de colunas.")
            return None, None, None, None, None, None
            
        col_data_pag = df.columns[4]
        col_contato = df.columns[7]
        col_categoria = df.columns[10]
        col_situacao = df.columns[11]
        col_valor = df.columns[12]
        col_grupo = df.columns[13]
        col_tipo_p = df.columns[15]
        
        # Limpeza
        df['situacao_limpa'] = df[col_situacao].astype(str).str.strip().str.lower()
        df = df[df['situacao_limpa'].isin(['conciliado', 'sem conciliação'])].copy()
        
        df[col_valor] = pd.to_numeric(df[col_valor].astype(str).str.replace(r'[R$\s.]', '', regex=True).str.replace(',', '.'), errors='coerce').fillna(0)
        df[col_data_pag] = pd.to_datetime(df[col_data_pag], errors='coerce')
        df = df.dropna(subset=[col_data_pag])
        
        df['ano'] = df[col_data_pag].dt.year
        df['ano_mes_texto'] = df[col_data_pag].dt.strftime('%b/%Y').str.lower()
        
        df['tipo_p_limpo'] = df[col_tipo_p].astype(str).str.strip().str.upper()
        df['fluxo_limpo'] = 'outros'
        df.loc[df['tipo_p_limpo'] == 'VENDA', 'fluxo_limpo'] = 'entrada'
        df.loc[df['tipo_p_limpo'].isin(['CUSTO', 'DESPESA']), 'fluxo_limpo'] = 'saída'
        
        return df, col_data_pag, col_contato, col_categoria, col_valor, col_grupo
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None, None, None, None, None, None

df_base, col_data_pag, col_contato, col_categoria, col_valor, col_grupo = carregar_dados()

if df_base is not None:
    st.sidebar.image("Logohorizontal.png", use_container_width=True)
    pagina = st.sidebar.radio("Navegação:", ["🚀 Visão Geral (YTD)", "📈 Análise de Entradas", "📉 Detalhe de Saídas", "👥 Gestão de Sócios", "🏗️ Custos na Prestação de Serviço"])
    
    meses = df_base.sort_values(col_data_pag)['ano_mes_texto'].unique().tolist()
    mes_selecionado = st.sidebar.selectbox("Mês:", meses, index=len(meses)-1)
    
    # Restante do seu código vai aqui...
    st.write(f"Você está na página: {pagina}")
    st.write(f"Mês selecionado: {mes_selecionado}")
else:
    st.warning("Não foi possível carregar os dados. Verifique o arquivo Excel.")
