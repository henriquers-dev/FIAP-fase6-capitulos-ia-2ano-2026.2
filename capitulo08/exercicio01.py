import pandas as pd
import numpy as np
from scipy.stats import skew, kurtosis
from scipy.fft import fft

arquivo_entrada = "dados_rotulados.csv"
arquivo_saida   = "dados_rotulados_Todas_Features.csv"

WINDOW = 20
N_FFT  = 5
EIXOS  = ["ax", "ay", "az"]

df = pd.read_csv(arquivo_entrada).reset_index(drop=True)

def extrair_features_bloco(bloco, segmento_id):
    feats = {
        "segmento_id": segmento_id,
        "timestamp_inicio": bloco["timestamp"].iloc[0],
        "label": bloco["label"].iloc[0]
    }
    for eixo in EIXOS:
        serie = bloco[eixo].values
        pref = eixo
        feats[f"{pref}_mean"]     = np.mean(serie)
        feats[f"{pref}_std"]      = np.std(serie)
        feats[f"{pref}_min"]      = np.min(serie)
        feats[f"{pref}_max"]      = np.max(serie)
        feats[f"{pref}_ptp"]      = np.ptp(serie)
        feats[f"{pref}_energy"]   = np.sum(serie ** 2)
        feats[f"{pref}_rms"]      = np.sqrt(np.mean(serie ** 2))
        feats[f"{pref}_skew"]     = skew(serie)
        feats[f"{pref}_kurtosis"] = kurtosis(serie)
        feats[f"{pref}_zero_crossings"] = ((serie[:-1] * serie[1:]) < 0).sum()
        fft_vals = np.abs(fft(serie))[1:N_FFT + 1]
        for i, val in enumerate(fft_vals, start=1):
            feats[f"{pref}_fft_{i}"] = val
    return feats

lista_features = []
n_segmentos = len(df) // WINDOW

for seg in range(n_segmentos):
    ini = seg * WINDOW
    fim = ini + WINDOW
    bloco = df.iloc[ini:fim]
    if bloco["label"].nunique() != 1:
        continue
    lista_features.append(extrair_features_bloco(bloco, seg + 1))

df_features = pd.DataFrame(lista_features)
df_features.to_csv(arquivo_saida, index=False)
print(df_features.shape)
