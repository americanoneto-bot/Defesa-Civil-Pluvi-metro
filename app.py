import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Defesa Civil Santos - Caderneta Oficial Saboó (P6)",
    layout="wide",
)

st.title("🛡️ Defesa Civil de Santos | Posto Morro do Saboó (P6)")
st.markdown(
    "**Caderneta Mensal de Observação de Precipitação** — Layout Operacional Padrão."
)

# 1. Campo para escrever/selecionar o Mês logo acima da tabela
col_mes1, col_mes2 = st.columns([2, 4])
with col_mes1:
    mes_referencia = st.selectbox(
        "📅 Mês de Referência:",
        [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ],
        index=8 # Setembro como padrão atual
    )
with col_mes2:
    ano_referencia = st.text_input("Ano:", value="2026")

st.markdown(f"### 📋 Posto do Saboó / P6 — Mês: **{mes_referencia} / {ano_referencia}**")

# Horários de medição de 3 em 3 horas (Linha Superior)
horarios_3h = [
    "06h", "09h", "12h", "15h", 
    "18h", "21h", "00h", "03h (+1)"
]

# Dias do mês de 1 a 31 (Coluna à Esquerda)
dias_mes = [str(i).zfill(2) for i in range(1, 32)]

# Inicializando a matriz de dados no session_state se não existir (Dias nas linhas, Horários nas colunas)
if 'caderneta_invertida' not in st.session_state:
    df_base = pd.DataFrame(0.0, index=dias_mes, columns=horarios_3h)
    st.session_state['caderneta_invertida'] = df_base

st.sidebar.header("⚙️ Controles Operacionais")
st.sidebar.info(
    "**Orientações de Preenchimento:**\n"
    "• À esquerda estão os **Dias do Mês** (01 a 31).\n"
    "• Na linha superior estão os **Horários (3 em 3h)**.\n"
    "• Insira os milímetros (mm) medidos em cada turno.\n"
    "• Os acumulados e totais serão calculados automaticamente."
)

st.markdown("Insira os índices pluviométricos nas células correspondentes:")

# Tabela interativa principal (Dias nas linhas, Horários nas colunas)
matriz_editada = st.data_editor(
    st.session_state['caderneta_invertida'],
    use_container_width=True,
    key="editor_caderneta_invertida"
)

st.session_state['caderneta_invertida'] = matriz_editada

# --- CÁLCULOS AUTOMÁTICOS DE RODAPÉ / LATERAIS ---
# 1. Total Diário: Soma horizontal de cada linha (dia)
total_diario = matriz_editada.sum(axis=1)

# 2. Acumulado de 72h (Soma móvel de 3 dias consecutivos)
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

# Montando a tabela de resultados consolidados (Rodapé de Acumulados)
df_resultados = pd.DataFrame({
    "Total Diário (mm)": total_diario,
    "Acumulado 72h (mm)": acumulado_72h,
    "Acumulado Mensal (mm)": acumulado_mensal
})

st.markdown("---")
st.subheader("📊 Totais e Acumulados Automáticos (Resultados do Período)")
st.markdown("Valores calculados em tempo real com base nos lançamentos diários e horários:")

# Exibição da tabela de resultados
st.dataframe(df_resultados, use_container_width=True)

# Checagem do maior acumulado recente de 72h para o gatilho de alerta
max_72h = acumulado_72h.max()

st.markdown("---")
st.subheader("🚨 Status Operacional Crítico (Morro do Saboó)")

if max_72h >= 80.0:
    st.error(
        f"⚠️ **ALERTA / ESTADO DE ATENÇÃO MÁXIMA:** O acumulado móvel de 72 horas atingiu "
        f"**{max_72h:.1f} mm** (ultrapassando o patamar normativo de 80 mm do PPDC). "
        "Ações de campo e vistorias preventivas obrigatórias!"
    )
elif max_72h >= 50.0:
    st.warning(
        f"⚠️ **ESTADO DE ATENÇÃO:** Acumulado de 72h em **{max_72h:.1f} mm**. "
        "Monitoramento intensificado nas encostas."
    )
else:
    st.success(
        f"✅ **ESTADO DE OBSERVAÇÃO:** Maior acumulado recente de 72h em **{max_72h:.1f} mm**. "
        "Índices dentro da normalidade operacional."
    )
