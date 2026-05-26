import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="WL Expertise | Conectsol BI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. CARREGAMENTO E TRATAMENTO DOS DADOS
@st.cache_data
def carregar_dados():
    nome_do_arquivo = 'dados_conectsol.xlsx' 
    df = pd.read_excel(nome_do_arquivo)
    df.columns = df.columns.str.strip()
    
    # Mapeamento por posição real
    col_tipo_fluxo = df.columns[2]     # Tipo (Entrada/Saída)
    col_data_pag = df.columns[4]       # Data de pagamento (E)
    col_contato = df.columns[7]        # Contato (H) - Sócios/Clientes
    col_categoria = df.columns[10]     # Categoria
    col_situacao = df.columns[11]      # Situação
    col_valor = df.columns[12]         # Valor (M)
    col_grupo = df.columns[13]         # Grupo (N)
    
    # Higienização
    df = df[df[col_situacao].astype(str).str.strip().str.lower() == 'conciliado'].copy()
    if df[col_valor].dtype == object:
        df[col_valor] = df[col_valor].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
    df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0)
    df[col_data_pag] = pd.to_datetime(df[col_data_pag], errors='coerce', dayfirst=True)
    df = df.dropna(subset=[col_data_pag])
    
    # Períodos
    df['ano'] = df[col_data_pag].dt.year
    df['mes'] = df[col_data_pag].dt.month
    df['ano_mes_num'] = df[col_data_pag].dt.strftime('%Y%m')
    meses_pt = {1: 'jan', 2: 'fev', 3: 'mar', 4: 'abr', 5: 'mai', 6: 'jun', 7: 'jul', 8: 'ago', 9: 'set', 10: 'out', 11: 'nov', 12: 'dez'}
    df['mes_nome_pt'] = df['mes'].map(meses_pt)
    df['ano_mes_texto'] = df['mes_nome_pt'] + '/' + df['ano'].astype(str)
    df['fluxo_limpo'] = df[col_tipo_fluxo].astype(str).str.strip().str.lower()
    
    return df, col_data_pag, col_contato, col_categoria, col_valor, col_grupo

df_base, col_data_pag, col_contato, col_categoria, col_valor, col_grupo = carregar_dados()

# 3. NAVEGAÇÃO LATERAL
st.sidebar.image("Logo horizontal-fundo.png", use_container_width=True)
pagina = st.sidebar.radio("Navegação:", ["🚀 Visão Geral (YTD)", "🔍 Detalhe Operacional", "👥 Gestão de Sócios", "🏗️ Insumos Operacionais"])

# Filtro de Mês Global para as páginas
df_ordenado = df_base.sort_values('ano_mes_num')
meses_disponiveis = df_ordenado['ano_mes_texto'].unique().tolist()
mes_selecionado = st.sidebar.selectbox("Selecione o Mês de Referência:", options=meses_disponiveis)

# Lógica de Filtro Mês vs YTD
reg_ref = df_base[df_base['ano_mes_texto'] == mes_selecionado].iloc[0]
df_ytd = df_base[(df_base['ano'] == reg_ref['ano']) & (df_base['mes'] <= reg_ref['mes'])]
df_mes = df_base[df_base['ano_mes_texto'] == mes_selecionado]

