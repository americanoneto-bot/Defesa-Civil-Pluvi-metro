import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Defesa Civil Santos - Caderneta Oficial Saboó (P6)",
    layout="wide",
)

st.title("🛡️ Defesa Civil de Santos | Posto Morro do Saboó (P6)")
st.markdown(
    "**Caderneta Mensal de Observação de Precipitação** — Módulo Operacional com Restrição de Exibição Condicional."
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

# Horários de medição de 3 em 3 horas (Colunas)
horarios_3h = [
    "06h", "09h", "12h", "15h", 
    "18h", "21h", "00h", "03h (+1)"
]

# Dias do mês de 01 a 31 (Linhas)
dias_mes = [str(i).zfill(2) for i in range(1, 32)]

# Inicializando a matriz de entrada manual com valores vazios (None)
if 'caderneta_manual' not in st.session_state:
    df_base = pd.DataFrame(None, index=dias_mes, columns=horarios_3h)
    st.session_state['caderneta_manual'] = df_base

st.sidebar.header("⚙️ Controles Operacionais")
st.sidebar.info(
    "**Orientações de Preenchimento:**\n"
    "• Insira os índices de chuva (mm) na tabela superior.\n"
    "• As tabelas 2 e 3 exibirão os cálculos apenas nos horários devidamente preenchidos, permanecendo zeradas nos demais."
)

st.subheader("📝 1. Lançamento Manual de Índices (mm)")
st.markdown("Digite os valores medidos em cada turno:")

# Tabela interativa para inserção manual
df_editado = st.data_editor(
    st.session_state['caderneta_manual'],
    use_container_width=True,
    key="editor_caderneta_estavel"
)

st.session_state['caderneta_manual'] = df_editado

# --- PROCESSAMENTO MATEMÁTICO COM RESTRIÇÃO CONDICIONAL ---
sequencia_indices = []
mapeamento_celulas = []
teve_dado = False

for dia in dias_mes:
    for h in horarios_3h:
        val = df_editado.loc[dia, h]
        if val is not None and str(val).strip() != "":
            try:
                val_num = float(val)
                teve_dado = True
            except:
                val_num = 0.0
        else:
            val_num = 0.0 # Tratado como zero para as somas matemáticas de fundo
            
        sequencia_indices.append(val_num)
        mapeamento_celulas.append((dia, h))

serie_para_calculo = pd.Series(sequencia_indices)

# 1. Janela móvel de 24 turnos consecutivos (72 horas)
serie_72h = serie_para_calculo.rolling(window=24, min_periods=1).sum()

# 2. Acumulado Mensal Progressivo contínuo
serie_mensal = serie_para_calculo.cumsum()

# Construindo as tabelas analíticas automáticas estritamente condicionadas aos preenchimentos da Tabela 1
df_72h = pd.DataFrame(0.0, index=dias_mes, columns=horarios_3h)
df_mensal = pd.DataFrame(0.0, index=dias_mes, columns=horarios_3h)

for idx, (dia, h) in enumerate(mapeamento_celulas):
    val_original = df_editado.loc[dia, h]
    has_data = val_original is not None and str(val_original).strip() != ""
    
    if has_data:
        df_72h.loc[dia, h] = round(serie_72h.iloc[idx], 1)
        df_mensal.loc[dia, h] = round(serie_mensal.iloc[idx], 1)
    else:
        df_72h.loc[dia, h] = 0.0
        df_mensal.loc[dia, h] = 0.0

st.markdown("---")
st.subheader("📊 2. Acumulado de 72h por Turno (Cálculo Automático)")
st.markdown("Exibido restritamente nos horários preenchidos na tabela de índices:")
st.dataframe(df_72h, use_container_width=True)

st.markdown("---")
st.subheader("📈 3. Acumulado Mensal Progressivo por Horário (Cálculo Automático)")
st.markdown("Evolução contínua acumulada exibida apenas para os turnos informados:")
st.dataframe(df_mensal, use_container_width=True)

# Identificando o maior acumulado de 72h para o gatilho de alerta do PPDC
max_72h_geral = df_72h.max().max() if teve_dado else 0.0

st.markdown("---")
st.subheader("🚨 Status Operacional Crítico (Morro do Saboó)")

if not teve_dado:
    st.info("ℹ️ **AGUARDANDO LANÇAMENTOS:** Nenhum índice pluviométrico inserido no período até o momento.")
elif max_72h_geral >= 80.0:
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
