import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E CSS
# ==========================================
st.set_page_config(
    page_title="WL Expertise | Conectsol BI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        .stApp { background-color: #f3f4f6 !important; }
        h1, h2, h3, p, label, .stMarkdown { color: #1f2937 !important; }
        [data-testid="stSidebar"] {
            background-color: rgba(19, 163, 181, 0.10) !important;
            border-right: 1px solid rgba(19, 163, 181, 0.20) !important;
        }
        [data-testid="stSidebar"] hr { border-color: rgba(19, 163, 181, 0.30) !important; }
        div[data-testid="stMetricValue"] > div { color: #0B5A60 !important; font-weight: 700; }
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

# ==========================================
# 2. FUNÇÕES DE FORMATAÇÃO E CARREGAMENTO
# ==========================================
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

def formatar_k(valor):
    """Formatador limpo para gráficos: Arredonda sem decimais (Ex: R$ 11K)"""
    if valor is None or pd.isna(valor) or valor == 0:
        return ""
    prefixo = "R$ "
    v_abs = abs(valor)
    
    if v_abs >= 1000:
        v_k = round(v_abs / 1000)
        texto = f"{v_k:,.0f}K"
    else:
        texto = f"{v_abs:,.0f}"
        
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    
    if valor < 0:
        return f"({prefixo}{texto})"
    return f"{prefixo}{texto}"

@st.cache_data
def carregar_dados():
    nome_do_arquivo = 'dados_conectsol.xlsx' 
    df = pd.read_excel(nome_do_arquivo)
    df.columns = df.columns.str.strip()
    
    col_data_pag = df.columns[4]       # Data de pagamento (E)
    col_contato = df.columns[7]        # Contato (H)
    col_categoria = df.columns[10]     # Categoria (K)
    col_situacao = df.columns[11]      # Situação (L)
    col_valor = df.columns[12]         # Valor (M)
    col_grupo = df.columns[13]         # Grupo (N)
    col_tipo_p = df.columns[15]        # Coluna P - Tipo
    
    # FILTRO DEFINITIVO PARA SITUAÇÃO
    mascara_situacao = df[col_situacao].astype(str).str.contains('conciliad|sem concilia', case=False, na=False, regex=True)
    df = df[mascara_situacao].copy()
    
    # Tratamento da coluna de valores
    if df[col_valor].dtype == object:
        df[col_valor] = df[col_valor].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
    df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0)
    
    # Tratamento de datas
    df[col_data_pag] = pd.to_datetime(df[col_data_pag], errors='coerce', dayfirst=True)
    df = df.dropna(subset=[col_data_pag])
    
    # Criação de colunas temporais
    df['ano'] = df[col_data_pag].dt.year
    df['mes'] = df[col_data_pag].dt.month
    df['ano_mes_num'] = df[col_data_pag].dt.strftime('%Y%m')
    meses_pt = {1: 'jan', 2: 'fev', 3: 'mar', 4: 'abr', 5: 'mai', 6: 'jun', 7: 'jul', 8: 'ago', 9: 'set', 10: 'out', 11: 'nov', 12: 'dez'}
    df['mes_nome_pt'] = df['mes'].map(meses_pt)
    df['ano_mes_texto'] = df['mes_nome_pt'] + '/' + df['ano'].astype(str)
    
    # Definição do fluxo (Entrada/Saída)
    df['tipo_p_limpo'] = df[col_tipo_p].astype(str).str.strip().str.upper()
    df['fluxo_limpo'] = 'ignorar'
    
    df.loc[df['tipo_p_limpo'].str.contains('VENDA', na=False), 'fluxo_limpo'] = 'entrada'
    df.loc[df['tipo_p_limpo'].str.contains('CUSTO|DESPESA', na=False), 'fluxo_limpo'] = 'saída'
    
    df = df[df['fluxo_limpo'].isin(['entrada', 'saída'])].copy()
    
    return df, col_data_pag, col_contato, col_categoria, col_valor, col_grupo

df_base, col_data_pag, col_contato, col_categoria, col_valor, col_grupo = carregar_dados()

# ==========================================
# 3. NAVEGAÇÃO LATERAL (MENU EXECUTIVO)
# ==========================================
st.sidebar.image("Logohorizontal.png", use_container_width=True)
st.sidebar.markdown("---")

pagina = st.sidebar.radio(
    "Navegação Estratégica:", 
    [
        "🚀 Visão Geral (YTD)", 
        "📈 Análise de Entradas", 
        "📉 Detalhe de Saídas", 
        "👥 Gestão de Sócios", 
        "🏗️ Custos na Prestação de Serviço",
        "🔬 Análises Avançadas"
    ]
)

df_ordenado = df_base.sort_values('ano_mes_num')
meses_disponiveis = df_ordenado['ano_mes_texto'].unique().tolist()

mes_selecionado = st.sidebar.selectbox(
    "Selecione o Mês de Referência:", 
    options=meses_disponiveis,
    index=len(meses_disponiveis) - 1
)

reg_ref = df_base[df_base['ano_mes_texto'] == mes_selecionado].iloc[0]
df_ytd = df_base[(df_base['ano'] == reg_ref['ano']) & (df_base['mes'] <= reg_ref['mes'])].copy()
df_mes = df_base[df_base['ano_mes_texto'] == mes_selecionado].copy()

# ==========================================
# 4. FUNÇÃO RESUMO (CARDS DO MÊS)
# ==========================================
def exibir_resumo_mes():
    ent_mes = df_mes[df_mes['fluxo_limpo'] == 'entrada'][col_valor].sum()
    sai_mes = df_mes[df_mes['fluxo_limpo'] == 'saída'][col_valor].sum()
    res_mes = ent_mes - sai_mes
    margem_mes = (res_mes / ent_mes * 100) if ent_mes > 0 else 0
    
    st.markdown(f"**Resumo do Mês ({mes_selecionado})**")
    rm1, rm2, rm3 = st.columns(3)
    rm1.metric("💰 Entradas no Mês", formatar_brl(ent_mes))
    rm2.metric("💸 Saídas no Mês", formatar_brl(sai_mes))
    rm3.metric("📊 Resultado do Mês", formatar_brl(res_mes), delta=f"{formatar_pct(margem_mes)} Margem")
    st.markdown("---")

# ==========================================
# 5. ESTRUTURA DAS PÁGINAS
# ==========================================
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
    exibir_resumo_mes()
    
    ent_ytd = df_ytd[df_ytd['fluxo_limpo'] == 'entrada'][col_valor].sum()
    sai_ytd = df_ytd[df_ytd['fluxo_limpo'] == 'saída'][col_valor].sum()
    res_ytd = ent_ytd - sai_ytd
    margem_val = (res_ytd / ent_ytd * 100) if ent_ytd > 0 else 0
    
    st.markdown("**Resumo Acumulado (YTD)**")
    c1, c2, c3 = st.columns(3)
    c1.metric("📈 Entradas Acumuladas", formatar_brl(ent_ytd))
    c2.metric("📉 Saídas Acumuladas", formatar_brl(sai_ytd))
    c3.metric("📊 Resultado Líquido YTD", formatar_brl(res_ytd), delta=f"{formatar_pct(margem_val)} Margem")

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
    
    textos_grafico = [formatar_k(val) for val in df_hist['Resultado']]
    
    fig_evolucao = go.Figure()
    fig_evolucao.add_trace(go.Bar(
        x=df_hist['ano_mes_texto'], 
        y=df_hist['Resultado'],
        marker_color=['#ef4444' if value < 0 else '#28B260' for value in df_hist['Resultado']],
        text=textos_grafico, 
        textposition='auto'
    ))
    fig_evolucao.update_traces(textangle=0) # Força texto na horizontal
    fig_evolucao.update_layout(
        template="plotly_white", 
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=25, b=15),
        bargap=0.15 # Colunas mais robustas
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
    exibir_resumo_mes()
    
    ent_ytd_total = df_ytd[df_ytd['fluxo_limpo'] == 'entrada'][col_valor].sum()
    st.metric("🚀 Total Entradas Acumulado (YTD)", formatar_brl(ent_ytd_total))
    st.markdown("---")
    
    df_cli = df_mes[df_mes['fluxo_limpo'] == 'entrada'].groupby(col_contato)[col_valor].sum().reset_index()
    df_cli = df_cli.sort_values(col_valor, ascending=True).tail(12)
    
    if not df_cli.empty:
        textos_cli = [formatar_k(val) for val in df_cli[col_valor]]
        fig_cli = px.bar(
            df_cli, x=col_valor, y=col_contato, orientation='h', 
            template="plotly_white", labels={col_contato: 'Cliente / Origem', col_valor: 'Valor Recebido'}
        )
        fig_cli.update_traces(marker_color='#0B5A60', text=textos_cli, textposition='auto')
        fig_cli.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis={'categoryorder':'total ascending'}, bargap=0.15)
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
    exibir_resumo_mes()
    
    sai_ytd_total = df_ytd[df_ytd['fluxo_limpo'] == 'saída'][col_valor].sum()
    st.metric("📉 Total Saídas Acumulado (YTD)", formatar_brl(sai_ytd_total))
    st.markdown("---")
    
    df_saidas_m = df_mes[df_mes['fluxo_limpo'] == 'saída']
    df_grp = df_saidas_m.groupby(col_grupo)[col_valor].sum().reset_index()
    df_grp = df_grp.sort_values(col_valor, ascending=True)
    
    if not df_grp.empty:
        textos_grp = [formatar_k(val) for val in df_grp[col_valor]]
        fig_grp = px.bar(
            df_grp, x=col_valor, y=col_grupo, orientation='h',
            template="plotly_white", labels={col_grupo: 'Grupo de Custo', col_valor: 'Total Gasto'}
        )
        fig_grp.update_traces(marker_color='#13A3B5', text=textos_grp, textposition='auto')
        fig_grp.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis={'categoryorder':'total ascending'}, bargap=0.15)
        st.plotly_chart(fig_grp, use_container_width=True)
    else:
        st.info("Nenhuma saída registrada para esta competência.")