# --- PÁGINA 1: VISÃO GERAL ---
if pagina == "🚀 Visão Geral (YTD)":
    st.title("Performance Financeira WL Expertise")
    st.subheader(f"Acumulado (YTD) até {mes_selecionado.upper()}")
    
    ent_ytd = df_ytd[df_ytd['fluxo_limpo'] == 'entrada'][col_valor].sum()
    sai_ytd = df_ytd[df_ytd['fluxo_limpo'] == 'saída'][col_valor].sum()
    res_ytd = ent_ytd - sai_ytd
    
    c1, c2, c3 = st.columns(3)
    c1.metric("📈 Entradas Acumuladas", f"R$ {ent_ytd:,.2f}")
    c2.metric("📉 Saídas Acumuladas", f"R$ {sai_ytd:,.2f}")
    c3.metric("📊 Resultado Líquido", f"R$ {res_ytd:,.2f}", delta=f"{(res_ytd/ent_ytd*100):.1f}% Margem" if ent_ytd > 0 else "0%")

    st.markdown("---")
    st.markdown(f"### 📈 Evolução Mensal do Resultado ({reg_ref['ano']})")
    
    df_hist = df_base[df_base['ano'] == reg_ref['ano']].groupby(['ano_mes_num', 'ano_mes_texto', 'fluxo_limpo'])[col_valor].sum().unstack(fill_value=0).reset_index()
    df_hist['Resultado'] = df_hist.get('entrada', 0) - df_hist.get('saída', 0)
    df_hist = df_hist.sort_values('ano_mes_num')
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_hist['ano_mes_texto'], y=df_hist['Resultado'],
        marker_color=['#ef4444' if x < 0 else '#10b981' for x in df_hist['Resultado']],
        text=df_hist['Resultado'].apply(lambda x: f"R$ {x:,.0f}"), textposition='auto'
    ))
    fig.update_layout(template="plotly_dark", margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

# --- PÁGINA 2: DETALHE OPERACIONAL ---
elif pagina == "🔍 Detalhe Operacional":
    st.title("Detalhamento Operacional")
    st.info(f"Análise das movimentações de {mes_selecionado}")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Entradas por Cliente")
        df_cli = df_mes[df_mes['fluxo_limpo'] == 'entrada'].groupby(col_contato)[col_valor].sum().reset_index().sort_values(col_valor, ascending=False).head(10)
        st.plotly_chart(px.bar(df_cli, x=col_valor, y=col_contato, orientation='h', color=col_valor, color_continuous_scale='Mint', template="plotly_dark"), use_container_width=True)
    with c2:
        st.markdown("### Saídas por Categoria")
        df_cat = df_mes[df_mes['fluxo_limpo'] == 'saída'].groupby(col_categoria)[col_valor].sum().reset_index()
        st.plotly_chart(px.pie(df_cat, values=col_valor, names=col_categoria, hole=0.4, template="plotly_dark"), use_container_width=True)

# --- PÁGINA 3: GESTÃO DE SÓCIOS ---
elif pagina == "👥 Gestão de Sócios":
    st.title("Controle de Retiradas de Sócios")
    
    df_socios_mes = df_mes[df_mes[col_grupo].str.contains('SÓCIO', na=False, case=False)]
    list_socios = ["Todos"] + df_socios_mes[col_contato].unique().tolist()
    socio_sel = st.selectbox("Filtrar por Sócio:", list_socios)
    
    if socio_sel != "Todos":
        df_socios_mes = df_socios_mes[df_socios_mes[col_contato] == socio_sel]
    
    total_socio = df_socios_mes[col_valor].sum()
    st.metric(f"Total Retirada: {socio_sel}", f"R$ {total_socio:,.2f}")
    
    st.markdown("### Detalhamento das Retiradas")
    st.dataframe(df_socios_mes[[col_data_pag, col_contato, 'Descrição', col_valor]], use_container_width=True)
    
    fig_soc = px.bar(df_socios_mes, x=col_data_pag, y=col_valor, color=col_contato, title="Cronograma de Retiradas no Mês", template="plotly_dark")
    st.plotly_chart(fig_soc, use_container_width=True)

# --- PÁGINA 4: INSUMOS ---
elif pagina == "🏗️ Insumos Operacionais":
    st.title("Análise de Insumos Operacionais")
    df_insumos = df_mes[df_mes[col_grupo].str.contains('INSUMOS OPERACIONAIS', na=False, case=False)]
    
    total_insumos = df_insumos[col_valor].sum()
    st.metric("Gasto Total com Insumos", f"R$ {total_insumos:,.2f}")
    
    st.markdown("### Composição dos Insumos por Categoria")
    df_ins_cat = df_insumos.groupby(col_categoria)[col_valor].sum().reset_index()
    st.plotly_chart(px.bar(df_ins_cat, x=col_categoria, y=col_valor, text_auto='.2s', color=col_valor, template="plotly_dark"), use_container_width=True)
    st.dataframe(df_insumos[[col_data_pag, col_contato, 'Descrição', col_valor]], use_container_width=True)
