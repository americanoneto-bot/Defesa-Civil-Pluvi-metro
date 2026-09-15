import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Defesa Civil Santos - Caderneta Oficial Saboó (P6)",
    layout="wide",
)

st.title("🛡️ Defesa Civil de Santos | Posto Morro do Saboó (P6)")
st.markdown(
    "**Caderneta Mensal de Observação de Precipitação** — Módulo Operacional com Alerta Crítico e Protocolo de Baixa de Índice."
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

# Inicializando estados de controle do alerta de 80mm
if 'atingiu_80mm' not in st.session_state:
    st.session_state['atingiu_80mm'] = False
if 'decisao_manual_atencao' not in st.session_state:
    st.session_state['decisao_manual_atencao'] = "Manter"

st.sidebar.header("⚙️ Controles Operacionais")
st.sidebar.info(
    "**Orientações de Preenchimento:**\n"
    "• Insira os índices de chuva (mm) na Tabela 1.\n"
    "• As Tabelas 2 e 3 exibirão os cálculos exclusivamente nos horários preenchidos.\n"
    "• O painel emitirá alertas visuais destacados ao atingir o patamar de 80 mm em 72h."
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
            sequencia_calculo.append(0.0)
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
st.dataframe(df_72h, use_container_width=True)

st.markdown("---")
st.subheader("📈 3. Acumulado Mensal Progressivo por Horário (Cálculo Automático)")
st.dataframe(df_mensal, use_container_width=True)

st.markdown("---")
st.subheader("🚨 Status Operacional Crítico (Morro do Saboó)")

# --- LÓGICA DO AVISO DE ATENÇÃO DESTAQUE E PROTOCOLO DE QUEDA ---
if max_72h_geral >= 80.0:
    st.session_state['atingiu_80mm'] = True
    # Aviso em letras grandes e destacadas em lugar visível
    st.markdown(
        """
        <div style="background-color: #ff4b4b; padding: 25px; border-radius: 10px; text-align: center; color: white;">
            <h1 style="margin: 0; font-size: 42px; font-weight: bold;">⚠️ ATENÇÃO ⚠️</h1>
            <h3 style="margin: 10px 0 0 0; font-size: 22px;">O acumulado de 72h atingiu o patamar crítico de <b>80.0 mm</b> ou mais!</h3>
            <p style="margin: 5px 0 0 0; font-size: 16px;">Ações de campo, vistorias e protocolo de alerta máximo ativados no Posto P6.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
elif st.session_state['atingiu_80mm'] and max_72h_geral < 80.0 and teve_dado:
    # O índice baixou para menos de 80mm após ter atingido anteriormente
    st.markdown(
        """
        <div style="background-color: #ffa500; padding: 20px; border-radius: 10px; text-align: center; color: black;">
            <h2 style="margin: 0; font-size: 30px; font-weight: bold;">⚠️ ATENÇÃO: QUEDA NO ACUMULADO</h2>
            <p style="margin: 5px 0 0 0; font-size: 16px;">O índice de 72h baixou para <b>{:.1f} mm</b> (abaixo de 80 mm).</p>
        </div>
        """.format(max_72h_geral),
        unsafe_allow_html=True
    )
    
    st.markdown("### 🎛️ Decisão de Protocolo Operacional:")
    escolha = st.radio(
        "O acumulado reduziu abaixo do patamar crítico. Deseja cancelar ou manter o nível de atenção atual?",
        ["Manter Nível de Atenção", "Cancelar Nível de Atenção"],
        index=0 if st.session_state['decisao_manual_atencao'] == "Manter" else 1
    )
    
    if escolha == "Manter Nível de Atenção":
        st.session_state['decisao_manual_atencao'] = "Manter"
        st.warning("🔒 **Nível de Atenção MANTIDO** por diretriz operacional do plantão, mesmo com a redução momentânea do índice.")
    else:
        st.session_state['decisao_manual_atencao'] = "Cancelar"
        st.session_state['atingiu_80mm'] = False  # Reseta o gatilho se o operador optar por cancelar
        st.success("✅ **Nível de Atenção CANCELADO** conforme decisão do operador em plantão. Retorno à observação normal.")

else:
    # Estado normal de observação
    if max_72h_geral >= 50.0:
        st.warning(
            f"⚠️ **ESTADO DE ATENÇÃO:** Acumulado de 72h em **{max_72h_geral:.1f} mm**. "
            "Monitoramento intensificado nas encostas."
        )
    else:
        st.success(
            f"✅ **ESTADO DE OBSERVAÇÃO:** Maior acumulado de 72h recente em **{max_72h_geral:.1f} mm**. "
            "Índices dentro da normalidade operacional."
        )
