import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURAÇÃO DA PÁGINA (Deve ser o primeiro comando Streamlit)
st.set_page_config(
    page_title="Painel Financeiro - Conectsol Engenharia",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilização CSS para o tema escuro/azul escuro conforme o seu modelo
st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    h1, h2, h3 { color: #f1f1f1; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    .stCard {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. CARREGAMENTO E TRATAMENTO DOS DADOS
@st.cache_data
def carregar_dados():
    # Substitua 'seu_arquivo.xlsx' pelo nome real do seu arquivo caso não use os dados embutidos
    # Exemplo: df = pd.read_excel('dados_financeiros.xlsx')
    
    # Simulando a estrutura real da sua base com dados até Abril para o funcionamento correto:
    dados_exemplo = {
        'Data de Pagamento': pd.date_range(start='2026-01-01', end='2026-04-30', freq='D').tolist() * 3,
        'Situação': ['Conciliado'] * 100 + ['Aberto'] * 20,
        'Tipo': ['Receita', 'Despesa', 'Despesa'] * 40,
        'Valor': [1500, 500, 300] * 40,
        'Categoria': ['Vendas', 'Administrativo', 'Pessoal'] * 40,
        'Fornecedor/Cliente': ['Moinho Dois Irmãos', 'Santa Rosa Alimentos', 'Carla Ferreira'] * 40,
        'Equipe Vendas': ['Varejo', 'Online', 'Distribuidoras'] * 40
    }
    df = pd.DataFrame(dados_exemplo)
    
    # Garantindo que a Coluna E (Data de Pagamento) está no formato de data correto
    df['Data de Pagamento'] = pd.to_datetime(df['Data de Pagamento'])
    
    # REGRA 2: Considerar APENAS o que tiver Situação == 'Conciliado'
    df = df[df['Situação'].str.lower() == 'conciliado']
    
    # REGRA 1: Criar o Mês de Competência baseado estritamente na Data de Pagamento
    # Criamos uma coluna de texto amigável e uma para ordenação
    df['Mês_Nome'] = df['Data de Pagamento'].dt.strftime('%b').str.lower()
    df['Mês_Num'] = df['Data de Pagamento'].dt.month
    
    return df

try:
    df_base = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar a base de dados: {e}")
    st.stop()

# 3. CABEÇALHO COM LOGO
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    try:
        st.image("Logo horizontal-fundo.png", width=200)
    except:
        st.write("📂 **Conectsol Engenharia**")

with col_titulo:
    st.title("Painel Financeiro & Business Intelligence")
    st.subheader("Análise de Resultado de Caixa")

st.markdown("---")

# 4. FILTRO DE MÊS (Mês de Competência baseado em Pagamento)
# Mapeamento para exibição amigável e ordenada
meses_map = {1: 'jan', 2: 'fev', 3: 'mar', 4: 'abr', 5: 'mai', 6: 'jun', 
             7: 'jul', 8: 'ago', 9: 'set', 10: 'out', 11: 'nov', 12: 'dez'}

# Descobre quais meses realmente existem na base após o filtro de conciliados
meses_existentes_num = sorted(df_base['Mês_Num'].unique())
meses_existentes_nome = [meses_map[m] for m in meses_existentes_num]

# Seletor horizontal no topo para os meses
mes_selecionado_nome = st.radio(
    "Mês de Competência (Data de Pagamento):",
    options=meses_existentes_nome,
    horizontal=True
)

# Filtrando o dataframe final com base no mês selecionado
df_filtrado = df_base[df_base['Mês_Nome'] == mes_selecionado_nome]

# 5. CÁLCULO DOS INDICADORES (KPIs)
receitas = df_filtrado[df_filtrado['Tipo'].str.lower() == 'receita']['Valor'].sum()
despesas = df_filtrado[df_filtrado['Tipo'].str.lower() == 'despesa']['Valor'].sum()
lucro_liquido = receitas - despesas
margem_lucro = (lucro_liquido / receitas * 100) if receitas > 0 else 0

# Exibição dos Cards Principais
kpi1, kpi2, kpi3 = st.columns(3)
with kpi1:
    st.markdown(f"""
    <div class="stCard">
        <h3 style='color: #ef4444; margin:0;'>📉 Despesas</h3>
        <h2 style='margin:10px 0 0 0;'>R$ {despesas:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="stCard">
        <h3 style='color: #10b981; margin:0;'>📈 Receitas</h3>
        <h2 style='margin:10px 0 0 0;'>R$ {receitas:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div class="stCard">
        <h3 style='color: #3b82f6; margin:0;'>📊 Lucro Líquido (Margem)</h3>
        <h2 style='margin:10px 0 0 0;'>R$ {lucro_liquido:,.2f} <span style='font-size:16px; color:#94a3b8;'>({margem_lucro:.1f}%)</span></h2>
    </div>
    """, unsafe_allow_html=True)

# 6. GRÁFICOS DO DASHBOARD
graf1, graf2 = st.columns(2)

with graf1:
    st.markdown("### Despesa por Categoria")
    df_desp_cat = df_filtrado[df_filtrado['Tipo'].str.lower() == 'despesa'].groupby('Categoria')['Valor'].sum().reset_index()
    if not df_desp_cat.empty:
        fig_desp = px.pie(df_desp_cat, values='Valor', names='Categoria', hole=0.4,
                          color_discrete_sequence=px.colors.sequential.Reds_r)
        fig_desp.update_layout(margin=dict(t=20, b=20, l=20, r=20), template="plotly_dark")
        st.plotly_chart(fig_desp, use_container_width=True)
    else:
        st.info("Nenhuma despesa registrada para este período.")

with graf2:
    st.markdown("### Análise por Equipe de Vendas")
    df_vendas = df_filtrado[df_filtrado['Tipo'].str.lower() == 'receita'].groupby('Equipe Vendas')['Valor'].sum().reset_index()
    if not df_vendas.empty:
        fig_vendas = px.bar(df_vendas, x='Equipe Vendas', y='Valor', 
                            color='Valor', color_continuous_scale='Viridis')
        fig_vendas.update_layout(margin=dict(t=20, b=20, l=20, r=20), template="plotly_dark")
        st.plotly_chart(fig_vendas, use_container_width=True)
    else:
        st.info("Nenhuma receita registrada para este período.")
