import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURAÇÃO DA PÁGINA (Layout limpo e moderno)
st.set_page_config(
    page_title="Painel Financeiro - Conectsol Engenharia",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. CARREGAMENTO E TRATAMENTO DOS DADOS REAIS
@st.cache_data
def carregar_dados():
    nome_do_arquivo = 'dados_conectsol.xlsx' 
    df = pd.read_excel(nome_do_arquivo)
    
    # Padroniza o nome das colunas
    df.columns = df.columns.str.strip().str.lower()
    
    # Mapeamento automático de colunas vitais
    col_data = [c for c in df.columns if 'pagamento' in c][0]
    col_situacao = [c for c in df.columns if 'situa' in c][0]
    
    # REGRA: Remover linhas sem data e converter para datetime
    df = df.dropna(subset=[col_data])
    df[col_data] = pd.to_datetime(df[col_data])
    
    # REGRA: Filtrar APENAS o que tiver Situação == 'Conciliado'
    df = df[df[col_situacao].astype(str).str.lower().str.strip() == 'conciliado']
    
    # Criação da coluna de filtro no padrão mmm/yyyy (ex: jan/2026)
    # Primeiro criamos chaves de ordenação para não Bagunçar os meses no menu
    df['ano_mes_num'] = df[col_data].dt.strftime('%Y%m')
    
    # Dicionário para forçar o português nos meses abreviados
    meses_pt = {1: 'jan', 2: 'fev', 3: 'mar', 4: 'abr', 5: 'mai', 6: 'jun',
                7: 'jul', 8: 'ago', 9: 'set', 10: 'out', 11: 'nov', 12: 'dez'}
    
    df['mes_nome_pt'] = df[col_data].dt.month.map(meses_pt)
    df['ano_mes_texto'] = df['mes_nome_pt'] + '/' + df[col_data].dt.year.astype(str)
    
    return df, col_data

try:
    df_base, col_data_real = carregar_dados()
except Exception as e:
    st.error(f"Erro ao processar o arquivo 'dados_conectsol.xlsx': {e}")
    st.stop()

# 3. BARRA LATERAL (MENU SUSPENSO)
st.sidebar.image("Logo horizontal-fundo.png", use_container_width=True)
st.sidebar.markdown("### FILTROS DE ANÁLISE")

# Ordena os meses corretamente pela data (cronológico)
df_ordenado = df_base.sort_values('ano_mes_num')
meses_disponiveis = df_ordenado['ano_mes_texto'].unique().tolist()

if meses_disponiveis:
    # Menu suspenso conforme solicitado
    mes_selecionado = st.sidebar.selectbox(
        "Selecione o Mês de Competência:",
        options=meses_disponiveis
    )
    # Filtrando a base pelo mês escolhido no dropdown
    df_filtrado = df_base[df_base['ano_mes_texto'] == mes_selecionado]
else:
    st.warning("Nenhum dado com a situação 'Conciliado' foi encontrado na planilha.")
    st.stop()


# 4. CABEÇALHO DO DASHBOARD
st.title("Painel Financeiro & Business Intelligence")
st.markdown(f"#### Análise de Resultado de Caixa: **Conectsol Engenharia** | Período: `{mes_selecionado.upper()}`")
st.markdown("---")


# 5. IDENTIFICAÇÃO DINÂMICA DE VALORES E TIPOS
col_tipo = [c for c in df_filtrado.columns if 'tipo' in c or 'movimenta' in c or 'd/c' in c][0]
col_valor = [c for c in df_filtrado.columns if 'valor' in c or 'lançamento' in c][0]

receitas = df_filtrado[df_filtrado[col_tipo].astype(str).str.lower().str.strip().str.contains('receita|cédito|c|entrada')][col_valor].sum()
despesas = df_filtrado[df_filtrado[col_tipo].astype(str).str.lower().str.strip().str.contains('despesa|débito|d|saída')][col_valor].sum()
lucro_liquido = receitas - despesas
margem_lucro = (lucro_liquido / receitas * 100) if receitas > 0 else 0


# 6. EXIBIÇÃO DOS CARDS (Indicadores Nativos de Alto Contraste)
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric(label="📉 Total de Despesas", value=f"R$ {despesas:,.2f}")
kpi2.metric(label="📈 Total de Receitas", value=f"R$ {receitas:,.2f}")
kpi3.metric(label="📊 Lucro Líquido (Margem %)", value=f"R$ {lucro_liquido:,.2f}", delta=f"{margem_lucro:.1f}% Margem")

st.markdown("---")


# 7. GRÁFICOS DO DASHBOARD (Temas limpos e legíveis)
graf1, graf2 = st.columns(2)

with graf1:
    st.markdown("### 🍕 Despesa por Categoria")
    col_cat_list = [c for c in df_filtrado.columns if 'categoria' in c or 'classifica' in c or 'descrição' in c]
    col_cat = col_cat_list[0] if col_cat_list else df_filtrado.columns[0]
    
    df_desp_cat = df_filtrado[df_filtrado[col_tipo].astype(str).str.lower().str.strip().str.contains('despesa|débito|d|saída')].groupby(col_cat)[col_valor].sum().reset_index()
    
    if not df_desp_cat.empty:
        fig_desp = px.pie(
            df_desp_cat, 
            values=col_valor, 
            names=col_cat, 
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_desp.update_layout(legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig_desp, use_container_width=True)
    else:
        st.info("Nenhuma despesa registrada para este período.")

with graf2:
    st.markdown("### 📊 Desempenho por Equipe de Vendas")
    col_equipe_list = [c for c in df_filtrado.columns if 'equipe' in c or 'vendedor' in c or 'consultor' in c]
    
    if col_equipe_list:
        col_equipe = col_equipe_list[0]
        df_vendas = df_filtrado[df_filtrado[col_tipo].astype(str).str.lower().str.strip().str.contains('receita|cédito|c|entrada')].groupby(col_equipe)[col_valor].sum().reset_index()
        
        if not df_vendas.empty:
            fig_vendas = px.bar(
                df_vendas, 
                x=col_equipe, 
                y=col_valor, 
                text_auto='.2s',
                color=col_valor,
                color_continuous_scale='Blugrn'
            )
            st.plotly_chart(fig_vendas, use_container_width=True)
        else:
            st.info("Nenhuma receita registrada para este período.")
    else:
        st.info("Coluna de Equipe/Vendedor não localizada na sua planilha.")
