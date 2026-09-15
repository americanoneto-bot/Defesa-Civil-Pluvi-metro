import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Defesa Civil Santos - Caderneta Oficial Saboó (P6)",
    layout="wide",
)

st.title("🛡️ Defesa Civil de Santos | Posto Morro do Saboó (P6)")
st.markdown(
    "Caderneta de Campo Digital — Insira os índices pluviométricos nas células de horários (3 em 3h) "
    "e acompanhe o cálculo automático dos acumulados diários, 72h e mensais."
)

# Horários oficiais de medição de 3 em 3 horas da Defesa Civil
horarios_3h = [
    "06:00", "09:00", "12:00", "15:00", 
    "18:00", "21:00", "00:00", "03:00 (dia seguinte)"
]

# Inicializando a matriz de dias (colunas 1 a 31) x horários (linhas) no session_state
dias_mes = [f"Dia {i}" for i in range(1, 32)]

if 'matriz_caderneta' not in st.session_state:
    # Cria uma tabela vazia ou com zeros para simular a grade da folha de campo
    df_inicial = pd.DataFrame(0.0, index=horarios_3h, columns=dias_mes)
    st.session_state['matriz_caderneta'] = df_inicial

st.sidebar.header("⚙️ Parâmetros Operacionais")
st.sidebar.info(
    "**Instruções de Preenchimento:**\n"
    "• Insira os valores de chuva (mm) nos horários correspondentes de 3 em 3 horas.\n"
    "• Os totais diários, acumulados de 72h e mensais serão calculados automaticamente no rodapé."
)

st.subheader("📝 Grade de Lançamento por Horário (Entradas de 3 em 3h)")
st.markdown("Edite os campos da matriz abaixo conforme os boletins de campo:")

# Tabela interativa onde o operador insere os dados nos horários
matriz_editada = st.data_editor(
    st.session_state['matriz_caderneta'],
    use_container_width=True,
    key="editor_matriz_horarios"
)

st.session_state['matriz_caderneta'] = matriz_editada

# --- CÁLCULOS AUTOMÁTICOS DE RODAPÉ (Lógica da Defesa Civil) ---
# 1. Total Diário: soma de todas as leituras de 3h de cada dia (coluna)
total_diario = matriz_editada.sum(axis=0)

# 2. Acumulado de 72h (3 dias móveis): soma do dia atual + os 2 dias anteriores
acumulado_72h = pd.Series(0.0, index=dias_mes)
for i in range(len(dias_mes)):
    if i == 0:
        acumulado_72h.iloc[i] = total_diario.iloc[i]
    elif i == 1:
        acumulado_72h.iloc[i] = total_diario.iloc[i-1] + total_diario.iloc[i]
    else:
        acumulado_72h.iloc[i] = total_diario.iloc[i-2] + total_diario.iloc[i-1] + total_diario.iloc[i]

# 3. Acumulado Mensal Progressivo
acumulado_mensal = total_diario.cumsum()

# Montando a tabela de resultados automáticos (Linhas Azuis de Rodapé)
df_resultados = pd.DataFrame({
    "Total Diário (mm)": total_diario,
    "Acumulado 72h (mm)": acumulado_72h,
    "Acumulado Mensal (mm)": acumulado_mensal
}).T # Trans põe para ficar com os dias nas colunas, igual à caderneta física

st.markdown("---")
st.subheader("🔵 Resultados Automáticos (Linhas de Rodapé / Acumulados)")
st.markdown("Valores calculados em tempo real com base nas inserções horárias:")

# Exibe a tabela de resultados com destaque visual
st.dataframe(df_resultados, use_container_width=True)

# Identificando o último dia preenchido ou o dia atual para checagem de alerta
# Pegamos o dia com maior índice recente ou a última coluna com dados
ultimos_valores_72h = acumulado_72h[total_diario > 0]
max_72h_atual = ultimos_valores_72h.iloc[-1] if not ultimos_valores_72h.empty else acumulado_72h.iloc[0]

st.markdown("---")
st.subheader("🚨 Status Operacional Crítico (Morro do Saboó)")

if max_72h_atual >= 80.0:
    st.error(
        f"⚠️ **ALERTA MÁXIMO / ATENÇÃO:** O acumulado móvel de 72 horas atingiu "
        f"**{max_72h_atual:.1f} mm** (ultrapassando o patamar de segurança de 80 mm do PPDC). "
        "Ações de campo e vistorias preventivas obrigatórias!"
    )
elif max_72h_atual >= 50.0:
    st.warning(
        f"⚠️ **ESTADO DE ATENÇÃO:** Acumulado de 72h em **{max_72h_atual:.1f} mm**. "
        "Monitoramento intensificado nas encostas do Saboó."
    )
else:
    st.success(
        f"✅ **ESTADO DE OBSERVAÇÃO:** Acumulado recente de 72h em **{max_72h_atual:.1f} mm**. "
        "Dentro da normalidade operacional."
    )
