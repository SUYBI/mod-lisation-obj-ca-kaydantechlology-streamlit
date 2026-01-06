import streamlit as st
import pandas as pd
import plotly.express as px
from difflib import get_close_matches

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(page_title="Prévision CA", layout="wide")

CAGR = 0.03  # 3 %

# =====================================================
# SECTEURS & TAUX
# =====================================================
SECTEURS = {
    "Finance": {"Télécom": 0.45, "Solutions digitales": 3.0, "Cyber sécurité": 0.75, "Data IA": 1.10},
    "Industrie": {"Télécom": 0.30, "Solutions digitales": 1.15, "Cyber sécurité": 0.35, "Data IA": 0.55},
    "Transport": {"Télécom": 0.45, "Solutions digitales": 1.50, "Cyber sécurité": 0.35, "Data IA": 0.70},
    "Énergie / Mines": {"Télécom": 0.50, "Solutions digitales": 1.15, "Cyber sécurité": 0.50, "Data IA": 0.55},
    "Services": {"Télécom": 0.45, "Solutions digitales": 2.25, "Cyber sécurité": 0.45, "Data IA": 0.85},
    "BTP": {"Télécom": 0.30, "Solutions digitales": 0.85, "Cyber sécurité": 0.20, "Data IA": 0.35},
    "EPN": {"Télécom": 0.60, "Solutions digitales": 2.25, "Cyber sécurité": 0.50, "Data IA": 0.70},
    "Télécom & TIC": {"Télécom": 2.50, "Solutions digitales": 2.25, "Cyber sécurité": 0.65, "Data IA": 1.00},
    "Organisation": {"Télécom": 0.45, "Solutions digitales": 1.00, "Cyber sécurité": 0.20, "Data IA": 0.40}
}

SECTEURS_LIST = list(SECTEURS.keys())
T_SECTEURS_LIST = {i.upper(): i for i in SECTEURS_LIST}



# =====================================================
# CAGR PAR SECTEUR (NOUVEAU – AJOUT SEULEMENT)
# =====================================================
CAGR_SECTEURS = {
    "Finance": 0.04,
    "Industrie": 0.03,
    "Transport": 0.035,
    "Énergie / Mines": 0.045,
    "Services": 0.038,
    "BTP": 0.03,
    "EPN": 0.042,
    "Télécom & TIC": 0.05,
    "Organisation": 0.03
}

def get_cagr(secteur):
    # fallback à 3 % si secteur non trouvé
    return CAGR_SECTEURS.get(secteur, 0.03)


# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.header("📌 Référentiel de benchmark")
st.sidebar.markdown(
    """
    **Source du modèle :**
    - Benchmarks sectoriels
    - Télécom, Digital, Cyber, Data IA

    **Hypothèses :**
    - Budget  proportionnel au CA
    - Approche macro sectorielle
    - Objectif : cadrage stratégique
    """
)

# =====================================================
# SESSION STATE INIT
# =====================================================
if "df_pred" not in st.session_state:
    st.session_state.df_pred = None

if "df_excel_pred" not in st.session_state:
    st.session_state.df_excel_pred = None

if "excel_unresolved_values" not in st.session_state:
    st.session_state.excel_unresolved_values = set()

# =====================================================
# TABS
# =====================================================
tab1, tab2 = st.tabs(["📊 Simulation unitaire", "📁 Simulation via Excel"])

