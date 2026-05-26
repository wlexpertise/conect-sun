import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURAÇÃO DA PÁGINA
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
    
    # Limpa espaços em branco dos nomes das colunas
    df.columns = df.columns.str.strip()
    colunas_minusculas = [c.lower() for c in df.columns]
    
    # 🔍 LOCALIZAÇÃO DINÂMICA DAS COLUNAS
    try:
        idx_data = [i for i, c in enumerate(colunas_minusculas) if 'pagamento' in c or 'data' in c][0]
        col_data_e = df.columns[idx_data]
    except IndexError:
        st.error("Coluna de Data de Pagamento não encontrada. Verifique os cabeçalhos.")
        st.stop()
        
    try:
        idx_valor = [i for i, c in enumerate(colunas_minusculas) if 'valor' in c][0]
        col_valor_m = df.columns[idx_valor]
    except IndexError:
        st.error("Coluna de Valor não encontrada.")
        st.stop()
        
    idx_grupos = [i for i, c in enumerate(colunas_minusculas) if 'grupo' in c or c == 'n']
    col_grupos_n = df.columns[idx_grupos[0]] if idx_grupos else (df.columns[13] if len(df.columns) > 13 else df.columns[0])
        
    try:
        idx_tipo = [i for i, c in enumerate(colunas_minusculas) if 'tipo' in c or c == 'p'][0]
        col_tipo_p = df.columns[idx_tipo]
    except IndexError:
        st.error("Coluna de Tipo não encontrada.")
        st.stop()
        
    try:
        idx_situacao = [i for i, c in enumerate(colunas_minusculas) if 'situa' in c or 'status' in c][0]
        col_situacao = df.columns[idx_situacao]
    except IndexError:
        st.error("Coluna de Situação não encontrada.")
        st.stop()
        
    idx_vendedor = [i for i, c in enumerate(colunas_minusculas) if 'vendedor' in c or 'equipe' in c or 'consultor' in c]
    col_vendedor = df.columns[idx_vendedor[0]] if idx_vendedor else df.columns[0]

    # 🧼 HIGIENIZAÇÃO PROFUNDA DOS DADOS
    
    # 1. Trata a coluna de Tipo (Remove espaços e põe em minúsculo)
    df[col_tipo_p] = df[col_tipo_p].astype(str).str.strip().str.lower()
    
    # 2. Força a conversão do Valor tirando símbolos monetários comuns do Excel se existirem
    if df[col_valor_m].dtype == object:
        df[col_valor_m] = df[col_valor_m].astype(str).str.replace('R$', '', regex=False)
        df[col_valor_m] = df[col_valor_m].str.replace('.', '', regex=False)
        df[col_valor_m] = df[col_valor_m].str.replace(',', '.', regex=False)
        df[col_valor_m] = df[col_valor_m].str.strip()
    df[col_valor_m] = pd.to_numeric(df[col_valor_m], errors='coerce').fillna(0)
    
    # 3. Converte e limpa as Datas
    df[col_data_e] = pd.to_datetime(df[col_data_e], errors='coerce')
    df = df.dropna(subset=[col_data_e])
    df = df[df[col_data_e].dt.year >= 2020]
    
    # 4. Trata a coluna de Situação para evitar divergência de escrita
    df['sit_limpa'] = df[col_situacao].astype(str).str.strip().str.lower()
    df = df[df['sit_limpa'].str.contains('conciliado', na=False)]
    
    # Geração dos períodos
    df['ano_mes_num'] = df[col_data_e].dt.strftime('%Y%m')
    meses_pt = {1: 'jan', 2: 'fev', 3: 'mar', 4: 'abr', 5: 'mai', 6: 'jun',
                7: 'jul', 8: 'ago', 9: 'set', 10: 'out', 11: 'nov', 12: 'dez'}
    df['mes_nome_pt'] = df[col_data_e].dt.month.map(meses_pt)
    df['ano_mes_texto'] = df['mes_nome_pt'] + '/' + df[col_data_e].dt.year.astype(str)
    
    return df, col_data_e, col_valor_m, col_grupos_n, col_tipo_p, col_vendedor

