import streamlit as st
import yfinance as yf
import pandas as pd
import pytz

# Configurações da aba do navegador
st.set_page_config(
    page_title="Calculadora de Rendimentos",
    page_icon="💰"
)

# Cabeçalho
st.title("Calculadora de Porcentagem de Ativo")
st.header("Bem-Vindo(a)!!")

# Inputs do Usuário
ativo = st.text_input("Digite o nome do ativo (Ex: MXRF11): ").upper()
if ativo and not ativo.endswith(".SA"):
    ativo += ".SA"
data_pagamento = st.date_input("Data do pagamento: ", value=None)
qtd_cotas = st.number_input("Insira a quantidade de cotas que você possui: ", min_value=1)
dividendo = st.number_input("Insira o valor recebido do dividendo R$: ", min_value=0.0)
bot_calcular = st.button("Calcular")

# Função para obter o valor do ativo
def obter_valor_fundo(ticker, data):
    try:
        ativo = yf.Ticker(ticker)
        dados = ativo.history(start=data, end=data + pd.Timedelta(days=1))
        return dados['Close'].iloc[0] if not dados.empty else None
    except Exception as e:
        st.error(f"Erro ao obter dados: {e}")
        return None

# Função para calcular o rendimento
def calcular(dividendo, qtd_cotas, valor_fundo_num):
    dividendo_cota = dividendo / qtd_cotas
    calculo = (dividendo_cota * 100) / valor_fundo_num
    return calculo

# Quando o botão "Calcular" é clicado
if bot_calcular:
    # Validações dos inputs
    if not ativo:
        st.warning("Por favor, insira um ativo.")
    elif data_pagamento is None:
        st.warning("Por favor, selecione uma data.")
    elif dividendo == 0.00:
        st.warning("Valor recebido do dividendo não pode ser zero!")
    # Realiza o cálculo se os inputs estiverem corretos
    else:
        tz = pytz.timezone('America/Sao_Paulo')  # Fuso horário de Brasília (UTC-3)
        data_pagamento = tz.localize(pd.Timestamp(data_pagamento))

        valor_fundo_num = obter_valor_fundo(ativo, data_pagamento)
        if valor_fundo_num is not None:
            rendimento = calcular(dividendo, qtd_cotas, valor_fundo_num)
            st.success(f"Rendimento por cota: {rendimento:.2f}%")
        else:
            st.error("Não foi possível obter o valor do fundo! Verifique o nome do ativo e tente novamente.")

# Rodapé da página
st.markdown("---")
st.markdown("Desenvolvido por: [Guilherme Wagner](https://www.linkedin.com/in/guilherme-wagner)")
