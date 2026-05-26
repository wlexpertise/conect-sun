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
    
    # Higienização básica
    df = df[df[col_situacao].astype(str).str.strip().str.lower() == 'conciliado'].copy()
    if df[col_valor].dtype == object:
        df[col_valor] = df[col_valor].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
    df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0)
    df[col_data_pag] = pd.to_datetime(df[col_data_pag], errors='coerce', dayfirst=True)
    df = df.dropna(subset=[col_data_pag])
    
    # Períodos cronológicos
    df['ano'] = df[col_data_pag].dt.year
    df['mes'] = df[col_data_pag].dt.month
    df['ano_mes_num'] = df[col_data_pag].dt.strftime('%Y%m')
    meses_pt = {1: 'jan', 2: 'fev', 3: 'mar', 4: 'abr', 5: 'mai', 6: 'jun', 7: 'jul', 8: 'ago', 9: 'set', 10: 'out', 11: 'nov', 12: 'dez'}
    df['mes_nome_pt'] = df['mes'].map(meses_pt)
    df['ano_mes_texto'] = df['mes_nome_pt'] + '/' + df['ano'].astype(str)
    df['fluxo_limpo'] = df[col_tipo_fluxo].astype(str).str.strip().str.lower()
    
    return df, col_data_pag, col_contato, col_categoria, col_valor, col_grupo

df_base, col_data_pag, col_contato, col_categoria, col_valor, col_grupo = carregar_dados()

# 3. NAVEGAÇÃO LATERAL (MENU EXECUTIVO)
st.sidebar.image("Logo horizontal-fundo.png", use_container_width=True)
st.sidebar.markdown("---")
pagina = st.sidebar.radio("Navegação Estratégica:", ["🚀 Visão Geral (YTD)", "🔍 Detalhe Operacional", "👥 Gestão de Sócios", "🏗️ Insumos Operacionais"])

# Filtro de Mês unificado na Barra Lateral
df_ordenado = df_base.sort_values('ano_mes_num')
meses_disponiveis = df_ordenado['ano_mes_texto'].unique().tolist()
mes_selecionado = st.sidebar.selectbox("Selecione o Mês de Referência:", options=meses_disponiveis)

# Processamento dos subconjuntos de dados (Mês vs YTD)
reg_ref = df_base[df_base['ano_mes_texto'] == mes_selecionado].iloc[0]
df_ytd = df_base[(df_base['ano'] == reg_ref['ano']) & (df_base['mes'] <= reg_ref['mes'])].copy()
df_mes = df_base[df_base['ano_mes_texto'] == mes_selecionado].copy()


# --- PÁGINA 1: VISÃO GERAL (YTD) ---
if pagina == "🚀 Visão Geral (YTD)":
    st.title("Performance Financeira WL Expertise")
    st.subheader(f"Acumulado Estratégico (YTD) até {mes_selecionado.upper()}")
    
    ent_ytd = df_ytd[df_ytd['fluxo_limpo'] == 'entrada'][col_valor].sum()
    sai_ytd = df_ytd[df_ytd['fluxo_limpo'] == 'saída'][col_valor].sum()
    res_ytd = ent_ytd - sai_ytd
    
    c1, c2, c3 = st.columns(3)
    c1.metric("📈 Entradas Acumuladas", f"R$ {ent_ytd:,.2f}")
    c2.metric("📉 Saídas Acumuladas", f"R$ {sai_ytd:,.2f}")
    c3.metric("📊 Resultado Líquido", f"R$ {res_ytd:,.2f}", delta=f"{(res_ytd/ent_ytd*100):.1f}% Margem" if ent_ytd > 0 else "0%")

    st.markdown("---")
    st.markdown(f"### 📊 Evolução Mensal do Resultado Líquido de Caixa ({reg_ref['ano']})")
    
    # Tratamento blindado para o gráfico mensal sem unstack()
    df_ano_atual = df_base[df_base['ano'] == reg_ref['ano']].copy()
    base_meses = df_ano_atual[['ano_mes_num', 'ano_mes_texto']].drop_duplicates()
    
    df_ent_m = df_ano_atual[df_ano_atual['fluxo_limpo'] == 'entrada'].groupby('ano_mes_num')[col_valor].sum().reset_index(name='entrada')
    df_sai_m = df_ano_atual[df_ano_atual['fluxo_limpo'] == 'saída'].groupby('ano_mes_num')[col_valor].sum().reset_index(name='saída')
    
    df_hist = pd.merge(base_meses, df_ent_m, on='ano_mes_num', how='left').fillna(0)
    df_hist = pd.merge(df_hist, df_sai_m, on='ano_mes_num', how='left').fillna(0)
    df_hist['Resultado'] = df_hist['entrada'] - df_hist['saída']
    df_hist = df_hist.sort_values('ano_mes_num')
    
    # Montagem do gráfico com cores dinâmicas (Verde se positivo, Vermelho se negativo)
    fig_evolucao = go.Figure()
    fig_evolucao.add_trace(go.Bar(
        x=df_hist['ano_mes_texto'], 
        y=df_hist['Resultado'],
        marker_color=['#ef4444' if value < 0 else '#10b981' for value in df_hist['Resultado']],
        text=df_hist['Resultado'].apply(lambda x: f"R$ {x:,.0f}"), 
        textposition='auto'
    ))
    fig_evolucao.update_layout(
        template="plotly_dark", 
        margin=dict(t=10, b=10),
        xaxis_title="Meses de Competência",
        yaxis_title="Resultado Líquido (R$)"
    )
    st.plotly_chart(fig_evolucao, use_container_width=True)


