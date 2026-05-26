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
    
    # Padroniza o nome das colunas originais (letras minúsculas e sem espaços nas pontas)
    df.columns = df.columns.str.strip().str.lower()
    
    # Mapeamento dinâmico de colunas essenciais por aproximação de nome
    col_data = [c for c in df.columns if 'pagamento' in c][0]
    col_situacao = [c for c in df.columns if 'situa' in c][0]
    
    # Mapeamento específico da Coluna P (Tipo) e Coluna N (Grupos) solicitadas
    col_tipo_p = [c for c in df.columns if 'tipo' in c][0] # Coluna P
    col_grupos_n = [c for c in df.columns if 'grupo' in c][0] # Coluna N
    
    # REGRA: Remover linhas sem data e converter para datetime
    df = df.dropna(subset=[col_data])
    df[col_data] = pd.to_datetime(df[col_data])
    
    # REGRA: Filtrar APENAS o que tiver Situação == 'Conciliado'
    df = df[df[col_situacao].astype(str).str.lower().str.strip() == 'conciliado']
    
    # Criar colunas de período no padrão mmm/yyyy para o menu suspenso
    df['ano_mes_num'] = df[col_data].dt.strftime('%Y%m')
    
    meses_pt = {1: 'jan', 2: 'fev', 3: 'mar', 4: 'abr', 5: 'mai', 6: 'jun',
                7: 'jul', 8: 'ago', 9: 'set', 10: 'out', 11: 'nov', 12: 'dez'}
    
    df['mes_nome_pt'] = df[col_data].dt.month.map(meses_pt)
    df['ano_mes_texto'] = df['mes_nome_pt'] + '/' + df[col_data].dt.year.astype(str)
    
    return df, col_data, col_tipo_p, col_grupos_n

try:
    df_base, col_data_real, col_tipo_p, col_grupos_n = carregar_dados()
except Exception as e:
    st.error(f"Erro ao processar o arquivo 'dados_conectsol.xlsx': {e}")
    st.info("Verifique se as colunas de data, situação, tipo e grupos existem na sua planilha.")
    st.stop()

# 3. BARRA LATERAL (MENU SUSPENSO)
st.sidebar.image("Logo horizontal-fundo.png", use_container_width=True)
st.sidebar.markdown("### FILTROS DE ANÁLISE")

# Garante a ordenação dos meses de forma estritamente cronológica
df_ordenado = df_base.sort_values('ano_mes_num')
meses_disponiveis = df_ordenado['ano_mes_texto'].unique().tolist()

if meses_disponiveis:
    mes_selecionado = st.sidebar.selectbox(
        "Selecione o Mês de Competência:",
        options=meses_disponiveis
    )
    df_filtrado = df_base[df_base['ano_mes_texto'] == mes_selecionado]
else:
    st.warning("Nenhum dado com a situação 'Conciliado' foi encontrado na planilha.")
    st.stop()


# 4. CABEÇALHO DO DASHBOARD
st.title("Painel Financeiro & Business Intelligence")
st.markdown(f"#### Análise de Resultado de Caixa: **Conectsol Engenharia** | Período: `{mes_selecionado.upper()}`")
st.markdown("---")


# 5. LÓGICA DE FILTRAGEM RESTRITA POR TIPO (COLUNA P) E VALOR
col_valor = [c for c in df_filtrado.columns if 'valor' in c or 'lançamento' in c][0]

# Tratamento do texto da Coluna P para busca estrita
df_filtrado['tipo_tratado'] = df_filtrado[col_tipo_p].astype(str).str.lower().str.strip()

# REGRA: Entrada = apenas 'venda'
df_entradas = df_filtrado[df_filtrado['tipo_tratado'] == 'venda']
entradas_total = df_entradas[col_valor].sum()

# REGRA: Saídas = apenas o que contiver 'custo' ou 'despes' (despesa / despesas)
df_saidas = df_filtrado[df_filtrado['tipo_tratado'].str.contains('custo|despes', na=False)]
saidas_total = df_saidas[col_valor].sum()

# Resultado Líquido
resultado_liquido = entradas_total - saidas_total
margem_resultado = (resultado_liquido / entradas_total * 100) if entradas_total > 0 else 0


# 6. EXIBIÇÃO DOS CARDS REORDENADOS E RENOMEADOS
kpi1, kpi2, kpi3 = st.columns(3)
# 1º Card: Entradas
kpi1.metric(label="📈 Total de Entradas", value=f"R$ {entradas_total:,.2f}")
# 2º Card: Saídas
kpi2.metric(label="📉 Total de Saídas", value=f"R$ {saidas_total:,.2f}")
# 3º Card: Resultado Líquido
kpi3.metric(label="📊 Resultado Líquido", value=f"R$ {resultado_liquido:,.2f}", delta=f"{margem_resultado:.1f}% Margem")

st.markdown("---")


# 7. GRÁFICOS DO DASHBOARD
graf1, graf2 = st.columns(2)

with graf1:
    st.markdown("### 🍕 Saídas por Grupo (Coluna N)")
    
    # Agrupamento estrito pela coluna N (Grupos) usando apenas a base filtrada de Saídas
    df_saidas_grupo = df_saidas.groupby(col_grupos_n)[col_valor].sum().reset_index()
    
    # Remove eventuais valores zerados ou vazios que possam poluir o gráfico
    df_saidas_grupo = df_saidas_grupo[df_saidas_grupo[col_valor] > 0]
    
    if not df_saidas_grupo.empty:
        fig_desp = px.pie(
            df_saidas_grupo, 
            values=col_valor, 
            names=col_grupos_n, 
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_desp.update_layout(legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig_desp, use_container_width=True)
    else:
        st.info("Nenhuma saída registrada para este período baseado nos filtros estabelecidos.")

with graf2:
    st.markdown("### 📊 Desempenho de Entradas por Vendedor")
    # Busca colunas relacionadas a vendas/equipe para segmentar as Entradas
    col_equipe_list = [c for c in df_filtrado.columns if 'equipe' in c or 'vendedor' in c or 'consultor' in c]
    
    if col_equipe_list:
        col_equipe = col_equipe_list[0]
        # Agrupamento usando apenas a base filtrada de Entradas (Vendas)
        df_vendas = df_entradas.groupby(col_equipe)[col_valor].sum().reset_index()
        df_vendas = df_vendas[df_vendas[col_valor] > 0]
        
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
            st.info("Nenhuma entrada (venda) registrada para este período.")
    else:
        st.info("Coluna de Equipe/Vendedor não localizada na sua planilha.")
