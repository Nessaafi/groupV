# # 01 – Nettoyage SHP (population + revenu + ménage)
# Projet « Paid to Be Replaced? » – Group V
#
# **Données :** ce notebook ne contient aucune donnée. Il lit les fichiers SHP (FORS) qui doivent se trouver sur ton ordinateur. Ces fichiers ne se partagent pas (contrat FORS) : ni sur GitHub, ni à une IA, ni à une personne extérieure au groupe.
#
# Ordre des étapes :
# 1. Indiquer où sont les 3 fichiers
# 2. Charger seulement les colonnes utiles
# 3. Garder 2016-2024
# 4. Valeurs négatives → NaN
# 5. Inspecter les codes (comptages seulement)
# 6. Codes utilisés pour les filtres (vérifiés)
# 7. Fusionner avec les fichiers revenus et ménage
# 8. Filtrer : personnes qui travaillent, salariées, 25-65 ans, métier connu
# 9. Créer les nouvelles variables
# 10. Retirer les salaires impossibles et les 1 % extrêmes
# 11. Vérifier et enregistrer

# ## Étape 1 – Où sont les fichiers
# **Pourquoi :** Python doit savoir où lire les données. Les chemins sont mis une seule fois, en haut, pour pouvoir les changer facilement.
#
# Sur Mac : sélectionne le fichier dans le Finder, puis **⌘ Cmd + ⌥ Option + C** pour copier son chemin.

# %%
import pandas as pd
import numpy as np

CHEMIN_P = "COLLE_ICI_LE_CHEMIN/shplong_p_user.dta"
CHEMIN_REV = "COLLE_ICI_LE_CHEMIN/imputed_income_pers_long_shp.dta"
CHEMIN_H = "COLLE_ICI_LE_CHEMIN/shplong_h_user.dta"

# Le fichier nettoyé sera enregistré ici (le préfixe shp_ le fait ignorer par GitHub via le .gitignore)
SORTIE = "shp_population_income.parquet"

# ## Étape 2 – Charger seulement les colonnes utiles
# **Pourquoi :** le fichier principal a 961 colonnes. En charger 16 est plus rapide et limite les données personnelles manipulées.
#
# `convert_categoricals=False` garde les **codes chiffrés** (par ex. `-3`) au lieu du texte (« inapplicable »). Sans ça, l'étape 4 ne trouverait pas les valeurs négatives.

# %%
COLS_P = ["idpers", "year", "idhous", "pdate", "age", "sex", "isced", "pe31",
          "wstat", "pw29", "pw39", "pw42", "is3maj", "noga2m", "iempyg", "wicss"]
COLS_REV = ["idpers", "year", "iempyni", "impempyn", "cpi2020"]
COLS_H = ["idhous", "year", "canton", "region", "com3_"]

p = pd.read_stata(CHEMIN_P, columns=COLS_P, convert_categoricals=False)
rev = pd.read_stata(CHEMIN_REV, columns=COLS_REV, convert_categoricals=False)
h = pd.read_stata(CHEMIN_H, columns=COLS_H, convert_categoricals=False)

print("Fichier principal :", p.shape)   # (nombre de lignes, nombre de colonnes)
print("Fichier revenus   :", rev.shape)
print("Fichier ménage    :", h.shape)

# ## Étape 3 – Garder 2016-2024
# **Pourquoi :** la période d'étude. 2025 (vague 27) est une version bêta, non vérifiée par FORS.

# %%
p = p[(p["year"] >= 2016) & (p["year"] <= 2024)].copy()
rev = rev[(rev["year"] >= 2016) & (rev["year"] <= 2024)].copy()
h = h[(h["year"] >= 2016) & (h["year"] <= 2024)].copy()

print(p["year"].value_counts().sort_index())   # nombre de lignes par année

# ## Étape 4 – Valeurs négatives → NaN
# **Pourquoi :** dans le SHP, -1 = ne sait pas, -2 = pas de réponse, -3 = question non posée, -7 et -8 = erreurs. Ce ne sont pas de vraies valeurs : un âge de -3 fausserait toutes les moyennes. `NaN` = valeur manquante, que pandas ignore dans les calculs.
#
# On garde une copie des codes d'origine (`p_codes`) pour l'étape 5.

# %%
p_codes = p.copy()   # copie avant nettoyage, pour l'inspection

