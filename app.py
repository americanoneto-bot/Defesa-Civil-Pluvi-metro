import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Defesa Civil Santos - Caderneta Oficial Saboó (P6)",
    layout="wide",
)

st.title("🛡️ Defesa Civil de Santos | Posto Morro do Saboó (P6)")
st.markdown(
    "**Caderneta Mensal de Observação de Precipitação** — Layout Horizontal Oficial. "
    "Insira os índices nas células de horários de 3 em 3h e acompanhe os acumulados automáticos no rodapé."
)

# Horários de medição de 3 em 3 horas (Linhas da caderneta física na horizontal)
horarios_3h = [
    "06h", "09h", "12h", "15h", 
    "18h", "21h", "00h", "03h (+1)"
]

# Dias do mês de 1 a 31 (Colunas da caderneta física)
dias_mes = [str(i).zfill(2) for i in range(1, 32)]

# Inicializando a matriz de dados no session_state se não existir
if 'caderneta_horizontal' not in st.session_state:
    # Cria a matriz com dias nas colunas e horários nas linhas
    df_base = pd.DataFrame(0.0, index=horarios_3h, columns=dias_mes)
    st.session_state['caderneta_horizontal'] = df_base

st.sidebar.header("⚙️ Controles Operacionais")
st.sidebar.info(
    "**Orientações de Preenchimento:**\n"
    "• Navegue pela tabela horizontal abaixo.\n"
    "• Insira os milímetros (mm) medidos em cada turno.\n"
    "• As linhas finais calculam automaticamente os totais e acumulados do PPDC."
)

st.subheader("📋 Planilha de Campo: Turnos (Horários) vs. Dias do Mês")

# Tabela interativa principal na horizontal
matriz_editada = st.data_editor(
    st.session_state['caderneta_horizontal'],
    use_container_width=True,
    key="editor_caderneta_horizontal"
)

st.session_state['caderneta_horizontal'] = matriz_editada

# --- CÁLCULOS AUTOMÁTICOS DE RODAPÉ ---
# 1. Total Diário (Soma das colunas de cada dia)
total_diario = matriz_editada.sum(axis=0)

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

# Montando a tabela de rodapé consolidada com os cálculos automáticos
df_rodape = pd.DataFrame({
    "Total Diário (mm)": total_diario,
    "Acumulado 72h (mm)": acumulado_72h,
    "Acumulado Mensal (mm)": acumulado_mensal
}).T # Trans põe para manter a mesma harmonia visual horizontal

st.markdown("---")
st.subheader("📊 Totais e Acumulados Automáticos (Rodapé Operacional)")
st.markdown("Valores calculados em tempo real de acordo com os lançamentos efetuados:")

# Exibição da tabela de resultados
st.dataframe(df_rodape, use_container_width=True)

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
