# ... [Seu código da Visão Geral (YTD) termina aqui em st.plotly_chart] ...

# --- PÁGINA 2: ANÁLISE DE ENTRADAS ---
elif pagina == "📈 Análise de Entradas":
    with header_col1:
        st.title("Análise de Entradas")
        st.subheader(f"Mês de Referência: {mes_selecionado.upper()}")
    with header_col2:
        st.markdown('<div class="logo-box">', unsafe_allow_html=True)
        st.image("conectlogo.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.info("Insira aqui os gráficos e métricas de Entradas.")
    # Exemplo: df_entradas = df_mes[df_mes['fluxo_limpo'] == 'entrada']

# --- PÁGINA 3: DETALHE DE SAÍDAS ---
elif pagina == "📉 Detalhe de Saídas":
    with header_col1:
        st.title("Detalhe de Saídas")
        st.subheader(f"Mês de Referência: {mes_selecionado.upper()}")
    with header_col2:
        st.markdown('<div class="logo-box">', unsafe_allow_html=True)
        st.image("conectlogo.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.info("Insira aqui os gráficos e métricas de Saídas.")
    # Exemplo: df_saidas = df_mes[df_mes['fluxo_limpo'] == 'saída']

# --- PÁGINA 4: GESTÃO DE SÓCIOS ---
elif pagina == "👥 Gestão de Sócios":
    with header_col1:
        st.title("Gestão de Sócios")
        st.subheader(f"Mês de Referência: {mes_selecionado.upper()}")
    with header_col2:
        st.markdown('<div class="logo-box">', unsafe_allow_html=True)
        st.image("conectlogo.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.info("Insira aqui a análise financeira referente aos sócios.")

# --- PÁGINA 5: CUSTOS NA PRESTAÇÃO DE SERVIÇO ---
elif pagina == "🏗️ Custos na Prestação de Serviço":
    with header_col1:
        st.title("Custos na Prestação de Serviço")
        st.subheader(f"Mês de Referência: {mes_selecionado.upper()}")
    with header_col2:
        st.markdown('<div class="logo-box">', unsafe_allow_html=True)
        st.image("conectlogo.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.info("Insira aqui a análise de custos diretos e indiretos dos serviços.")