# --- PÁGINA 4: GESTÃO DE SÓCIOS ---
elif pagina == "👥 Gestão de Sócios":
    with header_col1:
        st.title("Controle de Retiradas de Sócios")
        st.subheader(f"Auditoria de retiradas em {mes_selecionado.upper()}")
    with header_col2:
        st.markdown('<div class="logo-box">', unsafe_allow_html=True)
        st.image("conectlogo.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.markdown("---")
    exibir_resumo_mes()
    
    df_socios_mes = df_mes[df_mes[col_grupo].str.contains('SÓCIO', na=False, case=False)].copy()
    
    if not df_socios_mes.empty:
        df_soc_agrupado = df_socios_mes.groupby(col_contato)[col_valor].sum().reset_index().sort_values(by=col_valor, ascending=False)
        textos_soc_bars = [formatar_k(val) for val in df_soc_agrupado[col_valor]]
        
        fig_soc_vert = px.bar(
            df_soc_agrupado, x=col_contato, y=col_valor, template="plotly_white",
            labels={col_contato: 'Sócio / Beneficiário', col_valor: 'Total Retirado'}
        )
        fig_soc_vert.update_traces(marker_color='#0B5A60', text=textos_soc_bars, textposition='auto', textangle=0)
        fig_soc_vert.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', bargap=0.15)
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
        st.subheader(f"Acompanhamento analítico em {mes_selecionado.upper()}")
    with header_col2:
        st.markdown('<div class="logo-box">', unsafe_allow_html=True)
        st.image("conectlogo.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.markdown("---")
    
    df_insumos_mes = df_mes[df_mes[col_grupo].str.contains('CUSTOS NA PRESTAÇÃO DE SERVIÇO', na=False, case=False)].copy()
    total_insumos_mes = df_insumos_mes[col_valor].sum() if not df_insumos_mes.empty else 0
    
    df_insumos_ytd = df_ytd[df_ytd[col_grupo].str.contains('CUSTOS NA PRESTAÇÃO DE SERVIÇO', na=False, case=False)].copy()
    total_insumos_ytd = df_insumos_ytd[col_valor].sum() if not df_insumos_ytd.empty else 0
    
    cc1, cc2 = st.columns(2)
    cc1.metric(f"🏗️ Custos do Grupo ({mes_selecionado})", formatar_brl(total_insumos_mes))
    cc2.metric("🚀 Custos Acumulados no Ano (YTD)", formatar_brl(total_insumos_ytd))
    
    st.markdown("---")
    
    if not df_insumos_mes.empty:
        df_ins_cat = df_insumos_mes.groupby(col_categoria)[col_valor].sum().reset_index().sort_values(col_valor, ascending=True)
        textos_ins = [formatar_k(val) for val in df_ins_cat[col_valor]]
        
        fig_ins = px.bar(
            df_ins_cat, x=col_valor, y=col_categoria, orientation='h', 
            template="plotly_white", labels={col_categoria: 'Categoria de Despesa', col_valor: 'Total'}
        )
        fig_ins.update_traces(marker_color='#13A3B5', text=textos_ins, textposition='auto')
        fig_ins.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', bargap=0.15)
        st.plotly_chart(fig_ins, use_container_width=True)
        
        df_tabela_ins = df_insumos_mes[[col_data_pag, col_contato, 'Descrição', col_valor]].copy()
        df_tabela_ins[col_data_pag] = df_tabela_ins[col_data_pag].dt.strftime('%d/%m/%Y')
        df_tabela_ins[col_valor] = df_tabela_ins[col_valor].apply(formatar_brl)
        st.dataframe(df_tabela_ins, use_container_width=True)
    else:
        st.info("Nenhuma despesa de 'Custos na Prestação de Serviço' registrada para esta competência.")

# --- PÁGINA 6: ANÁLISES AVANÇADAS ---
elif pagina == "🔬 Análises Avançadas":
    with header_col1:
        st.title("Análises Avançadas Interanuais")
        st.subheader("Comparativo Ano a Ano (YoY) — 2025 vs 2026")
    with header_col2:
        st.markdown('<div class="logo-box">', unsafe_allow_html=True)
        st.image("conectlogo.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.markdown("---")
    
    tab_visao, tab_socios, tab_custos = st.tabs([
        "📊 Visão Geral YoY", 
        "👥 Gestão de Sócios YoY", 
        "🏗️ Custos na Prestação YoY"
    ])
    
    meses_id = list(range(1, 13))
    meses_nomes = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
    df_calendario = pd.DataFrame({'mes': meses_id, 'mes_nome': meses_nomes})

    # --- SUBABA 1: VISÃO GERAL YOY ---
    with tab_visao:
        st.markdown("### 📊 Histórico de Entradas, Saídas e Resultados de Caixa")
        
        metrica_yoy = st.selectbox("Selecione a métrica para comparar:", ["Entradas", "Saídas", "Resultado Líquido"])
        
        df_vg = df_base.groupby(['ano', 'mes', 'fluxo_limpo'])[col_valor].sum().unstack(fill_value=0).reset_index()
        df_vg['resultado'] = df_vg['entrada'] - df_vg['saída']
        
        df_2025 = df_vg[df_vg['ano'] == 2025].copy()
        df_2026 = df_vg[df_vg['ano'] == 2026].copy()
        
        df_comp = pd.merge(df_calendario, df_2025, on='mes', how='left').fillna(0)
        df_comp = pd.merge(df_comp, df_2026, on='mes', how='left', suffixes=('_2025', '_2026')).fillna(0)
        
        if metrica_yoy == "Entradas":
            v2025 = df_comp['entrada_2025']
            v2026 = df_comp['entrada_2026']
            c_2025, c_2026 = '#A3D9E2', '#0B5A60'
            label_tit = "Comparativo Mensal de Entradas"
        elif metrica_yoy == "Saídas":
            v2025 = df_comp['saída_2025']
            v2026 = df_comp['saída_2026']
            c_2025, c_2026 = '#FCA5A5', '#EF4444'
            label_tit = "Comparativo Mensal de Saídas"
        else:
            v2025 = df_comp['resultado_2025']
            v2026 = df_comp['resultado_2026']
            c_2025, c_2026 = '#93C5FD', '#1D4ED8'
            label_tit = "Comparativo Mensal do Resultado Líquido"
            
        var_pct = []
        for r25, r26 in zip(v2025, v2026):
            if r25 != 0:
                var_pct.append(((r26 - r25) / abs(r25)) * 100)
            elif r25 == 0 and r26 != 0:
                var_pct.append(100.0)
            else:
                var_pct.append(0.0)
                
        fig_vg_yoy = go.Figure()
        fig_vg_yoy.add_trace(go.Bar(
            x=df_comp['mes_nome'].str.upper(), y=v2025, name='Ano 2025', marker_color=c_2025,
            text=[formatar_k(x) for x in v2025], textposition='auto'
        ))
        fig_vg_yoy.add_trace(go.Bar(
            x=df_comp['mes_nome'].str.upper(), y=v2026, name='Ano 2026', marker_color=c_2026,
            text=[formatar_k(x) for x in v2026], textposition='auto'
        ))
        
        fig_vg_yoy.add_trace(go.Scatter(
            x=df_comp['mes_nome'].str.upper(), y=v2026, mode='lines+markers+text',
            name='Variação %', line=dict(color='#F59E0B', width=3, dash='dot'),
            text=[f"{' ' if v < 0 else '+'}{v:.1f}%" if v != 0 else "" for v in var_pct],
            textposition='top center'
        ))
        
        fig_vg_yoy.update_traces(selector=dict(type='bar'), textangle=0) # Força texto horizontal nas barras
        fig_vg_yoy.update_layout(
            title=label_tit, barmode='group', template='plotly_white',
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=40, b=15), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            bargap=0.15, bargroupgap=0.05 # Força colunas robustas agrupadas
        )
        st.plotly_chart(fig_vg_yoy, use_container_width=True)
        
        df_exibir_vg = pd.DataFrame({
            'Mês de Referência': df_comp['mes_nome'].str.upper(),
            'Realizado 2025': v2025.apply(formatar_brl),
            'Realizado 2026': v2026.apply(formatar_brl),
            'Diferença Absoluta': (v2026 - v2025).apply(formatar_brl),
            'Variação (%)': [f"{x:+.1f}%" if x != 0 else "-" for x in var_pct]
        })
        st.markdown("**Demonstrativo Analítico Interanual:**")
        st.dataframe(df_exibir_vg, use_container_width=True)

    # --- SUBABA 2: GESTÃO DE SÓCIOS YOY ---
    with tab_socios:
        st.markdown("### 👥 Análise Comparativa por Conta de Sócios")
        
        df_soc_all = df_base[df_base[col_grupo].str.contains('SÓCIO', na=False, case=False)].copy()
        
        if not df_soc_all.empty:
            socios_lista = sorted(df_soc_all[col_contato].dropna().unique().tolist())
            socio_sel_yoy = st.selectbox("Selecione o Sócio para Comparação interanual:", socios_lista)
            
            df_soc_filtrado = df_soc_all[df_soc_all[col_contato] == socio_sel_yoy].copy()
            df_soc_m = df_soc_filtrado.groupby(['ano', 'mes'])[col_valor].sum().unstack(level=0, fill_value=0).reset_index()
            
            if 2025 not in df_soc_m.columns: df_soc_m[2025] = 0.0
            if 2026 not in df_soc_m.columns: df_soc_m[2026] = 0.0
            
            df_soc_comp = pd.merge(df_calendario, df_soc_m, on='mes', how='left').fillna(0)
            df_soc_comp['acum_2025'] = df_soc_comp[2025].cumsum()
            df_soc_comp['acum_2026'] = df_soc_comp[2026].cumsum()
            
            visao_socio = st.radio("Selecione o tipo de visão:", ["Visão Mensal", "Visão Acumulada (YTD)"], horizontal=True)
            
            fig_soc_yoy = go.Figure()
            if visao_socio == "Visão Mensal":
                v25, v26 = df_soc_comp[2025], df_soc_comp[2026]
                tit_s = f"Retiradas Mensais — {socio_sel_yoy}"
            else:
                v25, v26 = df_soc_comp['acum_2025'], df_soc_comp['acum_2026']
                tit_s = f"Evolução Acumulada (YTD) — {socio_sel_yoy}"
                
            fig_soc_yoy.add_trace(go.Bar(
                x=df_soc_comp['mes_nome'].str.upper(), y=v25, name='2025', marker_color='#94A3B8',
                text=[formatar_k(x) for x in v25], textposition='auto'
            ))
            fig_soc_yoy.add_trace(go.Bar(
                x=df_soc_comp['mes_nome'].str.upper(), y=v26, name='2026', marker_color='#0B5A60',
                text=[formatar_k(x) for x in v26], textposition='auto'
            ))
            fig_soc_yoy.update_traces(textangle=0)
            fig_soc_yoy.update_layout(
                title=tit_s, barmode='group', template='plotly_white',
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                bargap=0.15, bargroupgap=0.05
            )
            st.plotly_chart(fig_soc_yoy, use_container_width=True)
            
            df_tab_soc = pd.DataFrame({
                'Mês': df_soc_comp['mes_nome'].str.upper(),
                'Mensal 2025': df_soc_comp[2025].apply(formatar_brl),
                'Mensal 2026': df_soc_comp[2026].apply(formatar_brl),
                'Acumulado 2025': df_soc_comp['acum_2025'].apply(formatar_brl),
                'Acumulado 2026': df_soc_comp['acum_2026'].apply(formatar_brl)
            })
            st.dataframe(df_tab_soc, use_container_width=True)
        else:
            st.info("Nenhum dado associado a Sócios encontrado na base.")

    # --- SUBABA 3: CUSTOS NA PRESTAÇÃO YOY ---
    with tab_custos:
        st.markdown("### 🏗️ Histórico Comparativo de Custos Operacionais")
        
        df_custos_all = df_base[df_base[col_grupo].str.contains('CUSTOS NA PRESTAÇÃO DE SERVIÇO', na=False, case=False)].copy()
        
        if not df_custos_all.empty:
            df_custos_m = df_custos_all.groupby(['ano', 'mes'])[col_valor].sum().unstack(level=0, fill_value=0).reset_index()
            
            if 2025 not in df_custos_m.columns: df_custos_m[2025] = 0.0
            if 2026 not in df_custos_m.columns: df_custos_m[2026] = 0.0
            
            df_custos_comp = pd.merge(df_calendario, df_custos_m, on='mes', how='left').fillna(0)
            df_custos_comp['acum_2025'] = df_custos_comp[2025].cumsum()
            df_custos_comp['acum_2026'] = df_custos_comp[2026].cumsum()
            
            visao_custos = st.radio("Selecione o tipo de visão:", ["Mensal ", "Acumulado (YTD) "], horizontal=True)
            
            fig_custos_yoy = go.Figure()
            if visao_custos == "Mensal ":
                v25_c, v26_c = df_custos_comp[2025], df_custos_comp[2026]
                tit_c = "Custos Mensais Globais na Prestação de Serviço"
            else:
                v25_c, v26_c = df_custos_comp['acum_2025'], df_custos_comp['acum_2026']
                tit_c = "Evolução do Custo Acumulado (YTD) na Prestação de Serviço"
                
            fig_custos_yoy.add_trace(go.Bar(
                x=df_custos_comp['mes_nome'].str.upper(), y=v25_c, name='2025', marker_color='#FCA5A5',
                text=[formatar_k(x) for x in v25_c], textposition='auto'
            ))
            fig_custos_yoy.add_trace(go.Bar(
                x=df_custos_comp['mes_nome'].str.upper(), y=v26_c, name='2026', marker_color='#13A3B5',
                text=[formatar_k(x) for x in v26_c], textposition='auto'
            ))
            fig_custos_yoy.update_traces(textangle=0)
            fig_custos_yoy.update_layout(
                title=tit_c, barmode='group', template='plotly_white',
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                bargap=0.15, bargroupgap=0.05
            )
            st.plotly_chart(fig_custos_yoy, use_container_width=True)
            
            df_tab_custos = pd.DataFrame({
                'Mês': df_custos_comp['mes_nome'].str.upper(),
                'Custos 2025': df_custos_comp[2025].apply(formatar_brl),
                'Custos 2026': df_custos_comp[2026].apply(formatar_brl),
                'Acumulado 2025': df_custos_comp['acum_2025'].apply(formatar_brl),
                'Acumulado 2026': df_custos_comp['acum_2026'].apply(formatar_brl)
            })
            st.dataframe(df_tab_custos, use_container_width=True)
        else:
            st.info("Nenhuma movimentação de Custos na Prestação de Serviço mapeada.")
