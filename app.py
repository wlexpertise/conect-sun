import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Configuração da Página (Modo Wide para simular o Power BI)
st.set_page_config(
    page_title="WL Expertise - Dashboard Financeiro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilização CSS para embutir as cores da WL Expertise e fontes limpas
st.markdown("""
    <style>
    .main { background-color: #F8F9FA; }
    div[data-testid="stMetricValue"] > div { font-weight: bold; }
    .kpi-container {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #0B5A60;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# 2. Paleta de Cores WL Expertise
COLOR_PRIMARY = "#0B5A60"    # Verde Escuro Corporativo
COLOR_SECONDARY = "#13A3B5"  # Azul Piscina / Ciano
COLOR_SUCCESS = "#28B260"    # Verde Sucesso
COLOR_MUTED = "#E9ECEF"

# 3. Carregamento e Tratamento dos Dados
@st.cache_data
def load_data():
    # Substitua pela URL do seu arquivo CSV bruto hospedado no GitHub
    # Exemplo: "https://raw.githubusercontent.com/usuario/repositorio/main/financeiro.csv"
    github_url = "https://raw.githubusercontent.com/seu_usuario/seu_repositorio/main/financeiro.csv"
    
    try:
        df = pd.read_csv(github_url, sep='\t', encoding='utf-8')
    except Exception:
        # Fallback de Contingência com Amostra dos seus dados caso esteja rodando localmente
        data_mock = [
            ["756","Saída","02/01/2026","FUN - EDUARDO HENRIQUE","SALARIO JANEIRO","Salários e Ordenados","Conciliado",1480.00,"DESPESA COM PESSOAL","Sicoob","DESPESA",1,"1º Tri"],
            ["756","Saída","02/01/2026","BELENUS LTDA","EQUIPAMENTO ESCOLA","Insumos Operacionais","Conciliado",21147.43,"CUSTOS NA PRESTAÇÃO DE SERVIÇO","Sicoob","CUSTO",1,"1º Tri"],
            ["756","Entrada","12/01/2026","AUGUSTO DE PAULA PEREIRA","ENTRADA","Instalação Fotovoltáica","Conciliado",8000.00,"SERVIÇOS","Sicoob","VENDA",1,"1º Tri"],
            ["756","Entrada","14/01/2026","RODRIGO SOUZA NOGUEIRA","BOLETO 3/4","Instalação Fotovoltáica","Conciliado",26600.00,"SERVIÇOS","Sicoob","VENDA",1,"1º Tri"],
            ["756","Saída","20/01/2026","MINISTERIO DA FAZENDA","SIMPLES NACIONAL","Simples Nacional","Conciliado",1935.62,"IMPOSTOS OPERACIONAIS","Sicoob","DESPESA",1,"1º Tri"],
            ["756","Entrada","29/01/2026","GELA GUELA FORMIGA","ENTRADA MATERIAIS","Instalação Fotovoltáica","Conciliado",20000.00,"SERVIÇOS","Sicoob","VENDA",1,"1º Tri"],
            ["756","Saída","02/02/2026","LEONARDO MACIEL GOMES","RUFO E PROTECOES","Insumos Operacionais","Conciliado",650.00,"CUSTOS NA PRESTAÇÃO DE SERVIÇO","Sicoob","CUSTO",2,"1º Tri"]
        ]
        columns = ["Banco", "Tipo_Transacao", "Data", "Contato", "Descricao", "Categoria", "Situacao", "Valor", "Grupo", "Instituicao", "Tipo", "Mes", "Tri"]
        df = pd.DataFrame(data_mock, columns=columns)
    
    # Garantir tipagens corretas
    df["Valor"] = pd.to_numeric(df["Valor"], errors='coerce').fillna(0.0)
    df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y", errors='coerce')
    df["Mes_Nome"] = df["Mes"].map({1: "Janeiro", 2: "Fevereiro", 3: "Março"})
    return df

df = load_data()

# 4. Cabeçalho com Logo WL Expertise
col_logo, col_title = st.columns([1, 4])
with col_logo:
    # IMPORTANTE: Altere para o caminho da sua imagem no GitHub ou localmente
    st.image("Logo horizontal-fundo.png", width=220) 
with col_title:
    st.markdown(f"<h1 style='color: {COLOR_PRIMARY}; margin-top: 10px;'>Painel de Performance Financeira</h1>", unsafe_allow_html=True)
    st.markdown("---")

# 5. Painel de Filtros Superiores (Estilo Slicer do Power BI)
st.markdown("### 🎛️ Filtros Gerenciais")
col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    meses_disponiveis = ["Todos"] + list(df["Mes_Nome"].dropna().unique())
    mes_selecionado = st.selectbox("Selecione o Mês:", meses_disponiveis)

with col_f2:
    grupos_disponiveis = ["Todos"] + list(df["Grupo"].dropna().unique())
    grupo_selecionado = st.selectbox("Filtrar por Grupo Dinâmico:", grupos_disponiveis)

with col_f3:
    situacao_disponivel = ["Todos"] + list(df["Situacao"].dropna().unique())
    situacao_selecionada = st.selectbox("Status de Conciliação:", situacao_disponivel)

# Aplicando os filtros dinamicamente ao DataFrame
df_filtered = df.copy()
if mes_selecionado != "Todos":
    df_filtered = df_filtered[df_filtered["Mes_Nome"] == mes_selecionado]
if grupo_selecionado != "Todos":
    df_filtered = df_filtered[df_filtered["Grupo"] == grupo_selecionado]
if situacao_selecionada != "Todos":
    df_filtered = df_filtered[df_filtered["Situacao"] == situacao_selecionada]

# 6. Cálculo das Métricas de FP&A
receita_total = df_filtered[df_filtered["Tipo"] == "VENDA"]["Valor"].sum()
custo_total = df_filtered[df_filtered["Tipo"] == "CUSTO"]["Valor"].sum()
despesa_total = df_filtered[df_filtered["Tipo"] == "DESPESA"]["Valor"].sum()

lucro_liquido = receita_total - (custo_total + despesa_total)
margem_lucro = (lucro_liquido / receita_total * 100) if receita_total > 0 else 0.0

# 7. Exibição dos Cards de KPI (Linha Superior)
col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

with col_kpi1:
    st.markdown(f"""
    <div class='kpi-container' style='border-left-color: {COLOR_SECONDARY};'>
        <p style='margin:0; font-size:14px; color:gray;'>RECEITA TOTAL</p>
        <h2 style='margin:0; color:{COLOR_SECONDARY};'>R$ {receita_total:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)

with col_kpi2:
    st.markdown(f"""
    <div class='kpi-container' style='border-left-color: #E67E22;'>
        <p style='margin:0; font-size:14px; color:gray;'>CUSTOS OPERACIONAIS</p>
        <h2 style='margin:0; color:#E67E22;'>R$ {custo_total:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)

with col_kpi3:
    st.markdown(f"""
    <div class='kpi-container' style='border-left-color: #E74C3C;'>
        <p style='margin:0; font-size:14px; color:gray;'>DESPESAS ADMINISTRATIVAS</p>
        <h2 style='margin:0; color:#E74C3C;'>R$ {despesa_total:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)

with col_kpi4:
    color_lucro = COLOR_SUCCESS if lucro_liquido >= 0 else "#E74C3C"
    st.markdown(f"""
    <div class='kpi-container' style='border-left-color: {color_lucro};'>
        <p style='margin:0; font-size:14px; color:gray;'>LUCRO LÍQUIDO (Margem %)</p>
        <h2 style='margin:0; color:{color_lucro};'>R$ {lucro_liquido:,.2f} <span style='font-size:16px;'>({margem_lucro:.1f}%)</span></h2>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 8. Bloco de Gráficos e Insights Visuais
col_graph1, col_graph2 = st.columns(2)

with col_graph1:
    st.markdown(f"<h4 style='color: {COLOR_PRIMARY};'>Evolução Diária do Fluxo de Caixa</h4>", unsafe_allow_html=True)
    df_trend = df_filtered.groupby(["Data", "Tipo"])["Valor"].sum().reset_index()
    
    fig_trend = px.line(
        df_trend, 
        x="Data", 
        y="Valor", 
        color="Tipo",
        color_discrete_map={"VENDA": COLOR_SUCCESS, "CUSTO": "#E67E22", "DESPESA": "#E74C3C"},
        template="simple_white"
    )
    fig_trend.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=320)
    st.plotly_chart(fig_trend, use_container_width=True)

with col_graph2:
    st.markdown(f"<h4 style='color: {COLOR_PRIMARY};'>Análise de Gastos por Grupo de Conta</h4>", unsafe_allow_html=True)
    df_gastos = df_filtered[df_filtered["Tipo"].isin(["CUSTO", "DESPESA"])]
    df_gastos_grouped = df_gastos.groupby("Grupo")["Valor"].sum().reset_index().sort_values(by="Valor", ascending=True)
    
    fig_bar = px.bar(
        df_gastos_grouped,
        x="Valor",
        y="Grupo",
        orientation="h",
        color_discrete_sequence=[COLOR_PRIMARY],
        template="simple_white"
    )
    fig_bar.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=320, xaxis_title="Total (R$)", yaxis_title="")
    st.plotly_chart(fig_bar, use_container_width=True)

# 9. Visão de Detalhes Adicionais e Tabela Comercial
col_sub1, col_sub2 = st.columns([1, 2])

with col_sub1:
    st.markdown(f"<h4 style='color: {COLOR_PRIMARY};'>Distribuição Bancária</h4>", unsafe_allow_html=True)
    df_bank = df_filtered.groupby("Instituicao")["Valor"].sum().reset_index()
    fig_pie = px.pie(
        df_bank, 
        values="Valor", 
        names="Instituicao", 
        color_discrete_sequence=[COLOR_PRIMARY, COLOR_SECONDARY, "#BDC3C7"],
        hole=0.4
    )
    fig_pie.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=260, showlegend=True)
    st.plotly_chart(fig_pie, use_container_width=True)

with col_sub2:
    st.markdown(f"<h4 style='color: {COLOR_PRIMARY};'>Detalhamento Analítico dos Lançamentos</h4>", unsafe_allow_html=True)
    # Seleção de colunas estratégicas para visualização limpa
    df_view = df_filtered[["Data", "Tipo_Transacao", "Contato", "Categoria", "Grupo", "Valor"]].copy()
    df_view["Data"] = df_view["Data"].dt.strftime('%d/%m/%Y')
    df_view["Valor"] = df_view["Valor"].map("R$ {:,.2f}".format)
    
    st.dataframe(df_view, height=240, use_container_width=True)

st.markdown("---")
st.caption("WL Expertise — Controladoria e Business Intelligence orientados a resultados. Dados atualizados via GitHub.")