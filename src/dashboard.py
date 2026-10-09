"""Dashboard IoT — Monitoramento de Temperatura (Streamlit + Plotly).

Uso:  streamlit run src/dashboard.py

Os gráficos principais leem as 3 views SQL do PostgreSQL. Os KPIs e o
histograma consultam a tabela base, aplicando os filtros da barra lateral.
"""
import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import text

from database import get_engine

st.set_page_config(page_title="Dashboard IoT — Temperatura", page_icon="🌡️", layout="wide")

# Cores fixas por ambiente (mesma cor em todos os gráficos)
CORES = {"In": "#2563EB", "Out": "#EA580C"}
ROTULOS = {"In": "Interno (In)", "Out": "Externo (Out)"}
LAYOUT = dict(template="plotly_white", hovermode="x unified",
              legend=dict(title="", orientation="h", y=-0.22, x=0),
              margin=dict(l=10, r=10, t=50, b=10))


@st.cache_resource
def engine():
    return get_engine()


@st.cache_data(ttl=300)
def query(sql: str, params: dict | None = None) -> pd.DataFrame:
    """Executa uma consulta no PostgreSQL e devolve um DataFrame."""
    with engine().connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)


def nome_ambiente(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ambiente_nome"] = df["ambiente"].map(ROTULOS)
    return df


# ---------------------------------------------------------------- dados
try:
    limites = query("SELECT MIN(noted_at)::date AS ini, MAX(noted_at)::date AS fim, "
                    "MIN(temperature) AS tmin, MAX(temperature) AS tmax FROM temperature_readings").iloc[0]
except Exception as exc:  # noqa: BLE001
    st.error(f"Não foi possível consultar o PostgreSQL. O contêiner está rodando e a carga foi feita?\n\n{exc}")
    st.stop()

# ---------------------------------------------------------------- filtros
st.sidebar.header("Filtros")
ambientes = st.sidebar.multiselect("Ambiente", ["In", "Out"], default=["In", "Out"],
                                   format_func=ROTULOS.get)
periodo = st.sidebar.date_input("Período", (limites.ini, limites.fim),
                                min_value=limites.ini, max_value=limites.fim)
faixa = st.sidebar.slider("Faixa de temperatura (°C)", int(limites.tmin), int(limites.tmax),
                          (int(limites.tmin), int(limites.tmax)))
st.sidebar.caption("Ambiente filtra todos os gráficos. Período filtra KPIs, série diária e "
                   "histograma. Faixa de temperatura filtra KPIs e histograma.")

if not ambientes:
    st.warning("Selecione ao menos um ambiente.")
    st.stop()
ini, fim = (periodo if isinstance(periodo, tuple) and len(periodo) == 2
            else (limites.ini, limites.fim))
filtro = {"amb": list(ambientes), "ini": ini, "fim": fim, "tmin": faixa[0], "tmax": faixa[1]}
WHERE = ("location = ANY(:amb) AND noted_at::date BETWEEN :ini AND :fim "
         "AND temperature BETWEEN :tmin AND :tmax")

# ---------------------------------------------------------------- cabeçalho
st.title("Dashboard IoT — Monitoramento de Temperatura")
st.caption("Pipeline: Kaggle CSV → Python/Pandas → PostgreSQL (Docker) → Views SQL → Streamlit + Plotly · "
           "Dataset: *Temperature Readings: IoT Devices* (sensor da sala 'Room Admin', 2018)")

kpi = query(f"""SELECT COUNT(*) AS total, AVG(temperature) AS media,
                       MAX(temperature) AS maxima, MIN(temperature) AS minima
                FROM temperature_readings WHERE {WHERE}""", filtro).iloc[0]
if kpi.total == 0:
    st.warning("Nenhuma leitura com esses filtros.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total de leituras", f"{int(kpi.total):,}".replace(",", "."))
c2.metric("Temperatura média", f"{kpi.media:.1f} °C".replace(".", ","))
c3.metric("Temperatura máxima", f"{int(kpi.maxima)} °C")
c4.metric("Temperatura mínima", f"{int(kpi.minima)} °C")

st.divider()

# ---------------------------------------------------------------- gráfico 1 (view 1)
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("1. Temperatura por ambiente")
    v1 = nome_ambiente(query("SELECT * FROM temperatura_media_ambiente WHERE ambiente = ANY(:amb) "
                             "ORDER BY ambiente", {"amb": list(ambientes)}))
    fig1 = px.bar(v1, x="ambiente_nome", y="temperatura_media", color="ambiente",
                  color_discrete_map=CORES, text="temperatura_media",
                  error_y="desvio_padrao",
                  hover_data={"ambiente": False, "quantidade_leituras": ":,",
                              "temperatura_minima": True, "temperatura_maxima": True},
                  labels={"ambiente_nome": "Ambiente", "temperatura_media": "Temperatura média (°C)",
                          "quantidade_leituras": "Leituras", "temperatura_minima": "Mínima (°C)",
                          "temperatura_maxima": "Máxima (°C)", "desvio_padrao": "Desvio padrão"},
                  title="Média com desvio padrão (°C)")
    fig1.update_traces(texttemplate="%{text:.1f} °C", textposition="inside", insidetextanchor="start", textfont_size=16)
    fig1.update_layout(**{**LAYOUT, "hovermode": "closest", "showlegend": False})
    st.plotly_chart(fig1, width="stretch")
    st.caption("Fonte: view `temperatura_media_ambiente`")

# ---------------------------------------------------------------- gráfico 2 (view 2)
with col_b:
    st.subheader("2. Leituras por hora do dia")
    v2 = nome_ambiente(query("SELECT * FROM leituras_por_hora WHERE ambiente = ANY(:amb)",
                             {"amb": list(ambientes)}))
    fig2 = px.bar(v2, x="hora", y="quantidade_leituras", color="ambiente",
                  color_discrete_map=CORES, hover_data={"temperatura_media": ":.1f"},
                  labels={"hora": "Hora do dia (0–23 h)", "quantidade_leituras": "Quantidade de leituras",
                          "ambiente": "Ambiente", "temperatura_media": "Temp. média (°C)"},
                  title="Leituras por hora (empilhado por ambiente)")
    fig2.for_each_trace(lambda t: t.update(name=ROTULOS[t.name]))
    fig2.update_layout(**LAYOUT)
    fig2.update_xaxes(dtick=2)
    st.plotly_chart(fig2, width="stretch")
    st.caption("Fonte: view `leituras_por_hora`. Passe o mouse para ver a temperatura média da hora.")

# ---------------------------------------------------------------- gráfico 3 (view 3)
st.subheader("3. Temperatura ao longo do tempo")
v3 = query("SELECT * FROM temperatura_por_dia WHERE ambiente = ANY(:amb) "
           "AND data BETWEEN :ini AND :fim ORDER BY data", filtro)
amb3 = st.radio("Ambiente da série diária", ambientes, horizontal=True, format_func=ROTULOS.get)
d3 = v3[v3["ambiente"] == amb3].melt(
    id_vars=["data", "quantidade_leituras"],
    value_vars=["temperatura_maxima", "temperatura_media", "temperatura_minima"],
    var_name="medida", value_name="temp")
d3["medida"] = d3["medida"].map({"temperatura_maxima": "Máxima", "temperatura_media": "Média",
                                 "temperatura_minima": "Mínima"})
fig3 = px.line(d3, x="data", y="temp", color="medida", markers=True,
               color_discrete_map={"Máxima": "#DC2626", "Média": "#6B7280", "Mínima": "#2563EB"},
               hover_data={"quantidade_leituras": ":,"},
               labels={"data": "Data", "temp": "Temperatura (°C)", "medida": "Medida",
                       "quantidade_leituras": "Leituras no dia"},
               title=f"Máxima, média e mínima diárias — {ROTULOS[amb3]}")
fig3.update_layout(**{**LAYOUT, "legend": {**LAYOUT["legend"], "title": "Medida"}})
st.plotly_chart(fig3, width="stretch")
st.caption("Fonte: view `temperatura_por_dia`. Dias sem leituras aparecem como saltos na linha: o sensor não enviou dados em todos os dias.")

# ---------------------------------------------------------------- gráfico 4 (extra)
st.subheader("4. Distribuição das temperaturas")
hist = nome_ambiente(query(f"""SELECT location AS ambiente, temperature, COUNT(*) AS leituras
                               FROM temperature_readings WHERE {WHERE}
                               GROUP BY location, temperature""", filtro))
fig4 = px.bar(hist, x="temperature", y="leituras", color="ambiente", barmode="overlay",
              color_discrete_map=CORES, opacity=0.75,
              labels={"temperature": "Temperatura (°C)", "leituras": "Quantidade de leituras",
                      "ambiente": "Ambiente"},
              title="Quantas leituras registraram cada temperatura (respeita todos os filtros)")
fig4.for_each_trace(lambda t: t.update(name=ROTULOS[t.name]))
fig4.update_layout(**LAYOUT)
st.plotly_chart(fig4, width="stretch")

with st.expander("Ver dados das views"):
    st.write("**temperatura_media_ambiente**"); st.dataframe(v1.drop(columns="ambiente_nome"), hide_index=True)
    st.write("**leituras_por_hora**"); st.dataframe(v2.drop(columns="ambiente_nome"), hide_index=True)
    st.write("**temperatura_por_dia**"); st.dataframe(v3, hide_index=True)
