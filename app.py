import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Defesa Civil Santos - Caderneta Oficial Saboó (P6)",
    layout="wide",
)

st.title("🛡️ Defesa Civil de Santos | Posto Morro do Saboó (P6)")
st.markdown(
    "**Caderneta Mensal de Observação de Precipitação** — Matriz Unificada de Linha Dupla "
    "(Lançamento Manual de Índices e Cálculo Automático de 72h por Turno na mesma tabela)."
)

# 1. Seleção do Mês e Ano de Referência
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

# Horários de medição de 3 em 3 horas (Linha Superior)
horarios_3h = [
    "06h", "09h", "12h", "15h", 
    "18h", "21h", "00h", "03h (+1)"
]

# Dias do mês de 01 a 31
dias_mes = [str(i).zfill(2) for i in range(1, 32)]

# Construindo as tuplas para o Multi-Index (Dia + Tipo de Linha)
tuplas_linhas = []
for dia in dias_mes:
    tuplas_linhas.append((dia, "Índice (mm)"))
    tuplas_linhas.append((dia, "Acum. 72h"))

multi_index = pd.MultiIndex.from_tuples(tuplas_linhas, names=["Dia", "Tipo"])

# Inicializando a matriz unificada no session_state
if 'caderneta_unificada' not in st.session_state:
    df_base = pd.DataFrame(0.0, index=multi_index, columns=horarios_3h)
    st.session_state['caderneta_unificada'] = df_base

st.sidebar.header("⚙️ Controles Operacionais")
st.sidebar.info(
    "**Orientações de Preenchimento:**\n"
    "• Digite os valores nas linhas de **Índice (mm)**.\n"
    "• As linhas de **Acum. 72h** calculam automaticamente o somatório das últimas 72 horas (24 turnos) para cada horário exato.\n"
    "• Tudo na mesma tabela."
)

st.subheader("📝 Caderneta de Campo Integrada (Entrada e Acumulados por Turno)")

# Tabela interativa unificada
df_editado = st.data_editor(
    st.session_state['caderneta_unificada'],
    use_container_width=True,
    key="editor_caderneta_unificada"
)

# --- PROCESSAMENTO MATEMÁTICO AUTOMÁTICO NA MESMA TABELA ---
# 1. Extraímos sequencialmente todos os índices digitados nas linhas de "Índice (mm)"
sequencia_indices = []
mapeamento_celulas = []

for dia in dias_mes:
    for h in horarios_3h:
        val = df_editado.loc[(dia, "Índice (mm)"), h]
        try:
            val_num = float(val)
        except:
            val_num = 0.0
        sequencia_indices.append(val_num)
        mapeamento_celulas.append((dia, h))

# 2. Calculamos a janela móvel de 72h (24 turnos consecutivos de 3 em 3h)
serie_temporal = pd.Series(sequencia_indices)
serie_72h = serie_temporal.rolling(window=24, min_periods=1).sum()

# 3. Atualizamos a tabela de trabalho preenchendo as linhas de Acum. 72h automaticamente
df_atualizado = df_editado.copy()
for idx, (dia, h) in enumerate(mapeamento_celulas):
    df_atualizado.loc[(dia, "Acum. 72h"), h] = round(serie_72h.iloc[idx], 1)

# Salvamos de volta no session_state para manter a sincronia visual
st.session_state['caderneta_unificada'] = df_atualizado

# Identificando o maior acumulado de 72h em toda a tabela para o gatilho de alerta do PPDC
max_72h_geral = 0.0
for dia in dias_mes:
    for h in horarios_3h:
        val_72h = df_atualizado.loc[(dia, "Acum. 72h"), h]
        if val_72h > max_72h_geral:
            max_72h_geral = val_72h

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
