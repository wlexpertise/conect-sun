@st.cache_data
def carregar_dados():
    nome_do_arquivo = 'dados_conectsol.xlsx' 
    df = pd.read_excel(nome_do_arquivo)
    df.columns = df.columns.str.strip()
    
    # Mapeamento seguro
    col_data_pag = df.columns[4]
    col_contato = df.columns[7]
    col_categoria = df.columns[10]
    col_situacao = df.columns[11]
    col_valor = df.columns[12]
    col_grupo = df.columns[13]
    col_tipo_p = df.columns[15]
    
    # 1. Filtro de Situação (O único necessário na base)
    df['situacao_limpa'] = df[col_situacao].astype(str).str.strip().str.lower()
    df = df[df['situacao_limpa'].isin(['conciliado', 'sem conciliação'])].copy()
    
    # 2. Tratamento numérico robusto
    df[col_valor] = pd.to_numeric(df[col_valor].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0)
    
    # 3. Tratamento de Datas
    df[col_data_pag] = pd.to_datetime(df[col_data_pag], errors='coerce', dayfirst=True)
    df = df.dropna(subset=[col_data_pag])
    
    # 4. Colunas de tempo
    df['ano'] = df[col_data_pag].dt.year
    df['mes'] = df[col_data_pag].dt.month
    df['ano_mes_num'] = df[col_data_pag].dt.strftime('%Y%m')
    meses_pt = {1: 'jan', 2: 'fev', 3: 'mar', 4: 'abr', 5: 'mai', 6: 'jun', 7: 'jul', 8: 'ago', 9: 'set', 10: 'out', 11: 'nov', 12: 'dez'}
    df['ano_mes_texto'] = df['mes'].map(meses_pt) + '/' + df['ano'].astype(str)
    
    # 5. Fluxo (Sem filtrar o DataFrame)
    df['tipo_p_limpo'] = df[col_tipo_p].astype(str).str.strip().str.upper()
    df['fluxo_limpo'] = 'outros'
    df.loc[df['tipo_p_limpo'] == 'VENDA', 'fluxo_limpo'] = 'entrada'
    df.loc[df['tipo_p_limpo'].isin(['CUSTO', 'DESPESA']), 'fluxo_limpo'] = 'saída'
    
    return df, col_data_pag, col_contato, col_categoria, col_valor, col_grupo
