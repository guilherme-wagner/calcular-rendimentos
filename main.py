import streamlit as st 
import yfinance as yf
import pandas as pd
import pytz
from datetime import date, timedelta, datetime
from pdf_report import gerar_pdf

# Configurações da aba do navegador
st.set_page_config(
    page_title="Calculadora de Rendimentos",
    page_icon="💰"
)

# Cabeçalho
st.title("Calculadora de Porcentagem de Ativo")
st.header("Bem-Vindo(a)!!")

# Data atual para validações de entrada de dados
data_atual = datetime.now().date()

# Entradas do Usuário
col1, col2 = st.columns(2)

def ultimo_dia_util():
    data = date.today()

    while data.weekday() >= 5:
        data -= timedelta(days=1)

    return data

with col1:
    ativos_input = st.text_input(
        "Ativos (Ex: SNAG11, PETR3):",
    ).upper()

with col2:
    data_pagamento = st.date_input(
        "Data de pagamento",
        value=ultimo_dia_util(),
        max_value=date.today()
    )

# Inicializa a estrutura de dividendos e total acumulado se não estiver no session state
if 'dividendos_ativos' not in st.session_state:
    st.session_state.dividendos_ativos = {}
if 'soma_acumulada_dividendos' not in st.session_state:
    st.session_state.soma_acumulada_dividendos = 0.0

# Checkbox para incluir quantidade de cotas/ativo
informar_quantidade_cotas = st.checkbox("Informar QTD de cotas")

# Exibir o input de quantidade de cotas apenas se a soma acumulada estiver selecionada
col3 = st.columns(1)[0]
with col3:
    quantidade_cotas = []
    if informar_quantidade_cotas:
        quantidade_cotas_input = st.text_input("Quantidade de cotas para cada ativo (Ex: 10, 5): ", help="As quantidades devem ser separadas por vírgula conforme o exemplo. Caso seja informado apenas um número para vários ativos será considerado esse valor para ambos os ativos.")
        if quantidade_cotas_input:
            try:
                quantidade_cotas = [int(q.strip()) for q in quantidade_cotas_input.split(',') if q.strip().isdigit() and int(q.strip()) > 0]
                if len(quantidade_cotas) != len(quantidade_cotas_input.split(',')):
                    raise ValueError("Todas as entradas devem ser números inteiros positivos.")
            except ValueError as e:
                st.error(f"Entrada inválida na quantidade de cotas: {e}")
                quantidade_cotas = []

# Função para obter o valor do ativo
def obter_valor_fundo(ticker, data):
    try:
        ativo = yf.Ticker(ticker)
        dados = ativo.history(start=data, end=data + pd.Timedelta(days=1))
        if dados.empty:
            dados = ativo.history(start=data - pd.Timedelta(days=1), end=data + pd.Timedelta(days=1))
        return dados['Close'].iloc[0] if not dados.empty else None
    except Exception as e:
        st.error(f"Erro ao obter dados: {e}")
        return None

# Função para obter o dividendo
def obter_dividendo(ticker, data):
    try:
        ativo = yf.Ticker(ticker)
        dividendos = ativo.dividends
        dividendos = dividendos[dividendos.index.date <= data.date()]
        return dividendos.iloc[-1] if not dividendos.empty else None
    except Exception as e:
        return None

# Função para obter o preço médio mensal
def obter_precos_mensais_media(ticker, meses=5):
    try:
        fim = pd.Timestamp.now()
        inicio = fim - pd.DateOffset(months=meses)
        ativo = yf.Ticker(ticker)
        historico = ativo.history(start=inicio, end=fim)

        # Agrupar por mês e calcular a média de preços
        historico['Month'] = historico.index.to_period('M')
        precos_mensais = historico.groupby('Month')['Close'].mean().reset_index()
        
        # Formatar o preço médio
        precos_mensais['Month'] = precos_mensais['Month'].dt.to_timestamp().dt.strftime('%B %Y')
        precos_mensais['Close'] = precos_mensais['Close'].apply(lambda x: f'R$ {x:,.2f}')

        return precos_mensais.rename(columns={"Month": "Mês", "Close": "Preço Médio"})
    except Exception as e:
        st.error(f"Erro ao obter preços mensais: {e}")
        return None

# Função para calcular o rendimento por cota
def calcular(dividendo_por_cota, valor_fundo_num, quantidade_cotas):
    total_dividendo = dividendo_por_cota * quantidade_cotas
    rendimento = (dividendo_por_cota * 100) / valor_fundo_num  # Rendimento por cota
    return rendimento, total_dividendo

