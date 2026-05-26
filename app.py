import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Painel Financeiro - Conectsol Engenharia",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilização CSS para o tema escuro
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

# 2. CARREGAMENTO E TRATAMENTO DOS DADOS REAIS
@st.cache_data
def carregar_dados():
    # Definição do seu arquivo real
    nome_do_arquivo = 'dados_conectsol.xlsx' 
    
    # Leitura do arquivo Excel
    df = pd.read_excel(nome_do_arquivo)
    
    # Padroniza o nome das colunas (remove espaços e deixa tudo em minúsculo)
    # Isso evita erros caso haja pequenas variações de acento ou maiúsculas
    df.columns = df.columns.str.strip().str.lower()
    
    # Mapeamento para encontrar as colunas dinamicamente pelos nomes prováveis
    col_data = [c for c in df.columns if 'pagamento' in c][0]
    col_situacao = [c for c in df.columns if 'situa' in c][0]
    
    # REGRA 1: Garantir que a coluna de Data de Pagamento possui valores válidos e formatados
    df = df.dropna(subset=[col_data])
    df[col_data] = pd.to_datetime(df[col_data])
    
    # REGRA 2: Filtrar APENAS o que tiver Situação == 'Conciliado'
    df = df[df[col_situacao].astype(str).str.lower().str.strip() == 'conciliado']
    
    # Criar colunas de Mês de Competência baseadas estritamente na Data de Pagamento
    df['mês_nome'] = df[col_data].dt.strftime('%b').str.lower()
    df['mês_num'] = df[col_data].dt.month
    
    # Retorna o dataframe e os nomes tratados das colunas dinâmicas
    return df, col_data

try:
    df_base, col_data_real = carregar_dados()
except Exception as e:
    st.error(f"Erro ao processar o arquivo 'dados_conectsol.xlsx': {e}")
    st.info("Verifique se o arquivo foi enviado para a raiz do GitHub com este nome exato e se as colunas 'Data de Pagamento' e 'Situação' existem nele.")
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
    st.subheader("Análise de Resultado de Caixa - Conectsol Engenharia")

st.markdown("---")

# 4. FILTRO DE MÊS (Mês de Competência baseado em Pagamento)
meses_map = {1: 'jan', 2: 'fev', 3: 'mar', 4: 'abr', 5: 'mai', 6: 'jun', 
             7: 'jul', 8: 'ago', 9: 'set', 10: 'out', 11: 'nov', 12: 'dez'}

# Identifica quais meses realmente possuem dados após o filtro de conciliados
meses_existentes_num = sorted(df_base['mês_num'].unique())
meses_existentes_nome = [meses_map[m] for m in meses_existentes_num]

if meses_existentes_nome:
    mes_selecionado_nome = st.radio(
        "Mês de Competência (Data de Pagamento):",
        options=meses_existentes_nome,
        horizontal=True
    )
    # Filtrando os dados pelo mês selecionado
    df_filtrado = df_base[df_base['mês_nome'] == mes_selecionado_nome]
else:
    st.warning("Nenhum dado com a situação 'Conciliado' foi encontrado na planilha.")
    st.stop()

# 5. IDENTIFICAÇÃO DINÂMICA DE VALORES E TIPOS
# Identifica as colunas de valores e tipos de movimentação
col_tipo = [c for c in df_filtrado.columns if 'tipo' in c or 'movimenta' in c or 'd/c' in c][0]
col_valor = [c for c in df_filtrado.columns if 'valor' in c or 'lançamento' in c][0]

receitas = df_filtrado[df_filtrado[col_tipo].astype(str).str.lower().str.strip().str.contains('receita|cédito|c|entrada')][col_valor].sum()
despesas = df_filtrado[df_filtrado[col_tipo].astype(str).str.lower().str.strip().str.contains('despesa|débito|d|saída')][col_valor].sum()
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
    # Busca colunas parecidas com categoria ou classificação
    col_cat_list = [c for c in df_filtrado.columns if 'categoria' in c or 'classifica' in c or 'descrição' in c]
    col_cat = col_cat_list[0] if col_cat_list else df_filtrado.columns[0]
    
    df_desp_cat = df_filtrado[df_filtrado[col_tipo].astype(str).str.lower().str.strip().str.contains('despesa|débito|d|saída')].groupby(col_cat)[col_valor].sum().reset_index()
    
    if not df_desp_cat.empty:
        fig_desp = px.pie(df_desp_cat, values=col_valor, names=col_cat, hole=0.4,
                          color_discrete_sequence=px.colors.sequential.Reds_r)
        fig_desp.update_layout(margin=dict(t=20, b=20, l=20, r=20), template="plotly_dark")
        st.plotly_chart(fig_desp, use_container_width=True)
    else:
        st.info("Nenhuma despesa registrada para este período.")

with graf2:
    st.markdown("### Análise por Equipe de Vendas / Vendedor")
    # Busca colunas parecidas com vendedor ou equipe
    col_equipe_list = [c for c in df_filtrado.columns if 'equipe' in c or 'vendedor' in c or 'consultor' in c]
    
    if col_equipe_list:
        col_equipe = col_equipe_list[0]
        df_vendas = df_filtrado[df_filtrado[col_tipo].astype(str).str.lower().str.strip().str.contains('receita|cédito|c|entrada')].groupby(col_equipe)[col_valor].sum().reset_index()
        if not df_vendas.empty:
            fig_vendas = px.bar(df_vendas, x=col_equipe, y=col_valor, 
                                color=col_valor, color_continuous_scale='Viridis')
            fig_vendas.update_layout(margin=dict(t=20, b=20, l=20, r=20), template="plotly_dark")
            st.plotly_chart(fig_vendas, use_container_width=True)
        else:
            st.info("Nenhuma receita registrada para este período.")
    else:
        st.info("Coluna de Equipe/Vendedor não identificada na planilha para gerar o gráfico.")
