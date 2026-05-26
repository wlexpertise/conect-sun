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
    
    # Remove espaços extras invisíveis nas pontas dos nomes das colunas
    df.columns = df.columns.str.strip()
    
    # 🔒 TRAVA DEFINITIVA: Nomes exatos extraídos da sua planilha original
    col_data_e = 'Data Pagamento'
    col_valor_m = 'Valor'
    col_grupos_n = 'Grupos'
    col_tipo_p = 'Tipo'
    col_situacao = 'Situação'
    col_vendedor = 'Vendedor'

    # LIMPEZA: Remove linhas onde a Data de Pagamento ou Tipo estão completamente vazios
    df = df.dropna(subset=[col_data_e, col_tipo_p])
    
    # Converte a coluna para data de forma segura, ignorando textos inválidos
    df[col_data_e] = pd.to_datetime(df[col_data_e], errors='coerce')
    df = df.dropna(subset=[col_data_e]) 
    
    # Filtra anos realistas para eliminar o ano fantasma de 1970
    df = df[df[col_data_e].dt.year >= 2020]
    
    # REGRA GERAL: Considerar apenas o que estiver 'Conciliado'
    df = df[df[col_situacao].astype(str).str.lower().str.strip().str.contains('conciliado', na=False)]
    
    # Criação das colunas de período no padrão mmm/yyyy para o menu suspenso
    df['ano_mes_num'] = df[col_data_e].dt.strftime('%Y%m')
    
    meses_pt = {1: 'jan', 2: 'fev', 3: 'mar', 4: 'abr', 5: 'mai', 6: 'jun',
                7: 'jul', 8: 'ago', 9: 'set', 10: 'out', 11: 'nov', 12: 'dez'}
    
    df['mes_nome_pt'] = df[col_data_e].dt.month.map(meses_pt)
    df['ano_mes_texto'] = df['mes_nome_pt'] + '/' + df[col_data_e].dt.year.astype(str)
    
    return df, col_data_e, col_valor_m, col_grupos_n, col_tipo_p, col_vendedor

try:
    df_base, col_data_e, col_valor_m, col_grupos_n, col_tipo_p, col_vendedor = carregar_dados()
except Exception as e:
    st.error(f"Erro crítico ao ler as colunas: {e}")
    st.info("Verifique se os nomes das colunas na sua planilha mudaram recentemente.")
    st.stop()

# 3. BARRA LATERAL (MENU SUSPENSO)
st.sidebar.image("Logo horizontal-fundo.png", use_container_width=True)
st.sidebar.markdown("### FILTROS DE ANÁLISE")

# Ordenação cronológica dos meses válidos
df_ordenado = df_base.sort_values('ano_mes_num')
meses_disponiveis = df_ordenado['ano_mes_texto'].unique().tolist()

if meses_disponiveis:
    mes_selecionado = st.sidebar.selectbox(
        "Selecione o Mês de Competência:",
        options=meses_disponiveis
    )
    df_filtrado = df_base[df_base['ano_mes_texto'] == mes_selecionado].copy()
else:
    st.warning("Nenhum dado válido com a situação 'Conciliado' foi encontrado na planilha.")
    st.stop()


# 4. CABEÇALHO DO DASHBOARD
st.title("Painel Financeiro & Business Intelligence")
st.markdown(f"#### Análise de Resultado de Caixa: **Conectsol Engenharia** | Período: `{mes_selecionado.upper()}`")
st.markdown("---")


# 5. PROCESSAMENTO DE ENTRADAS E SAÍDAS
df_filtrado['tipo_busca'] = df_filtrado[col_tipo_p].astype(str).str.lower().str.strip()

# REGRA: Entrada = apenas o que for exatamente 'venda'
df_entradas = df_filtrado[df_filtrado['tipo_busca'] == 'venda']
entradas_total = pd.to_numeric(df_entradas[col_valor_m], errors='coerce').sum()

# REGRA: Saída = o que contiver 'custo' ou 'despes'
df_saidas = df_filtrado[df_filtrado['tipo_busca'].str.contains('custo|despes|despesa', na=False)]
saidas_total = pd.to_numeric(df_saidas[col_valor_m], errors='coerce').sum()

# Resultado Líquido e Margem
resultado_liquido = entradas_total - saidas_total
margem_resultado = (resultado_liquido / entradas_total * 100) if entradas_total > 0 else 0


# 6. EXIBIÇÃO DOS CARDS (Entradas, Saídas, Resultado)
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric(label="📈 Total de Entradas (Vendas)", value=f"R$ {entradas_total:,.2f}")
kpi2.metric(label="📉 Total de Saídas (Custos/Despesas)", value=f"R$ {saidas_total:,.2f}")
kpi3.metric(label="📊 Resultado Líquido", value=f"R$ {resultado_liquido:,.2f}", delta=f"{margem_resultado:.1f}% Margem")

st.markdown("---")


# 7. GRÁFICOS DO DASHBOARD
graf1, graf2 = st.columns(2)

with graf1:
    st.markdown("### 🍕 Saídas por Grupo")
    df_saidas_grupo = df_saidas.groupby(col_grupos_n)[col_valor_m].sum().reset_index()
    df_saidas_grupo[col_valor_m] = pd.to_numeric(df_saidas_grupo[col_valor_m], errors='coerce')
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
        st.info("Nenhuma saída registrada para este mês.")

with graf2:
    st.markdown("### 📊 Desempenho de Entradas por Vendedor")
    df_vendas = df_entradas.groupby(col_vendedor)[col_valor_m].sum().reset_index()
    df_vendas[col_valor_m] = pd.to_numeric(df_vendas[col_valor_m], errors='coerce')
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
        st.info("Nenhuma entrada (venda) registrada para este mês.")
