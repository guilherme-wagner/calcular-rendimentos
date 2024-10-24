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
ativos_input = st.text_input("Digite os nomes dos ativos (Ex: SNAG11, PETR3): ", help="Os ativos devem ser separados por vírgula conforme o exemplo.").upper()
data_pagamento = st.date_input("Data do pagamento: ")

# Inicializa a estrutura de dividendos e total acumulado se não estiver no session state
if 'dividendos_ativos' not in st.session_state:
    st.session_state.dividendos_ativos = {}
if 'soma_acumulada_dividendos' not in st.session_state:
    st.session_state.soma_acumulada_dividendos = 0.0

# Checkbox para incluir a soma acumulada dos dividendos
calcular_soma_dividendos = st.checkbox("Incluir soma acumulada dos dividendos")

# Exibir o input de quantidade de cotas apenas se a soma acumulada estiver selecionada
quantidade_cotas = []
if calcular_soma_dividendos:
    quantidade_cotas_input = st.text_input("Digite a quantidade de cotas para cada ativo (Ex: 10, 5): ", help="As quantidades devem ser separadas por vírgula conforme o exemplo. Caso seja informado apenas um número para vários ativos será considerado esse valor para ambos os ativos.")
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
    elif calcular_soma_dividendos and not quantidade_cotas_input:
        st.warning("Por favor, insira a quantidade de cotas.")
    elif data_pagamento > data_atual:
        st.warning("A data não pode ser uma data futura! Por favor, insira uma data válida.")
    elif calcular_soma_dividendos and not quantidade_cotas:
        st.warning("Por favor, insira apenas números inteiros positivos para a quantidade de cotas.")
    else:
        # Define os ativos após todas as verificações
        ativos = [ativo.strip() + ".SA" if not ativo.strip().endswith(".SA") else ativo.strip() for ativo in ativos_input.split(',')]
        
        tz = pytz.timezone('America/Sao_Paulo')
        data_pagamento = tz.localize(pd.Timestamp(data_pagamento))

        for ativo in ativos:
            dividendo = obter_dividendo(ativo, data_pagamento)
            if dividendo is None:
                st.error(f"Não foi possível obter o valor do dividendo para {ativo}! Verifique o nome do ativo e a data.")
                continue
            
            chave = (ativo, data_pagamento.date())
            st.session_state.dividendos_ativos.setdefault(chave, 0)
            st.session_state.dividendos_ativos[chave] += dividendo
            
            valor_fundo_num = obter_valor_fundo(ativo, data_pagamento)
            if valor_fundo_num is not None:
                total_dividendo = dividendo
                if calcular_soma_dividendos and quantidade_cotas:
                    total_dividendo *= quantidade_cotas[0]  # Usar a primeira quantidade se várias forem dadas
                    st.session_state.soma_acumulada_dividendos += total_dividendo

                rendimento = (dividendo * 100) / valor_fundo_num  # Rendimento por cota
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

        # Exibe a soma acumulada dos dividendos ao final, se selecionado
        if calcular_soma_dividendos:
            st.success(f"Soma acumulada dos dividendos dos ativos consultados: R$ {st.session_state.soma_acumulada_dividendos:.2f}")

# Rodapé da página
st.markdown("---")
st.markdown("Desenvolvido por: [Guilherme Wagner](https://www.linkedin.com/in/guilherme-wagner)")
