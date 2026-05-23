"""
streamlit_app.py — Demo del KG-GenAI (Grupo 2).

Lee data/kg.ttl con rdflib (in-memory) y permite explorar el KG con consultas SPARQL
predefinidas. Esta hecho como herramienta para un *investigador junior* organizando una
revision bibliografica de 30 papers de IA generativa.

Sketch initially generated with AI assistance, subsequently reviewed by the group.

Uso:
    streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from rdflib import Graph

PROJECT_ROOT = Path(__file__).resolve().parents[1]
KG_PATH = PROJECT_ROOT / "data" / "kg.ttl"

NS = "https://w3id.org/oeg/grupo2/ontology#"
RES = "https://w3id.org/oeg/grupo2/resource/"

st.set_page_config(page_title="KG-GenAI · Grupo 2", layout="wide")


@st.cache_resource
def load_graph() -> Graph:
    g = Graph()
    if KG_PATH.exists():
        g.parse(str(KG_PATH), format="turtle")
    return g


def run(graph: Graph, query: str):
    prefixes = f"PREFIX ns: <{NS}>\nPREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
    return list(graph.query(prefixes + query))


def short(uri: str) -> str:
    return str(uri).replace(NS, "ns:").replace(RES, "")


# -----------------------------
st.title("📚 KG-GenAI · Acelerador de estado del arte")
st.caption("Grupo 2 — OS&AI in RSE · UPM · OEG")

g = load_graph()
if len(g) == 0:
    st.error(
        f"No se ha podido cargar el KG en {KG_PATH}. "
        "Ejecuta antes el pipeline: `python src/07_build_rdf.py`."
    )
    st.stop()

st.success(f"KG cargado: {len(g)} triples.")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["Resumen", "Buscar paper", "Top-similares", "Por tópico", "Modelos & Datasets", "Financiación"]
)

# ----- TAB 1: Resumen -----
with tab1:
    col1, col2, col3 = st.columns(3)
    n_papers = len(list(g.subjects(predicate=None, object=None)))
    counts = {}
    for cls in ["Paper", "Person", "Organization", "Project", "Topic", "Model", "Dataset", "Venue"]:
        rows = run(g, f"SELECT (COUNT(?x) as ?c) WHERE {{ ?x a ns:{cls} . }}")
        counts[cls] = int(rows[0][0]) if rows else 0
    col1.metric("Papers", counts["Paper"])
    col1.metric("Personas", counts["Person"])
    col2.metric("Organizaciones", counts["Organization"])
    col2.metric("Proyectos", counts["Project"])
    col3.metric("Topicos", counts["Topic"])
    col3.metric("Modelos / Datasets", f"{counts['Model']} / {counts['Dataset']}")

# ----- TAB 2: Buscar paper -----
with tab2:
    st.subheader("Detalle de un paper")
    papers = run(g, "SELECT ?p ?t WHERE { ?p a ns:Paper ; ns:title ?t . } ORDER BY ?t")
    options = {f"{short(p)} — {str(t)[:80]}": p for p, t in papers}
    pick = st.selectbox("Paper", list(options.keys()))
    if pick:
        p = options[pick]
        rows = run(g, f"""
        SELECT ?prop ?val WHERE {{
          <{p}> ?prop ?val .
        }}
        """)
        for prop, val in rows:
            st.write(f"- **{short(prop)}**: `{short(val)}`" if str(val).startswith(("http", "https")) else f"- **{short(prop)}**: {val}")

# ----- TAB 3: Top similares -----
with tab3:
    st.subheader("Papers más similares a uno dado")
    papers = run(g, "SELECT ?p ?t WHERE { ?p a ns:Paper ; ns:title ?t . } ORDER BY ?t")
    options = {f"{short(p)} — {str(t)[:80]}": p for p, t in papers}
    pick = st.selectbox("Paper origen", list(options.keys()), key="sim_pick")
    if pick:
        p = options[pick]
        rows = run(g, f"""
        SELECT DISTINCT ?other ?title WHERE {{
          <{p}> ns:similar_to ?other .
          ?other ns:title ?title .
        }}
        """)
        if not rows:
            st.info("No hay papers conectados por `similar_to`. (Recuerda: umbral configurable en 04_similarity.py).")
        for other, title in rows[:10]:
            st.write(f"- **{short(other)}**: {title}")

# ----- TAB 4: Por topico -----
with tab4:
    st.subheader("Papers agrupados por tópico")
    topics = run(g, "SELECT ?t ?lab WHERE { ?t a ns:Topic . OPTIONAL { ?t ns:label ?lab } } ORDER BY ?lab")
    for t, lab in topics:
        with st.expander(f"{lab if lab else short(t)}"):
            papers = run(g, f"""
            SELECT ?p ?title WHERE {{
              ?p ns:belongs_to_topic <{t}> ; ns:title ?title .
            }}
            """)
            for p, title in papers:
                st.write(f"- **{short(p)}**: {title}")

# ----- TAB 5: Modelos y Datasets -----
with tab5:
    st.subheader("Modelos HuggingFace referenciados")
    rows = run(g, """
    SELECT ?m ?mid ?pt ?pcount WHERE {
      ?m a ns:Model ; ns:modelId ?mid .
      OPTIONAL { ?m ns:pipelineTag ?pt }
      {
        SELECT ?m (COUNT(DISTINCT ?p) AS ?pcount) WHERE {
          ?p ns:usesModel ?m .
        } GROUP BY ?m
      }
    } ORDER BY DESC(?pcount)
    """)
    for m, mid, pt, pcount in rows:
        st.write(f"- **{mid}** ({pt or '-'}) — usado por {int(pcount)} papers")

    st.subheader("Datasets HuggingFace referenciados")
    rows = run(g, """
    SELECT ?d ?did ?pcount WHERE {
      ?d a ns:Dataset ; ns:datasetId ?did .
      {
        SELECT ?d (COUNT(DISTINCT ?p) AS ?pcount) WHERE {
          ?p ns:usesDataset ?d .
        } GROUP BY ?d
      }
    } ORDER BY DESC(?pcount)
    """)
    for d, did, pcount in rows:
        st.write(f"- **{did}** — usado por {int(pcount)} papers")

# ----- TAB 6: Financiacion -----
with tab6:
    st.subheader("Proyectos y agencias financiadoras")
    rows = run(g, """
    SELECT ?proj ?grant ?title ?funder ?fname WHERE {
      ?proj a ns:Project .
      OPTIONAL { ?proj ns:grantNumber ?grant }
      OPTIONAL { ?proj ns:title ?title }
      OPTIONAL { ?proj ns:hasFunder ?funder . ?funder ns:name ?fname . }
    }
    """)
    for proj, grant, title, funder, fname in rows:
        st.write(f"- **{title or short(proj)}** (grant: {grant or '-'}) financiado por **{fname or '-'}**")
