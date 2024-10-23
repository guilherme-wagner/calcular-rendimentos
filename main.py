import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime

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
ativos_input = st.text_input("Digite os nomes dos ativos (Ex: SNAG11, XPCA11): ", help="Os ativos devem ser separados por vírgula conforme o exemplo.").upper()
ativos = [ativo.strip() + ".SA" if not ativo.strip().endswith(".SA") else ativo.strip() for ativo in ativos_input.split(',')]
data_pagamento = st.date_input("Data do pagamento: ")

# Função para obter o valor do ativo
def obter_valor_fundo(ticker, data):
    try:
        ativo = yf.Ticker(ticker)
        dados = ativo.history(start=data, end=data + pd.Timedelta(days=1))
        if not dados.empty:
            return dados['Close'].iloc[0]
        else:
            data_anterior = data - pd.Timedelta(days=1)
            dados_anterior = ativo.history(start=data_anterior, end=data_anterior + pd.Timedelta(days=1))
            return dados_anterior['Close'].iloc[0] if not dados_anterior.empty else None
    except Exception as e:
        st.error(f"Erro ao obter dados: {e}")
        return None

# Função para obter o dividendo
def obter_dividendo(ticker, data):
    try:
        ativo = yf.Ticker(ticker)
        dividendos = ativo.dividends
        dividendos = dividendos[dividendos.index.date <= data.date()]
        if not dividendos.empty:
            return dividendos.iloc[-1]
        return None
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
def calcular(dividendo_por_cota, valor_fundo_num):
    calculo = (dividendo_por_cota * 100) / valor_fundo_num
    return calculo

# Quando o botão "Calcular" é clicado
if st.button("Calcular"):
    if not ativos_input:
        st.warning("Por favor, insira pelo menos um ativo.")
    elif data_pagamento > data_atual:
        st.warning("A data não pode ser uma data futura! Por favor, insira uma data válida.")
    else:
        tz = pytz.timezone('America/Sao_Paulo')
        data_pagamento = tz.localize(pd.Timestamp(data_pagamento))

        for ativo in ativos:
            dividendo = obter_dividendo(ativo, data_pagamento)
            if dividendo is None:
                st.error(f"Não foi possível obter o valor do dividendo para {ativo}! Verifique o nome do ativo e a data.")
                continue
            
            valor_fundo_num = obter_valor_fundo(ativo, data_pagamento)
            if valor_fundo_num is not None:
                rendimento = calcular(dividendo, valor_fundo_num)
                st.success(f"Rendimento por cota de {ativo}: {rendimento:.2f}%")

                # Obtém os preços médios dos últimos 6 meses
                precos_mensais = obter_precos_mensais_media(ativo)
                if precos_mensais is not None and not precos_mensais.empty:
                    st.subheader(f"Preço Médio de {ativo} nos Últimos 6 Meses")
                    st.dataframe(precos_mensais)
                else:
                    st.warning(f"Nenhum preço médio encontrado para {ativo} no período especificado.")
            else:
                st.error(f"Não foi possível obter o valor do fundo para {ativo}! Verifique o nome do ativo e a data e tente novamente.")

# Rodapé da página
st.markdown("---")
st.markdown("Desenvolvido por: [Guilherme Wagner](https://www.linkedin.com/in/guilherme-wagner)")