# Quando o botão "Calcular" é clicado
if st.button("Calcular"):
    if not ativos_input:
        st.warning("Por favor, insira os ativos.")
    elif informar_quantidade_cotas and not quantidade_cotas_input:
        st.warning("Por favor, insira a quantidade de cotas.")
    elif data_pagamento > data_atual:
        st.warning("A data não pode ser uma data futura! Por favor, insira uma data válida.")
    elif informar_quantidade_cotas and not quantidade_cotas:
        st.warning("Por favor, insira apenas números inteiros positivos para a quantidade de cotas.")
    else:
        # Define os ativos após todas as verificações
        ativos = [ativo.strip() + ".SA" if not ativo.strip().endswith(".SA") else ativo.strip() for ativo in ativos_input.split(',')]
        
        tz = pytz.timezone('America/Sao_Paulo')
        data_pagamento = tz.localize(pd.Timestamp(data_pagamento))

        resultados = []

        for i, ativo in enumerate(ativos):
            dividendo = obter_dividendo(ativo, data_pagamento)
            if dividendo is None:
                st.error(f"Não foi possível obter o valor do dividendo para {ativo}! Verifique o nome do ativo e a data.")
                continue
            
            chave = (ativo, data_pagamento.date())
            st.session_state.dividendos_ativos.setdefault(chave, 0)
            st.session_state.dividendos_ativos[chave] += dividendo
            
            valor_fundo_num = obter_valor_fundo(ativo, data_pagamento)
            if valor_fundo_num is not None:

                # Se o usuário não informou cotas, considera 1 cota
                quantidade_cota_atual = 1

                if informar_quantidade_cotas and quantidade_cotas:
                    quantidade_cota_atual = (
                        quantidade_cotas[i]
                        if i < len(quantidade_cotas)
                        else quantidade_cotas[0]
                    )

                # Usa a função para calcular tudo
                rendimento, total_dividendo = calcular(
                    dividendo,
                    valor_fundo_num,
                    quantidade_cota_atual
                )

                # Atualiza o total acumulado apenas se o usuário desejar
                if informar_quantidade_cotas:
                    st.session_state.soma_acumulada_dividendos += total_dividendo

                resultados.append({
                    "Mês": data_pagamento.strftime("%m/%Y"),
                    "Ativo": ativo.replace(".SA", ""),
                    "QTD Cotas": quantidade_cota_atual,
                    "Dividendo/Cota": dividendo,
                    "Total Recebido": total_dividendo,
                    "DY (%)": rendimento
                })

                # Obtém os preços médios dos últimos 6 meses
                precos_mensais = obter_precos_mensais_media(ativo)
                if precos_mensais is not None and not precos_mensais.empty:
                    with st.expander(f"📈 Preço médio (últimos 6 meses) - {ativo.replace('.SA','')}"):
                        st.dataframe(
                            precos_mensais,
                            use_container_width=True,
                            height=180,
                            hide_index=True
                        )
            else:
                st.error(f"Não foi possível obter o valor do fundo para {ativo}! Verifique o nome do ativo e a data e tente novamente.")
                
    # DataFrame original (mantém números)
    df = pd.DataFrame(resultados)

    # Guarda para uso futuro (PDF, Excel, etc.)
    st.session_state["df_resultado"] = df

    # Cria uma cópia apenas para exibição
    df_exibir = df.copy()
    total_recebido = df["Total Recebido"].sum()

    # Formata os campos para a interface
    df_exibir["Dividendo/Cota"] = df_exibir["Dividendo/Cota"].apply(
        lambda x: f"R$ {x:.2f}".replace(".", ",")
    )

    df_exibir["Total Recebido"] = df_exibir["Total Recebido"].apply(
        lambda x: f"R$ {x:.2f}".replace(".", ",")
    )

    df_exibir["DY (%)"] = df_exibir["DY (%)"].apply(
        lambda x: f"{x:.2f}%".replace(".", ",")
    )

    st.subheader("📊 Resultado")

    st.dataframe(
        df_exibir,
        use_container_width=True,
        hide_index=True
    )

    st.metric(
    "💰 TOTAL RECEBIDO:",
    f"R$ {total_recebido:.2f}".replace(".", ",")
    )

    # Botão para gerar pdf da consulta
    pdf = gerar_pdf(df)

    st.download_button(
        "📄 Baixar PDF",
        pdf,
        "rendimentos.pdf",
        "application/pdf"
    )

# Rodapé da página
st.markdown("---")
st.markdown("Desenvolvido por: [Guilherme Wagner](https://www.linkedin.com/in/guilherme-wagner)")