# --- PÁGINA 2: DETALHE OPERACIONAL ---
elif pagina == "🔍 Detalhe Operacional":
    st.title("Detalhamento Operacional Executivo")
    st.markdown(f"Análise aprofundada dos fluxos de caixa para a competência de **{mes_selecionado.upper()}**")
    st.markdown("---")
    
    col_esq, col_dir = st.columns(2)
    
    with col_esq:
        st.markdown("### 👥 Volume de Entradas por Cliente")
        df_cli = df_mes[df_mes['fluxo_limpo'] == 'entrada'].groupby(col_contato)[col_valor].sum().reset_index()
        df_cli = df_cli.sort_values(col_valor, ascending=True).tail(10) # Top 10 maiores
        
        if not df_cli.empty:
            fig_cli = px.bar(
                df_cli, 
                x=col_valor, 
                y=col_contato, 
                orientation='h', 
                text_auto='.2s',
                color=col_valor, 
                color_continuous_scale='Mint', 
                template="plotly_dark",
                labels={col_contato: 'Cliente / Origem', col_valor: 'Valor Recebido'}
            )
            fig_cli.update_layout(coloraxis_showscale=False, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_cli, use_container_width=True)
        else:
            st.info("Nenhuma entrada registrada para este mês.")
            
    with col_dir:
        st.markdown("### 🏷️ Distribuição de Saídas por Categoria")
        
        # Filtro de grupo integrado no corpo para refinar a busca de categorias
        grupos_saidas = ["Todos"] + df_mes[df_mes['fluxo_limpo'] == 'saída'][col_grupo].dropna().unique().tolist()
        grupo_escolhido = st.selectbox("Refinar visualização por Grupo de Custo:", options=grupos_saidas)
        
        df_saidas_f = df_mes[df_mes['fluxo_limpo'] == 'saída']
        if grupo_escolhido != "Todos":
            df_saidas_f = df_saidas_f[df_saidas_f[col_grupo] == grupo_escolhido]
            
        df_cat = df_saidas_f.groupby(col_categoria)[col_valor].sum().reset_index()
        df_cat = df_cat.sort_values(col_valor, ascending=True) # Ordenação executiva
        
        if not df_cat.empty:
            # Gráfico de Barras Horizontal de Alta Legibilidade substituindo a Pizza poluída
            fig_cat = px.bar(
                df_cat,
                x=col_valor,
                y=col_categoria,
                orientation='h',
                text_auto='.2s',
                color=col_valor,
                color_continuous_scale='Reds',
                template="plotly_dark",
                labels={col_categoria: 'Categoria de Despesa', col_valor: 'Total Gasto'}
            )
            fig_cat.update_layout(coloraxis_showscale=False, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("Nenhuma saída mapeada para os critérios atuais.")


# --- PÁGINA 3: GESTÃO DE SÓCIOS ---
elif pagina == "👥 Gestão de Sócios":
    st.title("Controle de Retiradas de Sócios")
    st.markdown(f"Auditoria de retiradas, pró-labores e despesas compartilhadas em **{mes_selecionado.upper()}**")
    st.markdown("---")
    
    df_socios_mes = df_mes[df_mes[col_grupo].str.contains('SÓCIO', na=False, case=False)].copy()
    
    if not df_socios_mes.empty:
        list_socios = ["Todos"] + df_socios_mes[col_contato].unique().tolist()
        socio_sel = st.selectbox("Selecione o Sócio para Análise (Coluna Contato):", list_socios)
        
        if socio_sel != "Todos":
            df_socios_mes = df_socios_mes[df_socios_mes[col_contato] == socio_sel]
        
        total_socio = df_socios_mes[col_valor].sum()
        st.metric(f"Total de Retiradas — {socio_sel}", f"R$ {total_socio:,.2f}")
        
        st.markdown("### 📋 Histórico Detalhado do Período")
        st.dataframe(df_socios_mes[[col_data_pag, col_contato, 'Descrição', col_valor]], use_container_width=True)
        
        fig_soc = px.bar(df_socios_mes, x=col_data_pag, y=col_valor, color=col_contato, title="Distribuição de Retiradas na Linha do Tempo", template="plotly_dark")
        st.plotly_chart(fig_soc, use_container_width=True)
    else:
        st.info("Não foram encontradas transações vinculadas ao grupo de Sócios neste mês.")


# --- PÁGINA 4: INSUMOS OPERACIONAIS ---
elif pagina == "🏗️ Insumos Operacionais":
    st.title("Análise Estratégica de Insumos Operacionais")
    st.markdown(f"Acompanhamento analítico dos custos técnicos diretos em **{mes_selecionado.upper()}**")
    st.markdown("---")
    
    df_insumos = df_mes[df_mes[col_grupo].str.contains('INSUMOS OPERACIONAIS', na=False, case=False)].copy()
    
    if not df_insumos.empty:
        total_insumos = df_insumos[col_valor].sum()
        st.metric("Despesa Consolidada com Insumos", f"R$ {total_insumos:,.2f}")
        
        st.markdown("### 📊 Detalhamento de Custos por Categoria Técnica")
        df_ins_cat = df_insumos.groupby(col_categoria)[col_valor].sum().reset_index().sort_values(col_valor, ascending=True)
        
        fig_ins = px.bar(df_ins_cat, x=col_valor, y=col_categoria, orientation='h', text_auto='.2s', color=col_valor, color_continuous_scale='Oranges', template="plotly_dark")
        fig_ins.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig_ins, use_container_width=True)
        
        st.markdown("### 📑 Notas de Entrada e Ordens de Pagamento")
        st.dataframe(df_insumos[[col_data_pag, col_contato, 'Descrição', col_valor]], use_container_width=True)
    else:
        st.info("Nenhuma despesa de 'Insumos Operacionais' registrada para esta competência.")