for df in [p, rev, h]:
    num = df.select_dtypes("number").columns.drop(["idpers", "idhous", "year"], errors="ignore")
    df[num] = df[num].where(df[num] >= 0, np.nan)

# Part de valeurs manquantes par colonne, en %
print((p.isna().mean() * 100).round(1).sort_values(ascending=False))

# ## Étape 5 – Inspecter les codes
# **Pourquoi :** pour filtrer « salarié » ou « tertiaire », il faut savoir quel chiffre correspond à quoi. Cette cellule affiche seulement des **comptages** par code, aucune ligne individuelle.

# %%
COLS_CAT = ["sex", "isced", "wstat", "pw29", "pw39"]

for col in COLS_CAT:
    print("\n=====", col, "=====")
    print(p_codes[col].value_counts(dropna=False).sort_index())

# Test ISCO-08 : les codes 25x et 26x n'existent qu'en ISCO-08
isco_txt = p["is3maj"].dropna().astype(int).astype(str)
print("\n===== Codes ISCO 25x/26x par année (doit être > 0 chaque année) =====")
print(p.loc[isco_txt.index][isco_txt.str[:2].isin(["25", "26"])].groupby("year").size())

for col in ["canton", "region", "com3_"]:
    print("\n=====", col, "=====")
    print(h[col].value_counts(dropna=False).sort_index())

print("\n===== pw42 (temps partiel %) =====")
print(p["pw42"].describe().round(1))

# ## Étape 6 – Codes utilisés pour les filtres (vérifiés)
# **Pourquoi :** les filtres de l'étape 8 dépendent de ces codes. Ils ont été vérifiés avec les libellés du fichier :
# - `isced` 51 = 5A tertiaire général (université, EPF, HES, HEP), 52 = 5B tertiaire professionnel (brevet, ES), 60 = doctorat
# - `wstat` 1 = actif occupé
# - `pw29` 5 = « employee of another private firm or government organisation » (salarié)
# - `pw39` **2 = temps plein** (1 = temps partiel : seules ces personnes ont un % dans `pw42`)

# %%
CODES_TERTIAIRE = [51, 52, 60]   # hautes écoles + formation prof. supérieure + doctorat
CODES_ACTIF_OCCUPE = [1]
CODES_SALARIE = [5]
CODE_TEMPS_PLEIN = 2

# ## Étape 7 – Fusionner avec les fichiers revenus et ménage
# **Pourquoi :** la variable cible `iempyni` est dans le fichier revenus (relié par personne **et** année). Le canton et la région sont dans le fichier ménage (relié par ménage **et** année, car le numéro de ménage change chaque année).
#
# - `how="left"` garde toutes les lignes du fichier principal.
# - `validate=...` fait planter le code en cas de doublon, au lieu de dupliquer des lignes sans prévenir.
# - `indicator=True` compte les lignes qui n'ont pas trouvé de correspondance.

# %%
df = p.merge(rev, on=["idpers", "year"], how="left", validate="one_to_one", indicator=True)
print(df["_merge"].value_counts())   # 'both' = fusion réussie, 'left_only' = pas de revenu trouvé
df = df.drop(columns="_merge")

# Plusieurs personnes peuvent partager le même ménage, d'où "many_to_one"
df = df.merge(h, on=["idhous", "year"], how="left", validate="many_to_one", indicator=True)
print(df["_merge"].value_counts())   # 'left_only' = canton non trouvé
df = df.drop(columns="_merge")

# ## Étape 8 – Filtrer : personnes qui travaillent, salariées, 25-65 ans, métier connu
# **Pourquoi :**
# - Une personne sans emploi n'a pas de salaire ; un indépendant a un revenu qui dépend de son entreprise, pas seulement de son métier.
# - **25 ans minimum** : avant 25 ans, beaucoup de salariés sont apprentis ou étudiants (38 % des 18-24 ans avaient un salaire temps plein < 20 000 CHF). 65 ans = âge de la retraite.
# - Sans code ISCO, impossible de relier la personne au score d'exposition OIT.
#
# On ne filtre **pas** sur le tertiaire : on crée une colonne à l'étape 9. Le tableau affiché va dans la partie Data du rapport.

# %%
etapes = [("Départ", len(df))]

