import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Defesa Civil Santos - Caderneta Oficial Saboó (P6)",
    layout="wide",
)

st.title("🛡️ Defesa Civil de Santos | Posto Morro do Saboó (P6)")
st.markdown(
    "**Caderneta Mensal de Observação de Precipitação** — Módulo Operacional com Vínculo Celular Estrito."
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

# Inicializando a matriz de entrada manual com strings vazias ("")
if 'caderneta_manual' not in st.session_state:
    df_base = pd.DataFrame("", index=dias_mes, columns=horarios_3h)
    st.session_state['caderneta_manual'] = df_base

st.sidebar.header("⚙️ Controles Operacionais")
st.sidebar.info(
    "**Orientações de Preenchimento:**\n"
    "• Insira os índices de chuva (mm) na Tabela 1.\n"
    "• As Tabelas 2 e 3 exibirão os cálculos **exclusivamente** nos horários preenchidos, mantendo o restante limpo e em branco."
)

st.subheader("📝 1. Tabela de Lançamento Manual (Índices em mm)")
st.markdown("Digite os valores medidos em cada turno:")

# Tabela interativa para inserção manual
df_editado = st.data_editor(
    st.session_state['caderneta_manual'],
    use_container_width=True,
    key="editor_caderneta_estavel"
)

st.session_state['caderneta_manual'] = df_editado

# --- PROCESSAMENTO MATEMÁTICO COM VÍNCULO CELULAR RESTRITO ---
sequencia_calculo = []
lista_status_preenchimento = []
teve_dado = False

# 1. Varre a tabela 1 identificando exatamente quais células possuem dados
for dia in dias_mes:
    for h in horarios_3h:
        val = df_editado.loc[dia, h]
        if val is not None and str(val).strip() != "" and str(val).lower() != "nan":
            try:
                val_num = float(val)
                sequencia_calculo.append(val_num)
                lista_status_preenchimento.append(True)
                teve_dado = True
            except:
                sequencia_calculo.append(0.0)
                lista_status_preenchimento.append(False)
        else:
            sequencia_calculo.append(0.0) # Zero para alimentar a matemática de fundo
            lista_status_preenchimento.append(False)

serie_matematica = pd.Series(sequencia_calculo)

# 2. Executa os cálculos contínuos globais
serie_72h = serie_matematica.rolling(window=24, min_periods=1).sum()
serie_mensal = serie_matematica.cumsum()

# 3. Constrói as tabelas 2 e 3 usando estritamente "" (vazio) para células não preenchidas na Tabela 1
df_72h = pd.DataFrame("", index=dias_mes, columns=horarios_3h)
df_mensal = pd.DataFrame("", index=dias_mes, columns=horarios_3h)

idx_global = 0
max_72h_geral = 0.0

for dia in dias_mes:
    for h in horarios_3h:
        if lista_status_preenchimento[idx_global]:
            val_72 = round(serie_72h.iloc[idx_global], 1)
            val_mes = round(serie_mensal.iloc[idx_global], 1)
            
            df_72h.loc[dia, h] = f"{val_72:.1f}"
            df_mensal.loc[dia, h] = f"{val_mes:.1f}"
            
            if val_72 > max_72h_geral:
                max_72h_geral = val_72
        else:
            df_72h.loc[dia, h] = ""
            df_mensal.loc[dia, h] = ""
            
        idx_global += 1

st.markdown("---")
st.subheader("📊 2. Acumulado de 72h por Turno (Cálculo Automático)")
st.markdown("Exibido estritamente e unicamente nos horários preenchidos na tabela de índices:")
st.dataframe(df_72h, use_container_width=True)

st.markdown("---")
st.subheader("📈 3. Acumulado Mensal Progressivo por Horário (Cálculo Automático)")
st.markdown("Evolução contínua exibida estritamente e unicamente nos turnos preenchidos:")
st.dataframe(df_mensal, use_container_width=True)

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
