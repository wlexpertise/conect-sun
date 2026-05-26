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

# 🎨 DESIGN MINIMALISTA CORPORATIVO (Fundo cinza claro e destaque real na logo)
st.markdown("""
    <style>
        /* Fundo limpo e contínuo para o App */
        .stApp {
            background-color: #f3f4f6 !important;
        }
        /* Garantir textos principais em cinza escuro profissional */
        h1, h2, h3, p, label, .stMarkdown {
            color: #1f2937 !important;
        }
        /* 🔵 Barra lateral com a cor #13A3B5 bem clarinha (10% de opacidade) e borda sutil */
        [data-testid="stSidebar"] {
            background-color: rgba(19, 163, 181, 0.10) !important;
            border-right: 1px solid rgba(19, 163, 181, 0.20) !important;
        }
        /* Ajuste na linha divisória da barra lateral para combinar com o tom */
        [data-testid="stSidebar"] hr {
            border-color: rgba(19, 163, 181, 0.30) !important;
        }
        /* Customização sutil dos cards nativos de métricas */
        div[data-testid="stMetricValue"] > div {
            color: #0B5A60 !important;
            font-weight: 700;
        }
        /* Card Branco Sólido e Destacado para a Logo do Cliente */
        .logo-box {
            background-color: #ffffff !important;
            padding: 15px !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important;
            text-align: center !important;
            display: block !important;
            margin-bottom: 10px !important;
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
    
    col_data_pag = df.columns[4]       # Data de pagamento (E)
    col_contato = df.columns[7]        # Contato (H) - Sócios/Clientes
    col_categoria = df.columns[10]     # Categoria (K)
    col_situacao = df.columns[11]      # Situação (L)
    col_valor = df.columns[12]         # Valor (M)
    col_grupo = df.columns[13]         # Grupo (N)
    col_tipo_p = df.columns[15]        # 🎯 Coluna P (16ª coluna, índice 15) - Tipo real para batimento
    
    # Filtrar situações válidas conforme combinado
    df['situacao_limpa'] = df[col_situacao].astype(str).str.strip().str.lower()
    df = df[df['situacao_limpa'].isin(['conciliado', 'sem conciliação'])].copy()
    
    # Tratamento da coluna de valores
    if df[col_valor].dtype == object:
        df[col_valor] = df[col_valor].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
    df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0)
    
    # Tratamento de datas
    df[col_data_pag] = pd.to_datetime(df[col_data_pag], errors='coerce', dayfirst=True)
    df = df.dropna(subset=[col_data_pag])
    
    df['ano'] = df[col_data_pag].dt.year
    df['mes'] = df[col_data_pag].dt.month
    df['ano_mes_num'] = df[col_data_pag].dt.strftime('%Y%m')
    meses_pt = {1: 'jan', 2: 'fev', 3: 'mar', 4: 'abr', 5: 'mai', 6: 'jun', 7: 'jul', 8: 'ago', 9: 'set', 10: 'out', 11: 'nov', 12: 'dez'}
    df['mes_nome_pt'] = df['mes'].map(meses_pt)
    df['ano_mes_texto'] = df['mes_nome_pt'] + '/' + df['ano'].astype(str)
    
    # 🔄 DEFINIÇÃO DO FLUXO PELA COLUNA P
    df['tipo_p_limpo'] = df[col_tipo_p].astype(str).str.strip().str.upper()
    
    df['fluxo_limpo'] = 'ignorar'
    df.loc[df['tipo_p_limpo'] == 'VENDA', 'fluxo_limpo'] = 'entrada'
    df.loc[df['tipo_p_limpo'].isin(['CUSTO', 'DESPESA']), 'fluxo_limpo'] = 'saída'
    
    # Filtrar para manter apenas o que é Entrada ou Saída real mapeada
    df = df[df['fluxo_limpo'].isin(['entrada', 'saída'])].copy()
    
    return df, col_data_pag, col_contato, col_categoria, col_valor, col_grupo

df_base, col_data_pag, col_contato, col_categoria, col_valor, col_grupo = carregar_dados()

# 3. NAVEGAÇÃO LATERAL (MENU EXECUTIVO)
st.sidebar.image("Logohorizontal.png", use_container_width=True)
st.sidebar.markdown("---")

pagina = st.sidebar.radio(
    "Navegação Estratégica:", 
    ["🚀 Visão Geral (YTD)", "📈 Análise de Entradas", "📉 Detalhe de Saídas", "👥 Gestão de Sócios", "🏗️ Custos na Prestação de Serviço"]
)

df_ordenado = df_base.sort_values('ano_mes_num')
meses_disponiveis = df_ordenado['ano_mes_texto'].unique().tolist()
mes_selecionado = st.sidebar.selectbox("Selecione o Mês de Referência:", options=meses_disponiveis)

reg_ref = df_base[df_base['ano_mes_texto'] == mes_selecionado].iloc[0]
df_ytd = df_base[(df_base['ano'] == reg_ref['ano']) & (df_base['mes'] <= reg_ref['mes'])].copy()
df_mes = df_base[df_base['ano_mes_texto'] == mes_selecionado].copy()

# Cabeçalho integrado com Grid de segurança para a Logo
header_col1, header_col2 = st.columns([4, 1])

# --- PÁGINA 1: VISÃO GERAL (YTD) ---
if pagina == "🚀 Visão Geral (YTD)":
    with header_col1:
        st.title("Performance Financeira ConectSol")
        st.subheader(f"Acumulado Estratégico (YTD) até {mes_selecionado.upper()}")
    with header_col2:
        st.markdown('<div class="logo-box">', unsafe_allow_html=True)
        st.image("conectlogo.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.markdown("---")
    
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
        margin=dict(t=25, b=15)
    )
    st.plotly_chart(fig_evolucao, use_container_width=True)

# --- PÁGINA 2: ANÁLISE DE ENTRADAS ---
elif pagina == "📈 Análise de Entradas":
    with header_col1:
        st.title("Análise de Entradas por Cliente")
        st.subheader(f"Competência de Referência: {mes_selecionado.upper()}")
    with header_col2:
        st.markdown('<div class="logo-box">', unsafe_allow_html=True)
        st.image("conectlogo.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.markdown("---")
    
    ent_mes_total = df_mes[df_mes['fluxo_limpo'] == 'entrada'][col_valor].sum()
    ent_ytd_total = df_ytd[df_ytd['fluxo_limpo'] == 'entrada'][col_valor].sum()
    
    mc1, mc2 = st.columns(2)
    mc1.metric(f"💰 Total Entradas no Mês ({mes_selecionado})", formatar_brl(ent_mes_total))
    mc2.metric("🚀 Total Entradas Acumulado (YTD)", formatar_brl(ent_ytd_total))
    
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

# --- PÁGINA 3: DETALHE DE SAÍDAS ---
elif pagina == "📉 Detalhe de Saídas":
    with header_col1:
        st.title("Distribuição de Saídas Estratégicas")
        st.subheader(f"Competência de Referência: {mes_selecionado.upper()}")
    with header_col2:
        st.markdown('<div class="logo-box">', unsafe_allow_html=True)
        st.image("conectlogo.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.markdown("---")
    
    sai_mes_total = df_mes[df_mes['fluxo_limpo'] == 'saída'][col_valor].sum()
    sai_ytd_total = df_ytd[df_ytd['fluxo_limpo'] == 'saída'][col_valor].sum()
    
    sc1, sc2 = st.columns(2)
    sc1.metric(f"💸 Total Saídas no Mês ({mes_selecionado})", formatar_brl(sai_mes_total))
    sc2.metric("📉 Total Saídas Acumulado (YTD)", formatar_brl(sai_ytd_total))
    
    st.markdown("---")
    
    df_saidas_m = df_mes[df_mes['fluxo_limpo'] == 'saída']
    df_grp = df_saidas_m.groupby(col_grupo)[col_valor].sum().reset_index()
    df_grp = df_grp.sort_values(col_valor, ascending=True)
    
    if not df_grp.empty:
        textos_grp = [formatar_brl(val) for val in df_grp[col_valor]]
        fig_grp = px.bar(
            df_grp, x=col_valor, y=col_grupo, orientation='h',
            template="plotly_white", labels={col_grupo: 'Grupo de Custo', col_valor: 'Total Gasto'}
        )
        fig_grp.update_traces(marker_color='#13A3B5', text=textos_grp, textposition='auto')
        fig_grp.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_grp, use_container_width=True)
    else:
        st.info("Nenhuma saída registrada para esta competência.")

# --- PÁGINA 4: GESTÃO DE SÓCIOS ---
elif pagina == "👥 Gestão de Sócios":
    with header_col1:
        st.title("Controle de Retiradas de Sócios")
        st.subheader(f"Auditoria de retiradas e despesas compartilhadas em {mes_selecionado.upper()}")
    with header_col2:
        st.markdown('<div class="logo-box">', unsafe_allow_html=True)
        st.image("conectlogo.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
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
        st.subheader(f"Acompanhamento analítico dos custos diretos em {mes_selecionado.upper()}")
    with header_col2:
        st.markdown('<div class="logo-box">', unsafe_allow_html=True)
        st.image("conectlogo.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.markdown("---")
    
    # Cálculo Mensal
    df_insumos_mes = df_mes[df_mes[col_grupo].str.contains('CUSTOS NA PRESTAÇÃO DE SERVIÇO', na=False, case=False)].copy()
    total_insumos_mes = df_insumos_mes[col_valor].sum() if not df_insumos_mes.empty else 0
    
    # Cálculo Acumulado (YTD)
    df_insumos_ytd = df_ytd[df_ytd[col_grupo].str.contains('CUSTOS NA PRESTAÇÃO DE SERVIÇO', na=False, case=False)].copy()
    total_insumos_ytd = df_insumos_ytd[col_valor].sum() if not df_insumos_ytd.empty else 0
    
    # Exibindo os dois cards lado a lado
    cc1, cc2 = st.columns(2)
    cc1.metric(f"🏗️ Custos no Mês ({mes_selecionado})", formatar_brl(total_insumos_mes))
    cc2.metric("🚀 Custos Acumulados no Ano (YTD)", formatar_brl(total_insumos_ytd))
    
    st.markdown("---")
    
    if not df_insumos_mes.empty:
        df_ins_cat = df_insumos_mes.groupby(col_categoria)[col_valor].sum().reset_index().sort_values(col_valor, ascending=True)
        textos_ins = [formatar_brl(val) for val in df_ins_cat[col_valor]]
        
        fig_ins = px.bar(
            df_ins_cat, x=col_valor, y=col_categoria, orientation='h', 
            template="plotly_white", labels={col_categoria: 'Categoria de Despesa', col_valor: 'Total'}
        )
        fig_ins.update_traces(marker_color='#13A3B5', text=textos_ins, textposition='auto')
        fig_ins.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_ins, use_container_width=True)
        
        df_tabela_ins = df_insumos_mes[[col_data_pag, col_contato, 'Descrição', col_valor]].copy()
        df_tabela_ins[col_data_pag] = df_tabela_ins[col_data_pag].dt.strftime('%d/%m/%Y')
        df_tabela_ins[col_valor] = df_tabela_ins[col_valor].apply(formatar_brl)
        st.dataframe(df_tabela_ins, use_container_width=True)
    else:
        st.info("Nenhuma despesa de 'Custos na Prestação de Serviço' registrada para esta competência.")
