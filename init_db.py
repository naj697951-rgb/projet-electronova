import os
import glob
import sqlite3
import pandas as pd

print("⏳ Début de l'initialisation de la base de données...")

# 1. Recherche automatique du fichier Excel dans le dossier
fichiers_excel = glob.glob("*.xlsx")
if not fichiers_excel:
    print("❌ Erreur : Aucun fichier Excel (.xlsx) trouvé dans le dossier !")
    exit()

nom_fichier_excel = fichiers_excel[0]
print(f"📁 Fichier Excel détecté : {nom_fichier_excel}")

# 2. Lecture des feuilles de l'Excel
excel_obj = pd.ExcelFile(nom_fichier_excel)
noms_feuilles = excel_obj.sheet_names
print(f"📑 Feuilles trouvées : {noms_feuilles}")

# Connexion à la base de données SQLite (crée le fichier electronova.db)
conn = sqlite3.connect("electronova.db")

# 3. Chargement et enregistrement de chaque feuille dans la base SQL
for feuille in noms_feuilles:
    nom_table = feuille.strip()
    
    # Nettoyage des noms de table pour SQL (éviter les accents)
    if "vent" in nom_table.lower():
        table_sql = "Ventes"
    elif "employ" in nom_table.lower():
        table_sql = "Employes"
    elif "produit" in nom_table.lower():
        table_sql = "Produits"
    else:
        table_sql = nom_table

    # Lecture des données de la feuille
    df = pd.read_excel(nom_fichier_excel, sheet_name=feuille)
    
    # Enregistrement permanent dans SQLite
    df.to_sql(table_sql, conn, if_exists="replace", index=False)
    print(f"✅ Table SQL créée : '{table_sql}' avec {len(df)} lignes.")

# 4. Requête SQL de contrôle (Chapitre IV : fonctions d'agrégation SUM)
cur = conn.cursor()
try:
    # On vérifie la somme du CA et de la Marge
    cur.execute("SELECT SUM(ca), SUM(marge_brute), COUNT(*) FROM Ventes;")
    ca_total, marge_totale, nb_ventes = cur.fetchone()
    
    print("\n--------------------------------------------------")
    print("🎯 VÉRIFICATION DES CHIFFRES AVEC LE COLLÈGUE :")
    print(f"   • Chiffre d'Affaires total : {ca_total:,.2f} MAD")
    print(f"   • Marge Brute totale       : {marge_totale:,.2f} MAD")
    print(f"   • Nombre de ventes         : {nb_ventes} transactions")
    print("--------------------------------------------------")
    
    if round(ca_total, 0) == 11709813:
        print("🎉 PARFAIT ! Le CA concorde exactement avec 11,71 M MAD !")
    else:
        print("⚠️ Attention : le montant diffère légèrement, nous ajusterons si nécessaire.")

except Exception as e:
    print(f"ℹ️ Note sur la requête de contrôle : {e}")

conn.close()
print("\n🚀 Base 'electronova.db' prête pour Streamlit !")