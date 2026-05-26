import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Painel Financeiro - WL Expertise",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. CARREGAMENTO E TRATAMENTO DOS DADOS
@st.cache_data
def carregar_dados():
    nome_do_arquivo = 'dados_conectsol.xlsx' 
    df = pd.read_excel(nome_do_arquivo)
    
    # Limpeza de nomes das colunas
    df.columns = df.columns.str.strip()
    
    # Mapeamento por posição real das colunas na planilha
    col_tipo_fluxo = df.columns[2]     # 3ª coluna: 'Tipo' (Entrada / Saída)
    col_data_pag = df.columns[4]       # 5ª coluna: 'Data de pagamento'
    col_contato = df.columns[7]        # 8ª coluna: 'Contato'
    col_categoria = df.columns[10]     # 11ª coluna: 'Categoria'
    col_situacao = df.columns[11]      # 12ª coluna: 'Situação' (Conciliado)
    col_valor = df.columns[12]         # 13ª coluna: 'Valor'
    col_grupo = df.columns[13]         # 14ª coluna: 'Grupo'
    
    # 🧼 TRATAMENTO E HIGIENIZAÇÃO
    # Filtrar apenas transações com status 'Conciliado'
    df = df[df[col_situacao].astype(str).str.strip().str.lower() == 'conciliado']
    
    # Limpeza profunda dos valores financeiros
    if df[col_valor].dtype == object:
        df[col_valor] = df[col_valor].astype(str).str.replace('R$', '', regex=False)
        df[col_valor] = df[col_valor].str.replace('.', '', regex=False)
        df[col_valor] = df[col_valor].str.replace(',', '.', regex=False)
        df[col_valor] = df[col_valor].str.strip()
    df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0)
    
    # Tratamento de Datas
    df[col_data_pag] = pd.to_datetime(df[col_data_pag], errors='coerce', dayfirst=True)
    df = df.dropna(subset=[col_data_pag])
    
    # Variáveis Auxiliares de Período
    df['ano'] = df[col_data_pag].dt.year
    df['mes'] = df[col_data_pag].dt.month
    df['ano_mes_num'] = df[col_data_pag].dt.strftime('%Y%m')
    
    meses_pt = {1: 'jan', 2: 'fev', 3: 'mar', 4: 'abr', 5: 'mai', 6: 'jun',
                7: 'jul', 8: 'ago', 9: 'set', 10: 'out', 11: 'nov', 12: 'dez'}
    df['mes_nome_pt'] = df[col_data_pag].dt.month.map(meses_pt)
    df['ano_mes_texto'] = df['mes_nome_pt'] + '/' + df['ano'].astype(str)
    
    # Padronização de fluxo para termos textuais exatos
    df['fluxo_limpo'] = df[col_tipo_fluxo].astype(str).str.strip().str.lower()
    
    return df, col_data_pag, col_contato, col_categoria, col_valor, col_grupo

try:
    df_base, col_data_pag, col_contato, col_categoria, col_valor, col_grupo = carregar_dados()
except Exception as e:
    st.error(f"Erro ao processar a planilha: {e}")
    st.stop()


# 3. BARRA LATERAL (MENU EXCLUSIVO PARA NAVEGAÇÃO)
st.sidebar.image("Logo horizontal-fundo.png", use_container_width=True)
st.sidebar.markdown("---")
st.sidebar.markdown("### 🗺️ NAVEGAÇÃO")
pagina = st.sidebar.radio("Ir para:", ["📊 Dashboard Financeiro", "📄 Outras Páginas (Em breve)"])


