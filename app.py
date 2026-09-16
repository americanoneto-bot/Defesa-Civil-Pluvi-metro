import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Defesa Civil Santos - Caderneta Oficial Saboó (P6)",
    layout="wide",
)

# --- INSERÇÃO DO LOGO OFICIAL DA DEFESA CIVIL ---
try:
    st.image("logo_defesa_civil.jpg", width=120)
except:
    pass

st.title("🛡️ Defesa Civil de Santos | Posto Morro do Saboó (P6)")
st.markdown(
    "**Caderneta Mensal de Observação de Precipitação** — Módulo Operacional com Monitoramento da Última Célula."
)

# Horários de medição de 3 em 3 horas (Colunas)
horarios_3h = [
    "06h", "09h", "12h", "15h", 
    "18h", "21h", "00h", "03h (+1)"
]

# Dias do mês de 01 a 31 (Linhas)
dias_mes = [f"{i:02d}" for i in range(1, 32)]
colunas_tabela_1 = horarios_3h + ["Total Diário"]

# --- BLINDAGEM ABSOLUTA DE PERSISTÊNCIA (CONTRA F5) ---
if 'caderneta_manual' not in st.session_state:
    st.session_state['caderneta_manual'] = pd.DataFrame("", index=dias_mes, columns=colunas_tabela_1)
else:
    for col in colunas_tabela_1:
        if col not in st.session_state['caderneta_manual'].columns:
            st.session_state['caderneta_manual'][col] = ""

if 'status_operacional' not in st.session_state:
    st.session_state['status_operacional'] = "Observacao"

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

st.sidebar.header("⚙️ Controles Operacionais")
st.sidebar.info(
    "**Orientações de Preenchimento:**\n"
    "• Insira os índices de chuva (mm) em qualquer célula da Tabela 1.\n"
    "• A coluna **Total Diário** calcula automaticamente a soma dos turnos.\n"
    "• **Dados blindados:** resistem a atualizações de página (F5)."
)

st.subheader("📝 1. Tabela de Lançamento Manual e Total Diário (mm)")
st.markdown("Digite os valores medidos em qualquer turno da tabela:")

# Tabela interativa de lançamento manual vinculada estritamente à sessão
df_editado = st.data_editor(
    st.session_state['caderneta_manual'],
    use_container_width=True,
    key="editor_caderneta_estavel"
)

# Atualiza imediatamente o session_state com o que foi digitado
st.session_state['caderneta_manual'] = df_editado

# --- PROCESSAMENTO MATEMÁTICO DE PRECISÃO ---
sequencia_calculo = []
lista_status_preenchimento = []
matriz_valores_numericos = pd.DataFrame(0.0, index=dias_mes, columns=horarios_3h)

for dia in dias_mes:
    soma_linha_atual = 0.0
    tem_dado_na_linha = False
    for h in horarios_3h:
        val = df_editado.loc[dia, h]
        if val is not None and str(val).strip() != "" and str(val).lower() != "nan":
            try:
                val_num = float(str(val).replace(',', '.'))
                sequencia_calculo.append(val_num)
                lista_status_preenchimento.append(True)
                matriz_valores_numericos.loc[dia, h] = val_num
                soma_linha_atual += val_num
                tem_dado_na_linha = True
            except:
                sequencia_calculo.append(0.0)
                lista_status_preenchimento.append(False)
        else:
            sequencia_calculo.append(0.0)
            lista_status_preenchimento.append(False)
            
    if tem_dado_na_linha:
        df_editado.loc[dia, "Total Diário"] = f"{soma_linha_atual:.1f}"
    else:
        df_editado.loc[dia, "Total Diário"] = ""

serie_matematica = pd.Series(sequencia_calculo)

# Executa os cálculos contínuos globais (janela de 72h = 24 turnos)
serie_72h = serie_matematica.rolling(window=24, min_periods=1).sum()
serie_mensal = serie_matematica.cumsum()

df_72h = pd.DataFrame("", index=dias_mes, columns=horarios_3h)
df_mensal = pd.DataFrame("", index=dias_mes, columns=horarios_3h)

idx_global = 0
max_72h_geral = 0.0
ultimo_val_72h = 0.0

