import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression

# ----------------- 1. CONFIGURATION & DESIGN CSS PROFESSIONNEL -----------------
st.set_page_config(
    page_title="ElectroNova Maroc | Dashboard Commercial",
    page_icon="📈",
    layout="wide"
)

# Injection de style CSS pour cartes KPIs modernes et lisibles (aucun chiffre coupé !)
st.markdown("""
<style>
    .kpi-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px 20px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        margin-bottom: 10px;
    }
    .kpi-title {
        font-size: 0.90rem;
        font-weight: 600;
        color: #64748b;
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-value {
        font-size: 1.70rem;
        font-weight: 700;
        color: #0f172a;
    }
    .kpi-sub {
        font-size: 0.80rem;
        color: #10b981;
        font-weight: 500;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- 2. CHARGEMENT & EXTRACTION SQL -----------------
@st.cache_data
def charger_donnees():
    conn = sqlite3.connect("electronova.db")
    df_ventes = pd.read_sql_query("SELECT * FROM Ventes;", conn)
    
    try:
        df_employes = pd.read_sql_query("SELECT * FROM Employes;", conn)
    except:
        df_employes = pd.DataFrame()
        
    conn.close()
    
    df_ventes.columns = [c.lower() for c in df_ventes.columns]
    if not df_employes.empty:
        df_employes.columns = [c.lower() for c in df_employes.columns]
    
    # Gestion des dates
    col_date = [c for c in df_ventes.columns if 'date' in c][0]
    df_ventes['date_dt'] = pd.to_datetime(df_ventes[col_date])
    df_ventes['annee'] = df_ventes['date_dt'].dt.year
    df_ventes['mois_annee'] = df_ventes['date_dt'].dt.to_period('M').dt.to_timestamp()
    
    return df_ventes, df_employes

df, df_emp = charger_donnees()

# ----------------- 3. BARRE LATÉRALE : FILTRES INTERACTIFS -----------------
st.sidebar.title("Filtres d'Analyse")

# 1. Filtre par Région avec "Toutes" par défaut
liste_regions = ["Toutes"] + sorted(list(df['region'].dropna().unique()))
region_choisie = st.sidebar.selectbox("Filtrer par Région :", options=liste_regions)

# 2. Filtre par Produit avec "Tous" par défaut
liste_produits = ["Tous"] + sorted(list(df['produit'].dropna().unique()))
produit_choisi = st.sidebar.selectbox("Filtrer par Produit :", options=liste_produits)

# 3. Filtre par Année avec "Toutes" par défaut
liste_annees = ["Toutes"] + sorted([str(a) for a in df['annee'].unique()])
annee_choisie = st.sidebar.selectbox("Filtrer par Année :", options=liste_annees)

# Application dynamique des filtres
df_filtre = df.copy()

if region_choisie != "Toutes":
    df_filtre = df_filtre[df_filtre['region'] == region_choisie]

if produit_choisi != "Tous":
    df_filtre = df_filtre[df_filtre['produit'] == produit_choisi]

if annee_choisie != "Toutes":
    df_filtre = df_filtre[df_filtre['annee'] == int(annee_choisie)
    ]


# ----------------- 4. EN-TÊTE & CARTES KPIS SANS TRONCATURE -----------------
st.title(" ElectroNova Maroc — Tableau de Bord Commercial")

ca_total = df_filtre['ca'].sum()
marge_totale = df_filtre['marge_brute'].sum()
taux_marge = (marge_totale / ca_total * 100) if ca_total > 0 else 0
nb_ventes = len(df_filtre)
volume_total = df_filtre['quantite'].sum()

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">💰 Chiffre d'Affaires</div>
        <div class="kpi-value">{ca_total/1e6:.2f} M MAD</div>
        <div class="kpi-sub">{ca_total:,.0f} MAD exact</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">📈 Marge Brute</div>
        <div class="kpi-value">{marge_totale/1e6:.2f} M MAD</div>
        <div class="kpi-sub">{marge_totale:,.0f} MAD exact</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">🎯 Taux de Marge Moyen</div>
        <div class="kpi-value">{taux_marge:.1f} %</div>
        <div class="kpi-sub">Rentabilité commerciale</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">📦 Volume des Ventes</div>
        <div class="kpi-value">{volume_total:,.0f} unités</div>
        <div class="kpi-sub">{nb_ventes:,} transactions</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# ----------------- 5. ONGLETS DE VISUALISATION -----------------
tab_global, tab_comparatif, tab_predict, tab_sql = st.tabs([
    "📊 Vue Globale & Produits",
    "⚖️ Analyses Comparatives (Régions & Vendeurs)",
    "🤖 Prévisions & Data Science",
    "🗄️ Données SQL & Export"
])

# ==================== ONGLET 1 : VUE GLOBALE ====================
with tab_global:
    g1, g2 = st.columns(2)
    
    with g1:
        st.subheader("📍 Répartition du CA par Région")
        ca_reg = df_filtre.groupby('region')['ca'].sum().reset_index().sort_values(by='ca', ascending=True)
        fig_reg = px.bar(
            ca_reg, x='ca', y='region', orientation='h', text_auto='.2s',
            color='ca', color_continuous_scale='Blues',
            labels={'ca': 'CA (MAD)', 'region': 'Région'}
        )
        fig_reg.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig_reg, use_container_width=True)

    with g2:
        st.subheader("🥧 Part de Marché par Catégorie/Produit")
        top_p = df_filtre.groupby('produit')['ca'].sum().reset_index()
        fig_pie = px.pie(
            top_p, names='produit', values='ca', hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig_pie.update_layout(height=380)
        st.plotly_chart(fig_pie, use_container_width=True)

# ==================== ONGLET 2 : ANALYSES COMPARATIVES ====================
with tab_comparatif:
    st.subheader("⚖️ Comparatif Multi-Dimensionnel")
    st.info("Cette section compare directement la performance financière et managériale entre les régions et la force de vente.")
    
    comp1, comp2 = st.columns(2)
    
    with comp1:
        st.markdown("#### 1. Comparaison Régionale : CA vs Marge Brute")
        reg_comp = df_filtre.groupby('region')[['ca', 'marge_brute']].sum().reset_index()
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(
            x=reg_comp['region'], y=reg_comp['ca'], name="Chiffre d'Affaires (MAD)", marker_color='#2563eb'
        ))
        fig_comp.add_trace(go.Bar(
            x=reg_comp['region'], y=reg_comp['marge_brute'], name="Marge Brute (MAD)", marker_color='#10b981'
        ))
        fig_comp.update_layout(barmode='group', height=400, xaxis_tickangle=-25)
        st.plotly_chart(fig_comp, use_container_width=True)
        
    with comp2:
        st.markdown("#### 2. Classement des Équipes Commerciales (Employés)")
        if not df_emp.empty:
            # Calcul du CA par région pour les vendeurs
            ca_par_reg = df.groupby('region')['ca'].sum().reset_index()
            df_perf_emp = pd.merge(df_emp, ca_par_reg, on='region', how='left')
            
            fig_emp = px.scatter(
                df_perf_emp, x='ca', y='performance', size='ca', color='nom',
                hover_name='region', text='nom',
                labels={'ca': 'CA généré par la Région (MAD)', 'performance': 'Score Performance'},
                title="Score de Performance vs CA Régional"
            )
            fig_emp.update_traces(textposition='top center')
            fig_emp.update_layout(height=400)
            st.plotly_chart(fig_emp, use_container_width=True)
        else:
            st.warning("Table Employés non trouvée pour le classement individuel.")

    st.markdown("#### 3. Rentabilité Comparée des Produits")
    prod_comp = df_filtre.groupby('produit').agg({'ca': 'sum', 'marge_brute': 'sum', 'quantite': 'sum'}).reset_index()
    prod_comp['taux_marge_%'] = (prod_comp['marge_brute'] / prod_comp['ca']) * 100
    
    fig_bubble = px.scatter(
        prod_comp, x='quantite', y='taux_marge_%', size='ca', color='produit',
        hover_name='produit', text='produit',
        labels={'quantite': 'Quantité Totale Vendue', 'taux_marge_%': 'Taux de Marge (%)'},
        title="Matrice Volume vs Taux de Rentabilité (Taille de la bulle = CA Total)"
    )
    fig_bubble.update_traces(textposition='top center')
    fig_bubble.update_layout(height=420)
    st.plotly_chart(fig_bubble, use_container_width=True)

# ==================== ONGLET 3 : DATA SCIENCE & PRÉVISIONS ====================
with tab_predict:
    st.subheader("🤖 Prévision du Chiffre d'Affaires Futur (Machine Learning)")
    st.markdown("Application d'un modèle de **Régression Linéaire temporelle** sur l'historique mensuel des ventes pour projeter la tendance future.")
    
    # Agrégation mensuelle
    serie_m = df.groupby('mois_annee')['ca'].sum().reset_index().sort_values('mois_annee')
    serie_m['index_temps'] = np.arange(len(serie_m))
    
    # Entraînement Scikit-Learn
    X = serie_m[['index_temps']]
    y = serie_m['ca']
    
    modele = LinearRegression()
    modele.fit(X, y)
    
    # Prévisions 3 mois
    dernier_idx = serie_m['index_temps'].max()
    indices_futurs = np.array([[dernier_idx + 1], [dernier_idx + 2], [dernier_idx + 3]])
    predictions = modele.predict(indices_futurs)
    
    derniere_date = serie_m['mois_annee'].max()
    dates_futures = [
        derniere_date + pd.DateOffset(months=1),
        derniere_date + pd.DateOffset(months=2),
        derniere_date + pd.DateOffset(months=3)
    ]
    
    df_pred = pd.DataFrame({'mois_annee': dates_futures, 'ca': predictions, 'type': 'Prévision (Modèle IA)'})
    serie_m['type'] = 'Historique Réel'
    
    df_trend = pd.concat([serie_m[['mois_annee', 'ca', 'type']], df_pred])
    
    fig_trend = px.line(
        df_trend, x='mois_annee', y='ca', color='type', markers=True,
        labels={'ca': 'CA Mensuel (MAD)', 'mois_annee': 'Mois'},
        color_discrete_map={'Historique Réel': '#2563eb', 'Prévision (Modèle IA)': '#f97316'}
    )
    fig_trend.update_layout(height=450)
    st.plotly_chart(fig_trend, use_container_width=True)
    
    p1, p2, p3 = st.columns(3)
    p1.metric(f"Prévision {dates_futures[0].strftime('%b %Y')}", f"{predictions[0]:,.0f} MAD")
    p2.metric(f"Prévision {dates_futures[1].strftime('%b %Y')}", f"{predictions[1]:,.0f} MAD")
    p3.metric(f"Prévision {dates_futures[2].strftime('%b %Y')}", f"{predictions[2]:,.0f} MAD")

# ==================== ONGLET 4 : DONNÉES SQL ====================
with tab_sql:
    st.subheader("🗄️ Registre des Ventes (Extrait SQL)")
    st.dataframe(df_filtre[['id', 'date_dt', 'region', 'produit', 'quantite', 'prix', 'ca', 'marge_brute']], use_container_width=True)
    
    csv = df_filtre.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Télécharger les données filtrées (CSV)", data=csv, file_name="ventes_electronova.csv", mime="text/csv")