# 4. CORPO DO DASHBOARD
if pagina == "📊 Dashboard Financeiro":
    st.title("Painel Financeiro & Business Intelligence")
    st.markdown("Análise de Performance de Caixa Integrada — **Conectsol Engenharia**")
    st.markdown("---")
    
    # 📆 SELEÇÃO DE MÊS NO CORPO DO DASHBOARD
    df_ordenado = df_base.sort_values('ano_mes_num')
    meses_disponiveis = df_ordenado['ano_mes_texto'].unique().tolist()
    
    if meses_disponiveis:
        f1, f2 = st.columns([2, 4])
        with f1:
            mes_selecionado = st.selectbox(
                "📅 Selecione o Mês de Referência:",
                options=meses_disponiveis
            )
        
        # Coleta metadados do mês escolhido para o YTD
        registro_ref = df_base[df_base['ano_mes_texto'] == mes_selecionado].iloc[0]
        ano_ref = registro_ref['ano']
        mes_ref = registro_ref['mes']
        
        # 📊 CÁLCULO DO YTD (Year-To-Date)
        df_ytd = df_base[(df_base['ano'] == ano_ref) & (df_base['mes'] <= mes_ref)]
        
        entradas_ytd = df_ytd[df_ytd['fluxo_limpo'] == 'entrada'][col_valor].sum()
        saidas_ytd = df_ytd[df_ytd['fluxo_limpo'] == 'saída'][col_valor].sum()
        resultado_ytd = entradas_ytd - saidas_ytd
        margem_ytd = (resultado_ytd / entradas_ytd * 100) if entradas_ytd > 0 else 0
        
        # Filtro para os gráficos detalhados do mês atual
        df_mes = df_base[df_base['ano_mes_texto'] == mes_selecionado].copy()
        
    else:
        st.warning("Nenhum dado financeiro 'Conciliado' foi encontrado.")
        st.stop()

    # 5. CARDS DE PERFORMANCE ACUMULADA (YTD)
    st.markdown(f"#### 🚀 Indicadores YTD (Acumulado de Jan/{ano_ref} até {mes_selecionado.upper()})")
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric(label="📈 Total de Entradas Acumuladas", value=f"R$ {entradas_ytd:,.2f}")
    kpi2.metric(label="📉 Total de Saídas Acumuladas", value=f"R$ {saidas_ytd:,.2f}")
    kpi3.metric(label="📊 Resultado Líquido Acumulado", value=f"R$ {resultado_ytd:,.2f}", delta=f"{margem_ytd:.1f}% Margem")
    
    st.markdown("---")

    # 6. GRÁFICO HISTÓRICO MENSAL DO ANO (CORRIGIDO)
    st.markdown(f"### 📈 Evolução de Resultado Mensal ({ano_ref})")
    df_ano_atual = df_base[df_base['ano'] == ano_ref].copy()
    
    # Agrupamento estruturado usando a coluna tratada 'fluxo_limpo'
    df_historico = df_ano_atual.groupby(['ano_mes_num', 'ano_mes_texto', 'fluxo_limpo'])[col_valor].sum().unstack(fill_value=0).reset_index()
    
    # Garante a existência das colunas para evitar novos erros de chave
    if 'entrada' not in df_historico.columns: df_historico['entrada'] = 0
    if 'saída' not in df_historico.columns: df_historico['saída'] = 0
    
    df_historico['Resultado Líquido'] = df_historico['entrada'] - df_historico['saída']
    df_historico = df_historico.sort_values('ano_mes_num')
    
    fig_hist = px.bar(
        df_historico,
        x='ano_mes_texto',
        y='Resultado Líquido',
        text_auto='.2s',
        color='Resultado Líquido',
        color_continuous_scale='RdYlGn',
        labels={'ano_mes_texto': 'Mês de Caixa', 'Resultado Líquido': 'Resultado Operacional (R$)'}
    )
    fig_hist.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("---")

    # 7. SEÇÃO DE ANÁLISE OPERACIONAL
    st.markdown(f"### 🔍 Detalhamento Operacional: Mês `{mes_selecionado.upper()}`")
    
    col_esquerda, col_direita = st.columns(2)
    
    with col_esquerda:
        st.markdown("### 🍕 Saídas por Categoria")
        
        grupos_disponiveis = ["Todos"] + df_mes[df_mes['fluxo_limpo'] == 'saída'][col_grupo].dropna().unique().tolist()
        grupo_escolhido = st.selectbox("Filtrar gastos por Grupo:", options=grupos_disponiveis)
        
        df_saidas_mes = df_mes[df_mes['fluxo_limpo'] == 'saída']
        if grupo_escolhido != "Todos":
            df_saidas_mes = df_saidas_mes[df_saidas_mes[col_grupo] == grupo_escolhido]
            
        df_cat = df_saidas_mes.groupby(col_categoria)[col_valor].sum().reset_index()
        df_cat = df_cat[df_cat[col_valor] > 0]
        
        if not df_cat.empty:
            fig_cat = px.pie(
                df_cat, 
                values=col_valor, 
                names=col_categoria, 
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_cat.update_layout(legend=dict(orientation="h", y=-0.15))
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("Nenhum registro de saída encontrado para os filtros selecionados.")
            
    with col_direita:
        st.markdown("### 👥 Entradas por Cliente")
        st.markdown("<div style='margin-bottom: 68px;'></div>", unsafe_allow_html=True)
        
        df_entradas_mes = df_mes[df_mes['fluxo_limpo'] == 'entrada']
        df_cli = df_entradas_mes.groupby(col_contato)[col_valor].sum().reset_index()
        df_cli = df_cli[df_cli[col_valor] > 0].sort_values(by=col_valor, ascending=False).head(10)
        
        if not df_cli.empty:
            fig_cli = px.bar(
                df_cli,
                x=col_valor,
                y=col_contato,
                orientation='h',
                text_auto='.2s',
                color=col_valor,
                color_continuous_scale='Mint',
                labels={col_contato: 'Cliente / Origem', col_valor: 'Total Recebido (R$)'}
            )
            fig_cli.update_layout(coloraxis_showscale=False, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_cli, use_container_width=True)
        else:
            st.info("Nenhuma entrada registrada neste mês.")

else:
    st.title("Páginas Adicionais")
    st.info("Utilize a barra lateral para retornar ao Dashboard Financeiro principal.")