# =====================================================
# TAB 1 — SIMULATION UNITAIRE
# =====================================================
with tab1:
    st.subheader("Simulation unitaire")

    col1, col2 = st.columns(2)
    with col1:
        ca = st.number_input("CA annuel", min_value=0.0, step=1_000_000.0, format="%.0f")

    with col2:
        mode = st.sidebar.radio("Mode d’analyse", ["Analyse simple", "Comparaison de secteurs"])
        if mode == "Analyse simple":
            secteurs_sel = [st.selectbox("Secteur", SECTEURS_LIST)]
        else:
            secteurs_sel = st.multiselect(
                "Secteurs", SECTEURS_LIST, default=["Finance", "Télécom & TIC"]
            )

    if st.button("🚀 Predict", key="predict_unit"):
        results = []
        for sec in secteurs_sel:
            for cat, taux in SECTEURS[sec].items():
                results.append({
                    "Secteur": sec,
                    "Catégorie": cat,
                    "Taux (%)": taux,
                    "Prévision budget": ca * taux / 100
                })
        st.session_state.df_pred = pd.DataFrame(results)

    if st.session_state.df_pred is not None:
        df = st.session_state.df_pred
        st.dataframe(df, use_container_width=True)

        total_budget = df["Prévision budget"].sum()
        taux_global = (total_budget / ca * 100) if ca > 0 else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("💰 CA analysé", f"{ca:,.0f}")
        c2.metric("📊 Budget IT prédit", f"{total_budget:,.0f}")
        c3.metric("📈 Taux global IT", f"{taux_global:.2f} %")

        if mode == "Analyse simple":
            fig_bar = px.bar(
                df,
                x="Catégorie",
                y="Prévision budget",
                title="Budget IT par catégorie"
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            fig_pie = px.pie(
                df,
                names="Catégorie",
                values="Prévision budget",
                title="Répartition du budget IT"
            )
            st.plotly_chart(fig_pie, use_container_width=True)

            st.markdown("### 📈 Projection des budgets (CAGR 3 %)")

            if st.button("📊 Prédire 2027, 2028"):
                secteur = df["Secteur"].iloc[0]
                cagr = get_cagr(secteur)

                df["Prévision budget 2027"] = df["Prévision budget"] * (1 + cagr)
                df["Prévision budget 2028"] = df["Prévision budget"] * (1 + cagr) ** 2

                st.session_state.df_pred = df

                st.dataframe(df, use_container_width=True)

                df_trend = df.melt(
                    id_vars=["Secteur", "Catégorie"],
                    value_vars=[
                        "Prévision budget",
                        "Prévision budget 2027",
                        "Prévision budget 2028"
                    ],
                    var_name="Année",
                    value_name="Budget"
                )
                df_trend["Année"] = df_trend["Année"].replace({
                    "Prévision budget": "2026",
                    "Prévision budget 2027": "2027",
                    "Prévision budget 2028": "2028"
                })

                fig_trend = px.line(
                    df_trend,
                    x="Année",
                    y="Budget",
                    color="Catégorie",
                    markers=True,
                    title="Évolution du budget IT (2026–2028)"
                )
                st.plotly_chart(fig_trend, use_container_width=True)

        else:
            fig_comp = px.bar(
                df,
                x="Catégorie",
                y="Prévision budget",
                color="Secteur",
                barmode="group",
                title="Comparaison inter-sectorielle"
            )
            st.plotly_chart(fig_comp, use_container_width=True)

# =====================================================
# TAB 2 — SIMULATION VIA EXCEL (AVEC SESSION STATE)
# =====================================================
with tab2:
    st.subheader("Simulation en masse via Excel")

    file = st.file_uploader("📥 Charger un fichier Excel", type=["xlsx"])

    if file:
        df_raw = pd.read_excel(file)

        if not {"SECTEUR", "CA/TOTAL BILAN"}.issubset(df_raw.columns):
            st.error("Le fichier doit contenir 'SECTEUR' et 'CA/TOTAL BILAN'")
            st.stop()

        df_raw["SECTEUR-GROUPE"] = None
        unresolved_values = set()

        for idx, secteur in df_raw["SECTEUR"].items():
            match = get_close_matches(
                str(secteur).upper(),
                [s.upper() for s in SECTEURS_LIST],
                n=1,
                cutoff=0.75
            )
            if match:
                df_raw.at[idx, "SECTEUR-GROUPE"] = T_SECTEURS_LIST[match[0]]
            else:
                unresolved_values.add(str(secteur))

        st.session_state.excel_unresolved_values = unresolved_values

        # ============================
        # STATS AU CHARGEMENT (incluant non reconnus)
        # ============================
        st.markdown("### 📌 Statistiques du fichier")
        c1, c2, c3 = st.columns(3)
        c1.metric("Lignes", len(df_raw))
        c2.metric("Secteurs uniques", df_raw["SECTEUR"].nunique())
        c3.metric("Secteurs non reconnus", len(unresolved_values))

        # ============================
        # PREDICTION INITIALE
        # ============================
        if st.button("🚀 Predict sur le fichier"):
            df = df_raw.copy()

            for cat in ["Télécom", "Solutions digitales", "Cyber sécurité", "Data IA"]:
                df[cat] = df.apply(
                    lambda r: (
                        r["CA/TOTAL BILAN"] * SECTEURS[r["SECTEUR-GROUPE"]][cat] / 100
                        if pd.notna(r["SECTEUR-GROUPE"])
                        else None
                    ),
                    axis=1
                )

            st.session_state.df_excel_pred = df

        # ============================
        # AFFICHAGE RESULTATS + STATS APRÈS PRÉDICTION
        # ============================
        if st.session_state.df_excel_pred is not None:
            df = st.session_state.df_excel_pred

            predicted_rows = df["Télécom"].notna().sum()
            total_budget = df[["Télécom", "Solutions digitales", "Cyber sécurité", "Data IA"]].sum().sum()

            st.markdown("### 📊 Résultats de la prédiction")
            c1, c2, c3 = st.columns(3)
            c1.metric("CA analysé", f"{df['CA/TOTAL BILAN'].sum():,.0f}")
            c2.metric("CA prédit", f"{total_budget:,.0f}")
            c3.metric("Lignes prédites", f"{predicted_rows}/{len(df)}")

            if predicted_rows < len(df):
                st.warning("⚠️ Certaines lignes n'ont pas été prédites (secteur non corrigé)")

            st.dataframe(df, use_container_width=True)

            # ============================
            # PROJECTION 2027–2028
            # ============================
            st.markdown("### 📈 Projection des budgets (CAGR)")

            if st.button("📊 Prédire 2027, 2028 (Excel)"):
                for cat in ["Télécom", "Solutions digitales", "Cyber sécurité", "Data IA"]:
                    df[f"{cat} 2027"] = df.apply(
                        lambda r: r[cat] * (1 + get_cagr(r["SECTEUR-GROUPE"]))
                        if pd.notna(r[cat]) else None,
                        axis=1
                    )

                    df[f"{cat} 2028"] = df.apply(
                        lambda r: r[cat] * (1 + get_cagr(r["SECTEUR-GROUPE"])) ** 2
                        if pd.notna(r[cat]) else None,
                        axis=1
                    )

                st.session_state.df_excel_pred = df

            st.dataframe(df, use_container_width=True)


            # ============================
            # GRAPHE TENDANCE
            # ============================
            df_trend = df.melt(
                id_vars=["SECTEUR-GROUPE"],
                value_vars=[c for c in df.columns if "2027" in c or "2028" in c],
                var_name="Année",
                value_name="Budget"
            )

            fig_trend = px.line(
                df_trend,
                x="Année",
                y="Budget",
                color="SECTEUR-GROUPE",
                title="Tendance budgétaire 2026–2028 (Excel)"
            )

            st.plotly_chart(fig_trend, use_container_width=True)