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

# 🎨 INJEÇÃO DE DESIGN EXECUTIVO CORRIGIDA (Sem parâmetros fantasmas)
st.markdown("""
    <style>
        /* Fundo geral da aplicação em Cinza Claro Corporativo */
        .stApp {
            background-color: #f8fafc !important;
        }
        /* Estilização dos blocos/cards de conteúdo */
        div[data-testid="stVerticalBlock"] > div {
            background-color: #ffffff !important;
            border-radius: 8px !important;
            padding: 20px !important;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1) !important;
            margin-bottom: 1rem !important;
        }
        /* Forçar cor dos textos para garantir leitura no fundo claro */
        h1, h2, h3, p, label, .stMarkdown {
            color: #0f172a !important;
        }
        /* Sidebar branca com separador sutil */
        [data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 1px solid #e2e8f0 !important;
        }
    </style>
""", unsafe_allow_html=True)

# 🛠️ FUNÇÃO AUXILIAR DE FORMATAÇÃO CONTÁBIL PADRÃO (0.0; (0.0); -)
def formatar_brl(valor):
    if valor is None or pd.isna(valor) or valor == 0:
        return "-"
    if valor < 0:
        return f"(R$ {abs(valor):,.2f})".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_pct(valor):
    if valor is None or pd.isna(valor) or valor == 0:
        return "-"
    if valor < 0:
        return f"({abs(valor):.1f}%)".replace(".", ",")
    return f"{valor:.1f}%".replace(".", ",")

# 2. CARREGAMENTO E TRATAMENTO DOS DADOS
@st.cache_data
def carregar_dados():
    nome_do_arquivo = 'dados_conectsol.xlsx' 
    df = pd.read_excel(nome_do_arquivo)
    df.columns = df.columns.str.strip()
    
    col_tipo_fluxo = df.columns[2]     # Tipo (Entrada/Saída)
    col_data_pag = df.columns[4]       # Data de pagamento
    col_contato = df.columns[7]        # Contato (H) - Sócios/Clientes
    col_categoria = df.columns[10]     # Categoria
    col_situacao = df.columns[11]      # Situação
    col_valor = df.columns[12]         # Valor
    col_grupo = df.columns[13]         # Grupo
    
    df = df[df[col_situacao].astype(str).str.strip().str.lower() == 'conciliado'].copy()
    if df[col_valor].dtype == object:
        df[col_valor] = df[col_valor].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
    df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0)
    df[col_data_pag] = pd.to_datetime(df[col_data_pag], errors='coerce', dayfirst=True)
    df = df.dropna(subset=[col_data_pag])
    
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
st.sidebar.image("Logohorizontal.png", use_container_width=True)
st.sidebar.markdown("---")

pagina = st.sidebar.radio(
    "Navegação Estratégica:", 
    ["🚀 Visão Geral (YTD)", "📈 Análise de Receitas", "📉 Detalhe de Despesas", "👥 Gestão de Sócios", "🏗️ Custos na Prestação de Serviço"]
)

df_ordenado = df_base.sort_values('ano_mes_num')
meses_disponiveis = df_ordenado['ano_mes_texto'].unique().tolist()
mes_selecionado = st.sidebar.selectbox("Selecione o Mês de Referência:", options=meses_disponiveis)

reg_ref = df_base[df_base['ano_mes_texto'] == mes_selecionado].iloc[0]
df_ytd = df_base[(df_base['ano'] == reg_ref['ano']) & (df_base['mes'] <= reg_ref['mes'])].copy()
df_mes = df_base[df_base['ano_mes_texto'] == mes_selecionado].copy()

# Cabeçalho Fixo com a Logo do Cliente alinhada à direita
header_col1, header_col2 = st.columns([5, 1])
with header_col2:
    st.image("conectlogo.png", use_container_width=True)