try:
    df_base, col_data_e, col_valor_m, col_grupos_n, col_tipo_p, col_vendedor = carregar_dados()
except Exception as e:
    st.error(f"Erro inesperado ao tratar os dados: {e}")
    st.stop()

# 3. BARRA LATERAL
st.sidebar.image("Logo horizontal-fundo.png", use_container_width=True)
st.sidebar.markdown("### FILTROS DE ANÁLISE")

df_ordenado = df_base.sort_values('ano_mes_num')
meses_disponiveis = df_ordenado['ano_mes_texto'].unique().tolist()

if meses_disponiveis:
    mes_selecionado = st.sidebar.selectbox(
        "Selecione o Mês de Competência:",
        options=meses_disponiveis
    )
    df_filtrado = df_base[df_base['ano_mes_texto'] == mes_selecionado].copy()
else:
    st.warning("Atenção: Nenhuma linha foi encontrada com o status 'Conciliado'. Verifique a coluna de situação no Excel.")
    st.stop()

# 4. CABEÇALHO DO DASHBOARD
st.title("Painel Financeiro & Business Intelligence")
st.markdown(f"#### Análise de Resultado de Caixa: **Conectsol Engenharia** | Período: `{mes_selecionado.upper()}`")
st.markdown("---")

# 5. PROCESSAMENTO DE VALORES (MÉTODO FLEXÍVEL DE BUSCA)
# Entrada: se conter a palavra 'venda'
df_entradas = df_filtrado[df_filtrado[col_tipo_p].str.contains('venda', na=False)]
entradas_total = df_entradas[col_valor_m].sum()

# Saída: se conter 'custo' ou 'despes'
df_saidas = df_filtrado[df_filtrado[col_tipo_p].str.contains('custo|despes', na=False)]
saidas_total = df_saidas[col_valor_m].sum()

resultado_liquido = entradas_total - saidas_total
margem_resultado = (resultado_liquido / entradas_total * 100) if entradas_total > 0 else 0

# 6. EXIBIÇÃO DOS CARDS
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric(label="📈 Total de Entradas", value=f"R$ {entradas_total:,.2f}")
kpi2.metric(label="📉 Total de Saídas", value=f"R$ {saidas_total:,.2f}")
kpi3.metric(label="📊 Resultado Líquido", value=f"R$ {resultado_liquido:,.2f}", delta=f"{margem_resultado:.1f}% Margem")

st.markdown("---")

# 7. GRÁFICOS DO DASHBOARD
graf1, graf2 = st.columns(2)

with graf1:
    st.markdown("### 🍕 Saídas por Grupo")
    df_saidas_grupo = df_saidas.groupby(col_grupos_n)[col_valor_m].sum().reset_index()
    df_saidas_grupo = df_saidas_grupo[df_saidas_grupo[col_valor_m] > 0]
    
    if not df_saidas_grupo.empty:
        fig_desp = px.pie(
            df_saidas_grupo, 
            values=col_valor_m, 
            names=col_grupos_n, 
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_desp.update_layout(legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig_desp, use_container_width=True)
    else:
        st.info("Nenhuma saída identificada para este mês.")

with graf2:
    st.markdown("### 📊 Desempenho de Entradas por Vendedor")
    df_vendas = df_entradas.groupby(col_vendedor)[col_valor_m].sum().reset_index()
    df_vendas = df_vendas[df_vendas[col_valor_m] > 0]
    
    if not df_vendas.empty:
        fig_vendas = px.bar(
            df_vendas, 
            x=col_vendedor, 
            y=col_valor_m, 
            text_auto='.2s',
            color=col_valor_m,
            color_continuous_scale='Blugrn'
        )
        st.plotly_chart(fig_vendas, use_container_width=True)
    else:
        st.info("Nenhuma entrada registrada para este mês.")
