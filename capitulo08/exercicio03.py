import pandas as pd
from sklearn.feature_selection import SelectKBest, f_classif
arquivo_features = "dados_rotulados_Todas_Features.csv"
saida_principais = "dados_rotulados_Principais_Features.csv"

df = pd.read_csv(arquivo_features)

X_full = df.drop(columns=["segmento_id", "timestamp_inicio", "label"], errors="ignore")
X = X_full.select_dtypes(include=["number"])
y = df["label"]

k = 7
selector = SelectKBest(score_func=f_classif, k=k)
selector.fit(X, y)

scores_df = pd.DataFrame({
    "feature": X.columns,
    "f_score": selector.scores_
}).sort_values(by="f_score", ascending=False)

print(scores_df.head(k).to_string(index=False))

features_selecionadas = scores_df["feature"].head(k).tolist()
print("Features selecionadas:", features_selecionadas)

df_reduzido = df[features_selecionadas + ["label"]]
df_reduzido.to_csv(saida_principais, index=False)
print(df_reduzido.shape)