df = df[df["wstat"].isin(CODES_ACTIF_OCCUPE)];  etapes.append(("Personnes qui travaillent", len(df)))
df = df[df["pw29"].isin(CODES_SALARIE)];        etapes.append(("Salariés", len(df)))
df = df[df["age"].between(25, 65)];             etapes.append(("25-65 ans", len(df)))
df = df[df["is3maj"].notna()];                  etapes.append(("Métier ISCO connu", len(df)))

print(pd.DataFrame(etapes, columns=["étape", "lignes restantes"]))

# ## Étape 9 – Créer les nouvelles variables
# **Pourquoi :**
# - `tertiary` : 1 si diplômé du tertiaire (définition OFS : 51, 52, 60), 0 sinon.
# - `tertiary_type` : distingue hautes écoles (51, 60) et formation professionnelle supérieure (52), pour un test de robustesse.
# - `young` : 1 si 25-34 ans.
# - `isco3` : le code métier **en texte**, pour que 011 ne devienne pas 11 et que la fusion avec l'OIT marche.
# - `activity_rate` : 100 pour les temps pleins (ils n'ont pas de pourcentage).
# - `income_real` : salaire en francs de 2020, pour comparer 2016 et 2024 sans l'inflation.
# - `income_fte` : salaire équivalent temps plein, pour comparer un 60 % et un 100 %.

# %%
df["tertiary"] = df["isced"].isin(CODES_TERTIAIRE).astype(int)
df["tertiary_type"] = df["isced"].map({51: "haute_ecole", 60: "haute_ecole", 52: "prof_superieure"})
df["young"] = df["age"].between(25, 34).astype(int)
df["isco3"] = df["is3maj"].astype(int).astype(str).str.zfill(3)

df["activity_rate"] = np.where(df["pw39"] == CODE_TEMPS_PLEIN, 100, df["pw42"])
df["income_real"] = df["iempyni"] * 100 / df["cpi2020"]
df["income_fte"] = df["income_real"] * 100 / df["activity_rate"]

print(df[["tertiary", "young"]].mean().round(3))      # part de tertiaires et de jeunes
print("Canton manquant (%) :", round(df["canton"].isna().mean() * 100, 1))
print(df["activity_rate"].describe().round(1))

# ## Étape 10 – Retirer les salaires impossibles et les valeurs extrêmes
# **Pourquoi :**
# - Un salaire de 0 ou manquant ne peut pas être prédit (et le log de 0 n'existe pas).
# - Sous 20 % de taux d'activité, le calcul temps plein devient absurde : 5 000 CHF à 5 % donnent 100 000 CHF « temps plein ».
# - On retire le 1 % le plus bas et le 1 % le plus haut, pour limiter l'influence des valeurs extrêmes et des erreurs de déclaration.
# - `log_income` : le log réduit l'effet des très hauts salaires et rend les écarts lisibles en % ; c'est la variable à prédire.

# %%
avant = len(df)
df = df[df["income_fte"] > 0]
df = df[df["activity_rate"] >= 20]
print("Lignes retirées :", avant - len(df), "| restantes :", len(df))

# Retire le 1 % le plus bas et le 1 % le plus haut
bornes = df["income_fte"].quantile([0.01, 0.99])
avant_trim = len(df)
df = df[df["income_fte"].between(bornes[0.01], bornes[0.99])]
print("Bornes gardées (CHF) :", bornes.round(0).tolist(), "| lignes retirées :", avant_trim - len(df))

df["log_income"] = np.log(df["income_fte"])

print(df["income_fte"].quantile([0.01, 0.05, 0.5, 0.95, 0.99]).round(0))

# ## Étape 11 – Vérifier et enregistrer
# **Pourquoi :** contrôler qu'il y a assez de personnes par année, notamment de jeunes tertiaires, avant la fusion OIT. Le fichier commence par `shp_` → il est ignoré par GitHub.
#
# Résultat attendu avec les données complètes : **40 796 lignes**, **10 076 personnes**.

# %%
print("Effectifs par année et groupe :")
print(pd.crosstab(df["year"], [df["tertiary"], df["young"]]))
print("\nLignes :", len(df))
print("Personnes différentes :", df["idpers"].nunique())
print("Part de revenus imputés (%) :", round((df["impempyn"] > 0).mean() * 100, 1))

# Si erreur "pyarrow" : lance une fois  !pip install pyarrow  dans une cellule, puis relance
df.to_parquet(SORTIE, index=False)
print("Enregistré :", SORTIE)
