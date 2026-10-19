import pandas as pd
from sklearn.model_selection import train_test_split

arquivo_entrada = "dados_rotulados_Principais_Features.csv"
df = pd.read_csv(arquivo_entrada)

X = df.drop(columns=["label"], errors="ignore")
y = df["label"]

X_train, X_val, y_train, y_val = train_test_split(
    X,
    y,
    test_size=0.3,
    random_state=42,
    stratify=y
)

df_treino = X_train.copy()
df_treino["label"] = y_train.values

df_validacao = X_val.copy()
df_validacao["label"] = y_val.values

arquivo_treino = "dados_rotulados_Principais_Features_Treino.csv"
arquivo_validacao = "dados_rotulados_Principais_Features_Validacao.csv"

df_treino.to_csv(arquivo_treino, index=False)
df_validacao.to_csv(arquivo_validacao, index=False)