for dia in dias_mes:
    for h in horarios_3h:
        if lista_status_preenchimento[idx_global]:
            val_72 = round(serie_72h.iloc[idx_global], 1)
            val_mes = round(serie_mensal.iloc[idx_global], 1)
            
            df_72h.loc[dia, h] = f"{val_72:.1f}"
            df_mensal.loc[dia, h] = f"{val_mes:.1f}"
            
            # Armazena o valor de 72h da última célula preenchida cronologicamente
            ultimo_val_72h = val_72
            
            if val_72 > max_72h_geral:
                max_72h_geral = val_72
        else:
            df_72h.loc[dia, h] = ""
            df_mensal.loc[dia, h] = ""
            
        idx_global += 1

# --- MECANISMO BASEADO NA ÚLTIMA CÉLULA PREENCHIDA ---
# Se a última célula preenchida baixou de 80 mm, o sistema retorna imediatamente para Observação
if ultimo_val_72h < 80.0 and st.session_state['status_operacional'] == "Atencao":
    st.session_state['status_operacional'] = "Observacao"

# Se a última célula preenchida atingiu >= 80 mm e estávamos em observação, abre a subida pendente
elif st.session_state['status_operacional'] == "Observacao" and ultimo_val_72h >= 80.0:
    st.session_state['status_operacional'] = "Subida_Pendente"

st.markdown("---")
st.subheader("📊 2. Acumulado de 72h por Turno (Cálculo Automático)")
st.dataframe(df_72h, use_container_width=True)

st.markdown("---")
st.subheader("📈 3. Acumulado Mensal Progressivo por Horário (Cálculo Automático)")
st.dataframe(df_mensal, use_container_width=True)

st.markdown("---")
st.subheader("🚨 Status Operacional Crítico (Morro do Saboó)")

# --- RENDERIZAÇÃO DOS ESTADOS ---

if st.session_state['status_operacional'] == "Subida_Pendente":
    st.markdown(
        """
        <div style="background-color: #ffeb3b; padding: 20px; border-radius: 10px; text-align: center; color: #333333; border: 2px solid #fbc02d;">
            <h2 style="margin: 0; font-size: 28px; font-weight: bold;">⚠️ ATENÇÃO: PATAMAR DE 80 MM ATINGIDO</h2>
            <p style="margin: 5px 0 0 0; font-size: 16px;">O acumulado de 72h na última medição chegou a <b>{:.1f} mm</b>.</p>
        </div>
        """.format(ultimo_val_72h),
        unsafe_allow_html=True
    )
    
    st.markdown("### 🎛️ Decisão de Protocolo Operacional (Subida):")
    escolha_subida = st.radio(
        "O acumulado atingiu o patamar crítico. Deseja declarar Estado de Atenção ou Manter Observação?",
        ["Declarar Estado de Atenção", "Manter Estado de Observação"],
        key="radio_decisao_subida"
    )
    
    if st.button("Confirmar e Atualizar Status", key="btn_subida"):
        if escolha_subida == "Declarar Estado de Atenção":
            st.session_state['status_operacional'] = "Atencao"
            st.success("🚨 **Estado de Atenção DECLARADO** com sucesso.")
        else:
            st.session_state['status_operacional'] = "Observacao"
            st.warning("⚠️ **Estado de Observação MANTIDO** com sucesso.")
        st.rerun()

elif st.session_state['status_operacional'] == "Atencao":
    st.markdown(
        """
        <div style="background-color: #ffeb3b; padding: 25px; border-radius: 10px; text-align: center; color: #333333; border: 2px solid #fbc02d;">
            <h1 style="margin: 0; font-size: 42px; font-weight: bold;">⚠️ ATENÇÃO ⚠️</h1>
            <h3 style="margin: 10px 0 0 0; font-size: 22px;">O acumulado de 72h na última medição está em <b>{:.1f} mm</b>.</h3>
            <p style="margin: 8px 0 0 0; font-size: 17px; font-weight: 500;">Estado de Atenção : Vistoria de campo para avaliação de riscos.</p>
        </div>
        """.format(ultimo_val_72h),
        unsafe_allow_html=True
    )

else:
    # Status Operacional Oficial: Observação / Normalidade (Exibido em verde imediatamente se a última célula for < 80)
    st.success(
        f"✅ **ESTADO DE OBSERVAÇÃO:** Acumulado de 72h na última medição em **{ultimo_val_72h:.1f} mm** (abaixo de 80 mm). "
        "Índices dentro da normalidade operacional para o Posto P6."
    )
