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

# 2. CARREGAMENTO E TRATAMENTO DOS DADOS BASEADO NO SEU ARQUIVO REAL
@st.cache_data
def carregar_dados():
    nome_do_arquivo = 'dados_conectsol.xlsx' 
    df = pd.read_excel(nome_do_arquivo)
    
    # Força a limpeza de nomes das colunas (remove espaços invisíveis nas pontas)
    df.columns = df.columns.str.strip()
    
    # MAPEAMENTO MANUAL BASEADO NA ESTRUTURA REAL FORNECIDA:
    # Cabeçalhos: Banco | Conta bancária | Tipo | Data de emissão | Data de pagamento | ... | Contato | ... | Situação | Valor | Grupo | Instituição | Tipo | Mês | Tri
    
    # Como existem duas colunas chamadas 'Tipo', o pandas renomeia a segunda para 'Tipo.1'. 
    # Vamos criar apelidos fixos baseados na posição real delas para não haver erro:
    col_tipo_fluxo = df.columns[2]     # 3ª coluna: 'Tipo' (Entrada / Saída)
    col_data_pag = df.columns[4]       # 5ª coluna: 'Data de pagamento'
    col_contato = df.columns[7]        # 8ª coluna: 'Contato'
    col_situacao = df.columns[11]      # 12ª coluna: 'Situação' (Conciliado)
    col_valor = df.columns[12]         # 13ª coluna: 'Valor'
    col_grupo = df.columns[13]         # 14ª coluna: 'Grupo' (DESPESA COM PESSOAL, SERVIÇOS, etc.)
    
    # 🧼 TRATAMENTO DE LIMPEZA PROFUNDA
    
    # 1. Filtrar apenas o que está 'Conciliado' (ignora "Sem conciliação")
    df = df[df[col_situacao].astype(str).str.strip().str.lower() == 'conciliado']
    
    # 2. Limpar e converter a coluna de Valor de forma agressiva
    if df[col_valor].dtype == object:
        df[col_valor] = df[col_valor].astype(str).str.replace('R$', '', regex=False)
        df[col_valor] = df[col_valor].str.replace('.', '', regex=False)
        df[col_valor] = df[col_valor].str.replace(',', '.', regex=False)
        df[col_valor] = df[col_valor].str.strip()
    df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0)
    
    # 3. Tratamento de Datas (Data de pagamento)
    df[col_data_pag] = pd.to_datetime(df[col_data_pag], errors='coerce', dayfirst=True)
    df = df.dropna(subset=[col_data_pag])
    
    # 4. Criação dos períodos para o menu (Ex: jan/2026)
    df['ano_mes_num'] = df[col_data_pag].dt.strftime('%Y%m')
    
    meses_pt = {1: 'jan', 2: 'fev', 3: 'mar', 4: 'abr', 5: 'mai', 6: 'jun',
                7: 'jul', 8: 'ago', 9: 'set', 10: 'out', 11: 'nov', 12: 'dez'}
    df['mes_nome_pt'] = df[col_data_pag].dt.month.map(meses_pt)
    df['ano_mes_texto'] = df['mes_nome_pt'] + '/' + df[col_data_pag].dt.year.astype(str)
    
    return df, col_tipo_fluxo, col_data_pag, col_contato, col_valor, col_grupo

try:
    df_base, col_tipo_fluxo, col_data_pag, col_contato, col_valor, col_grupo = carregar_dados()
except Exception as e:
    st.error(f"Erro ao processar as colunas da planilha: {e}")
    st.stop()

# 3. BARRA LATERAL (MENU FILTRO)
st.sidebar.image("Logo horizontal-fundo.png", use_container_width=True)
st.sidebar.markdown("### FILTROS DE ANÁLISE")

# Ordena os meses disponíveis cronologicamente
df_ordenado = df_base.sort_values('ano_mes_num')
meses_disponiveis = df_ordenado['ano_mes_texto'].unique().tolist()

if meses_disponiveis:
    mes_selecionado = st.sidebar.selectbox(
        "Selecione o Mês de Competência:",
        options=meses_disponiveis
    )
    df_filtrado = df_base[df_base['ano_mes_texto'] == mes_selecionado].copy()
else:
    st.warning("Nenhum dado com status 'Conciliado' e data válida foi encontrado na planilha.")
    st.stop()

# 4. CABEÇALHO DO DASHBOARD
st.title("Painel Financeiro & Business Intelligence")
st.markdown(f"#### Análise de Resultado de Caixa: **Conectsol Engenharia** | Período: `{mes_selecionado.upper()}`")
st.markdown("---")

# 5. CÁLCULO DE ENTRADAS E SAÍDAS (Baseado na 3ª coluna: Entrada / Saída)
df_filtrado['fluxo_limpo'] = df_filtrado[col_tipo_fluxo].astype(str).str.strip().str.lower()

df_entradas = df_filtrado[df_filtrado['fluxo_limpo'] == 'entrada']
entradas_total = df_entradas[col_valor].sum()

df_saidas = df_filtrado[df_filtrado['fluxo_limpo'] == 'saída']
saidas_total = df_saidas[col_valor].sum()

resultado_liquido = entradas_total - saidas_total
margem_resultado = (resultado_liquido / entradas_total * 100) if entradas_total > 0 else 0

# 6. CARD PRINCIPAIS
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric(label="📈 Total de Entradas", value=f"R$ {entradas_total:,.2f}")
kpi2.metric(label="📉 Total de Saídas", value=f"R$ {saidas_total:,.2f}")
kpi3.metric(label="📊 Resultado Líquido", value=f"R$ {resultado_liquido:,.2f}", delta=f"{margem_resultado:.1f}% Margem")

st.markdown("---")

# 7. GRÁFICOS DO DASHBOARD
graf1, graf2 = st.columns(2)

with graf1:
    st.markdown("### 🍕 Saídas por Categoria / Grupo")
    df_saidas_grupo = df_saidas.groupby(col_grupo)[col_valor].sum().reset_index()
    df_saidas_grupo = df_saidas_grupo[df_saidas_grupo[col_valor] > 0]
    
    if not df_saidas_grupo.empty:
        fig_desp = px.pie(
            df_saidas_grupo, 
            values=col_valor, 
            names=col_grupo, 
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_desp.update_layout(legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig_desp, use_container_width=True)
    else:
        st.info("Nenhuma saída conciliada para este período.")

with graf2:
    st.markdown("### 📊 Maiores Entradas por Contato/Cliente")
    df_vendas = df_entradas.groupby(col_contato)[col_valor].sum().reset_index()
    df_vendas = df_vendas[df_vendas[col_valor] > 0].sort_values(by=col_valor, ascending=False).head(10)
    
    if not df_vendas.empty:
        fig_vendas = px.bar(
            df_vendas, 
            x=col_contato, 
            y=col_valor, 
            text_auto='.2s',
            color=col_valor,
            color_continuous_scale='Blugrn',
            labels={col_contato: 'Cliente / Origem', col_valor: 'Valor (R$)'}
        )
        st.plotly_chart(fig_vendas, use_container_width=True)
    else:
        st.info("Nenhuma entrada conciliada para este período.")
