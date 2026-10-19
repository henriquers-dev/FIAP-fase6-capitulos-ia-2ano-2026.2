import numpy as np
import matplotlib.pyplot as plt

# df_scores já existe; aqui só pegamos o top 20
df_top20 = df_scores.head(20)

plt.figure(figsize=(14, 7))

# Cria uma lista de cores usando o colormap viridis
cores = plt.cm.viridis(np.linspace(0, 1, len(df_top20)))

plt.barh(
    df_top20["feature"],
    df_top20["f_score"],
    color=cores
)

plt.gca().invert_yaxis()  # deixa a feature mais importante em cima
plt.title("Top 20 Features por F-Score (ANOVA)", fontsize=16)
plt.xlabel("F-Score", fontsize=12)
plt.ylabel("Feature", fontsize=12)
plt.tight_layout()
plt.show()