# --- PÁGINA 1: VISÃO GERAL (YTD) ---
if pagina == "🚀 Visão Geral (YTD)":
    with header_col1:
        st.title("Performance Financeira WL Expertise")
        st.subheader(f"Acumulado Estratégico (YTD) até {mes_selecionado.upper()}")
    
    ent_ytd = df_ytd[df_ytd['fluxo_limpo'] == 'entrada'][col_valor].sum()
    sai_ytd = df_ytd[df_ytd['fluxo_limpo'] == 'saída'][col_valor].sum()
    res_ytd = ent_ytd - sai_ytd
    margem_val = (res_ytd / ent_ytd * 100) if ent_ytd > 0 else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("📈 Entradas Acumuladas", formatar_brl(ent_ytd))
    c2.metric("📉 Saídas Acumuladas", formatar_brl(sai_ytd))
    c3.metric("📊 Resultado Líquido", formatar_brl(res_ytd), delta=f"{formatar_pct(margem_val)} Margem")

    st.markdown("---")
    st.markdown(f"### 📊 Evolução Mensal do Resultado Líquido de Caixa ({reg_ref['ano']})")
    
    df_ano_atual = df_base[df_base['ano'] == reg_ref['ano']].copy()
    base_meses = df_ano_atual[['ano_mes_num', 'ano_mes_texto']].drop_duplicates()
    
    df_ent_m = df_ano_atual[df_ano_atual['fluxo_limpo'] == 'entrada'].groupby('ano_mes_num')[col_valor].sum().reset_index(name='entrada')
    df_sai_m = df_ano_atual[df_ano_atual['fluxo_limpo'] == 'saída'].groupby('ano_mes_num')[col_valor].sum().reset_index(name='saída')
    
    df_hist = pd.merge(base_meses, df_ent_m, on='ano_mes_num', how='left').fillna(0)
    df_hist = pd.merge(df_hist, df_sai_m, on='ano_mes_num', how='left').fillna(0)
    df_hist['Resultado'] = df_hist['entrada'] - df_hist['saída']
    df_hist = df_hist.sort_values('ano_mes_num')
    
    textos_grafico = [formatar_brl(val) for val in df_hist['Resultado']]
    
    fig_evolucao = go.Figure()
    fig_evolucao.add_trace(go.Bar(
        x=df_hist['ano_mes_texto'], 
        y=df_hist['Resultado'],
        marker_color=['#ef4444' if value < 0 else '#28B260' for value in df_hist['Resultado']],
        text=textos_grafico, 
        textposition='auto'
    ))
    fig_evolucao.update_layout(
        template="plotly_white", 
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=15, b=15)
    )
    st.plotly_chart(fig_evolucao, use_container_width=True)

# --- PÁGINA 2: ANÁLISE DE RECEITAS ---
elif pagina == "📈 Análise de Receitas":
    with header_col1:
        st.title("Análise de Receitas por Cliente")
        st.markdown(f"Entradas registradas na competência de **{mes_selecionado.upper()}**")
    st.markdown("---")
    
    df_cli = df_mes[df_mes['fluxo_limpo'] == 'entrada'].groupby(col_contato)[col_valor].sum().reset_index()
    df_cli = df_cli.sort_values(col_valor, ascending=True).tail(12)
    
    if not df_cli.empty:
        textos_cli = [formatar_brl(val) for val in df_cli[col_valor]]
        fig_cli = px.bar(
            df_cli, x=col_valor, y=col_contato, orientation='h', 
            template="plotly_white", labels={col_contato: 'Cliente / Origem', col_valor: 'Valor Recebido'}
        )
        fig_cli.update_traces(marker_color='#0B5A60', text=textos_cli, textposition='auto')
        fig_cli.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_cli, use_container_width=True)
    else:
        st.info("Nenhuma entrada registrada para este mês.")

# --- PÁGINA 3: DETALHE DE DESPESAS ---
elif pagina == "📉 Detalhe de Despesas":
    with header_col1:
        st.title("Distribuição de Despesas Operacionais")
        st.markdown(f"Estrutura de saídas analíticas para a competência de **{mes_selecionado.upper()}**")
    st.markdown("---")
    
    grupos_saidas = ["Todos"] + df_mes[df_mes['fluxo_limpo'] == 'saída'][col_grupo].dropna().unique().tolist()
    grupo_escolhido = st.selectbox("Filtrar por Grupo de Custo da Empresa:", options=grupos_saidas)
    
    df_saidas_f = df_mes[df_mes['fluxo_limpo'] == 'saída']
    if grupo_escolhido != "Todos":
        df_saidas_f = df_saidas_f[df_saidas_f[col_grupo] == grupo_escolhido]
        
    df_cat = df_saidas_f.groupby(col_categoria)[col_valor].sum().reset_index()
    df_cat = df_cat.sort_values(col_valor, ascending=True)
    
    if not df_cat.empty:
        textos_cat = [formatar_brl(val) for val in df_cat[col_valor]]
        fig_cat = px.bar(
            df_cat, x=col_valor, y=col_categoria, orientation='h',
            template="plotly_white", labels={col_categoria: 'Categoria de Despesa', col_valor: 'Total Gasto'}
        )
        fig_cat.update_traces(marker_color='#13A3B5', text=textos_cat, textposition='auto')
        fig_cat.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_cat, use_container_width=True)
    else:
        st.info("Nenhuma saída mapeada para os critérios atuais.")

