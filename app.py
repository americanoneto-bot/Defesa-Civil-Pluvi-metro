import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Defesa Civil Santos - Caderneta de Campo Saboó",
    layout="wide",
)

st.title("🛡️ Defesa Civil de Santos | Posto Morro do Saboó (P6)")
st.markdown(
    "Módulo de Caderneta de Campo Digital: Insira os índices pluviométricos manualmente "
    "e acompanhe os cálculos automáticos de acumulados (24h, 72h e Mensal) conforme as diretrizes do PPDC."
)

# Inicializando uma base padrão de dados para preenchimento manual (simulando a caderneta)
if 'df_caderneta' not in st.session_state:
    datas_padrao = pd.date_range(end=datetime.date.today(), periods=10, freq="D")
    st.session_state['df_caderneta'] = pd.DataFrame({
        "Data": datas_padrao,
        "Precipitação_Diária_mm": [0.0, 13.8, 0.5, 74.8, 37.4, 15.0, 2.1, 8.4, 19.3, 12.5]
    })

st.sidebar.header("⚙️ Painel de Controle Operacional")
st.sidebar.info(
    "Instruções:\n"
    "1. Edite diretamente os valores na tabela abaixo (coluna de Precipitação).\n"
    "2. O sistema recalculará automaticamente as janelas de 24h, 72h e o Acumulado Mensal."
)

# Tabela interativa para inserção manual (Data Editor)
st.subheader("📝 Caderneta de Lançamento Manual (Entrada de Dados às 06h)")
df_editado = st.data_editor(
    st.session_state['df_caderneta'],
    num_rows="dynamic",
    use_container_width=True,
    key="editor_dados"
)

# Salvando as edições no estado da sessão
st.session_state['df_caderneta'] = df_editado

# Processamento matemático automático dos acumulados exigidos pela Defesa Civil
if not df_editado.empty:
    df_processado = df_editado.copy()
    df_processado['Data'] = pd.to_datetime(df_processado['Data'])
    df_processado = df_processado.sort_values('Data').reset_index(drop=True)
    
    # Garantindo valores numéricos
    df_processado['Precipitação_Diária_mm'] = pd.to_numeric(df_processado['Precipitação_Diária_mm'], errors='coerce').fillna(0.0)
    
    # Cálculo automático do Acumulado de 72 horas (soma móvel das últimas 3 entradas/dias)
    df_processado['Acumulado_72h_mm'] = df_processado['Precipitação_Diária_mm'].rolling(window=3, min_periods=1).sum()
    
    # Cálculo automático do Acumulado Mensal progressivo
    df_processado['Acumulado_Mensal_mm'] = df_processado['Precipitação_Diária_mm'].cumsum()
    
    # Pegando os valores mais recentes para os Indicadores Oficiais
    ultimo_registro = df_processado.iloc[-1]
    ac_24h = ultimo_registro['Precipitação_Diária_mm']
    ac_72h = ultimo_registro['Acumulado_72h_mm']
    ac_mes = ultimo_registro['Acumulado_Mensal_mm']

    st.markdown("---")
    st.subheader("📊 Indicadores Oficiais Calculados Automaticamente")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Acumulado Diário (24h)", f"{ac_24h:.1f} mm", "Medição Base")
    col2.metric("Acumulado 72 Horas", f"{ac_72h:.1f} mm", "Gatilho PPDC (Lim. 80mm)")
    col3.metric("Acumulado Mensal", f"{ac_mes:.1f} mm", "Saturação Periódica")

    # Avaliação de Risco Normativa da Defesa Civil baseada no acumulado de 72h
    st.subheader("🚨 Status Operacional do Morro do Saboó")
    if ac_72h >= 80.0:
        st.error(
            f"⚠️ **ALERTA / ESTADO DE ATENÇÃO:** O acumulado móvel de 72h atingiu **{ac_72h:.1f} mm** "
            f"(ultrapassando o patamar normativo de 80 mm exigido pelo PPDC). Intensificar vistorias de campo!"
        )
    elif ac_72h >= 50.0:
        st.warning(
            f"⚠️ **ESTADO DE ATENÇÃO:** Acumulado de 72h em **{ac_72h:.1f} mm**. "
            "Monitoramento preventivo ativo nas encostas do Saboó."
        )
    else:
        st.success(
            f"✅ **ESTADO DE OBSERVAÇÃO:** Acumulado de 72h em **{ac_72h:.1f} mm**. "
            "Índices dentro da faixa de normalidade operacional."
        )

    st.markdown("---")
    st.subheader("📈 Gráfico Comparativo da Evolução Diária e de 72h")
    
    # Exibição gráfica otimizada
    df_grafico = df_processado.set_index('Data')[['Precipitação_Diária_mm', 'Acumulado_72h_mm']]
    st.bar_chart(df_grafico, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Trilha de Auditoria e Relatório Consolidado")
    st.dataframe(df_processado, use_container_width=True)
