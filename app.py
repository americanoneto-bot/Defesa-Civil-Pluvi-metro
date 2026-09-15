import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Defesa Civil Santos - Caderneta Oficial Saboó (P6)",
    layout="wide",
)

st.title("🛡️ Defesa Civil de Santos | Posto Morro do Saboó (P6)")
st.markdown(
    "**Caderneta Mensal de Observação de Precipitação** — Layout Operacional de Linha Dupla por Dia."
)

# 1. Campo para escrever/selecionar o Mês e Ano
col_mes1, col_mes2 = st.columns([2, 4])
with col_mes1:
    mes_referencia = st.selectbox(
        "📅 Mês de Referência:",
        [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ],
        index=8 # Setembro
    )
with col_mes2:
    ano_referencia = st.text_input("Ano:", value="2026")

st.markdown(f"### 📋 Posto do Saboó / P6 — Mês: **{mes_referencia} / {ano_referencia}**")

# Horários de medição de 3 em 3 horas (Linha Superior da Tabela)
horarios_3h = [
    "06h", "09h", "12h", "15h", 
    "18h", "21h", "00h", "03h (+1)"
]

# Construindo o índice duplo para cada dia (Dia X - Entrada e Dia X - Acum. 72h)
dias_mes = [str(i).zfill(2) for i in range(1, 32)]
indices_linhas = []
for dia in dias_mes:
    indices_linhas.append(f"{dia} - Índice (mm)")
    indices_linhas.append(f"{dia} - Acum. 72h")

# Inicializando a matriz no session_state se não existir
if 'caderneta_linha_dupla' not in st.session_state:
    df_base = pd.DataFrame(0.0, index=indices_linhas, columns=horarios_3h)
    st.session_state['caderneta_linha_dupla'] = df_base

st.sidebar.header("⚙️ Controles Operacionais")
st.sidebar.info(
    "**Orientações de Preenchimento:**\n"
    "• Linhas **'Índice (mm)'**: Insira manualmente os valores de chuva de cada turno.\n"
    "• Linhas **'Acum. 72h'**: Calculadas automaticamente pelo sistema em tempo real.\n"
    "• Colunas superiores: Horários de medição (3 em 3h)."
)

st.markdown("Insira os índices pluviométricos nas linhas de **Índice (mm)** correspondentes a cada dia:")

# Tabela interativa principal
matriz_editada = st.data_editor(
    st.session_state['caderneta_linha_dupla'],
    use_container_width=True,
    key="editor_caderneta_dupla"
)

# --- CÁLCULO AUTOMÁTICO DO ACUMULADO DE 72H POR HORÁRIO ---
# Para cada horário, somamos as últimas 24 entradas de turnos (equivalente a 3 dias x 8 turnos/dia = 24 turnos)
df_processado = matriz_editada.copy()

# Achata todas as células de índices em uma série cronológica contínua para calcular a janela móvel de 72h (24 turnos)
lista_indices_por_turno = []
mapeamento_posicoes = []

for dia in dias_mes:
    linha_idx = f"{dia} - Índice (mm)"
    linha_72h = f"{dia} - Acum. 72h"
    for h in horarios_3h:
        val = df_processado.loc[linha_idx, h]
        try:
            val_num = float(val)
        except:
            val_num = 0.0
        lista_indices_por_turno.append(val_num)
        mapeamento_posicoes.append((linha_72h, h))

serie_temporal = pd.Series(lista_indices_por_turno)
# Janela móvel de 24 turnos (72 horas)
serie_72h = serie_temporal.rolling(window=24, min_periods=1).sum()

# Reatribuindo os valores calculados de volta às linhas de Acum. 72h
for idx, (linha_72h, h) in enumerate(mapeamento_posicoes):
    df_processado.loc[linha_72h, h] = round(serie_72h.iloc[idx], 1)

# Atualiza a sessão com os cálculos automáticos aplicados nas linhas de 72h
st.session_state['caderneta_linha_dupla'] = df_processado

st.markdown("---")
st.subheader("📋 Matriz Oficial Consolidada (Entradas e Acumulados Automáticos)")
st.dataframe(df_processado, use_container_width=True)

# Identificando o maior valor de 72h gerado na tabela para fins de alerta do PPDC
todos_valores_72h = []
for dia in dias_mes:
    linha_72h = f"{dia} - Acum. 72h"
    for h in horarios_3h:
        todos_valores_72h.append(df_processado.loc[linha_72h, h])

max_72h_geral = max(todos_valores_72h) if todos_valores_72h else 0.0

st.markdown("---")
st.subheader("🚨 Status Operacional Crítico (Morro do Saboó)")

if max_72h_geral >= 80.0:
    st.error(
        f"⚠️ **ALERTA / ESTADO DE ATENÇÃO MÁXIMA:** O acumulado móvel de 72 horas atingiu "
        f"**{max_72h_geral:.1f} mm** (ultrapassando o patamar normativo de 80 mm do PPDC). "
        "Ações de campo e vistorias preventivas obrigatórias!"
    )
elif max_72h_geral >= 50.0:
    st.warning(
        f"⚠️ **ESTADO DE ATENÇÃO:** Acumulado de 72h em **{max_72h_geral:.1f} mm**. "
        "Monitoramento intensificado nas encostas."
    )
else:
    st.success(
        f"✅ **ESTADO DE OBSERVAÇÃO:** Maior acumulado de 72h recente em **{max_72h_geral:.1f} mm**. "
        "Índices dentro da normalidade operacional."
    )