# --- PÁGINA 4: GESTÃO DE SÓCIOS ---
elif pagina == "👥 Gestão de Sócios":
    with header_col1:
        st.title("Controle de Retiradas de Sócios")
        st.markdown(f"Auditoria de retiradas e despesas compartilhadas em **{mes_selecionado.upper()}**")
    st.markdown("---")
    
    df_socios_mes = df_mes[df_mes[col_grupo].str.contains('SÓCIO', na=False, case=False)].copy()
    
    if not df_socios_mes.empty:
        df_soc_agrupado = df_socios_mes.groupby(col_contato)[col_valor].sum().reset_index().sort_values(by=col_valor, ascending=False)
        textos_soc_bars = [formatar_brl(val) for val in df_soc_agrupado[col_valor]]
        
        fig_soc_vert = px.bar(
            df_soc_agrupado, x=col_contato, y=col_valor, template="plotly_white",
            labels={col_contato: 'Sócio / Beneficiário', col_valor: 'Total Retirado'}
        )
        fig_soc_vert.update_traces(marker_color='#0B5A60', text=textos_soc_bars, textposition='auto')
        fig_soc_vert.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_soc_vert, use_container_width=True)
        
        st.markdown("---")
        list_socios = ["Todos"] + df_socios_mes[col_contato].unique().tolist()
        socio_sel = st.selectbox("Filtrar Tabela por Sócio:", list_socios)
        
        if socio_sel != "Todos":
            df_socios_mes = df_socios_mes[df_socios_mes[col_contato] == socio_sel]
        
        total_socio = df_socios_mes[col_valor].sum()
        st.metric(f"Total Isolado — {socio_sel}", formatar_brl(total_socio))
        
        df_tabela_socio = df_socios_mes[[col_data_pag, col_contato, 'Descrição', col_valor]].copy()
        df_tabela_socio[col_data_pag] = df_tabela_socio[col_data_pag].dt.strftime('%d/%m/%Y')
        df_tabela_socio[col_valor] = df_tabela_socio[col_valor].apply(formatar_brl)
        st.dataframe(df_tabela_socio, use_container_width=True)
    else:
        st.info("Não foram encontradas transações vinculadas ao grupo de Sócios neste mês.")

# --- PÁGINA 5: CUSTOS NA PRESTAÇÃO DE SERVIÇO ---
elif pagina == "🏗️ Custos na Prestação de Serviço":
    with header_col1:
        st.title("Análise de Custos na Prestação de Serviço")
        st.markdown(f"Acompanhamento analítico dos custos diretos em **{mes_selecionado.upper()}**")
    st.markdown("---")
    
    df_insumos = df_mes[df_mes[col_grupo].str.contains('CUSTOS NA PRESTAÇÃO DE SERVIÇO', na=False, case=False)].copy()
    
    if not df_insumos.empty:
        total_insumos = df_insumos[col_valor].sum()
        st.metric("Gasto Total Consolidado", formatar_brl(total_insumos))
        
        df_ins_cat = df_insumos.groupby(col_categoria)[col_valor].sum().reset_index().sort_values(col_valor, ascending=True)
        textos_ins = [formatar_brl(val) for val in df_ins_cat[col_valor]]
        
        fig_ins = px.bar(
            df_ins_cat, x=col_valor, y=col_categoria, orientation='h', 
            template="plotly_white", labels={col_categoria: 'Categoria de Despesa', col_valor: 'Total'}
        )
        fig_ins.update_traces(marker_color='#13A3B5', text=textos_ins, textposition='auto')
        fig_ins.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_ins, use_container_width=True)
        
        df_tabela_ins = df_insumos[[col_data_pag, col_contato, 'Descrição', col_valor]].copy()
        df_tabela_ins[col_data_pag] = df_tabela_ins[col_data_pag].dt.strftime('%d/%m/%Y')
        df_tabela_ins[col_valor] = df_tabela_ins[col_valor].apply(formatar_brl)
        st.dataframe(df_tabela_ins, use_container_width=True)
    else:
        st.info("Nenhuma despesa de 'Custos na Prestação de Serviço' registrada para esta competência.")
