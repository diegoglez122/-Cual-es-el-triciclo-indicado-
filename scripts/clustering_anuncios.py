#!/usr/bin/env python3
"""Clustering de los 757 anuncios de Revolico (validación metodológica).
NO usa 'marca_detectada' como feature: es la hipótesis a testear.
Output: data/processed/clustering_anuncios/{.md,.png}
"""
import json
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    from sklearn.preprocessing import RobustScaler
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
except ImportError:
    print("ERROR: falta scikit-learn. Instalar: pip install scikit-learn")
    raise SystemExit(1)

from scipy.cluster.hierarchy import dendrogram, linkage

ROOT = Path(__file__).resolve().parent.parent
JSON = ROOT / "data" / "processed" / "triciclos_aceptados_normalizado.json"
OUT = ROOT / "data" / "processed" / "clustering_anuncios"
OUT.mkdir(parents=True, exist_ok=True)

d = json.loads(JSON.read_text(encoding="utf-8"))
print(f"Total entradas: {len(d)}")

usd = [x for x in d if x.get("moneda_original") == "USD"]
print(f"En USD: {len(usd)}")

X_raw, meta = [], []
dropped = {"no_usd": len(d) - len(usd), "sin_precio": 0, "sin_km": 0, "sin_voltaje": 0, "sin_tipo": 0}
for x in usd:
    precio = x.get("precio_publicado")
    km = x.get("autonomia_km")
    volt = x.get("voltaje_bateria")
    tipo = (x.get("tipo_triciclo") or "").lower().strip()
    if precio is None: dropped["sin_precio"] += 1; continue
    if km is None: dropped["sin_km"] += 1; continue
    if volt is None: dropped["sin_voltaje"] += 1; continue
    if not tipo: dropped["sin_tipo"] += 1; continue
    if "eléctric" in tipo or "electric" in tipo: es_elec = 1
    elif "híbrid" in tipo or "hibrid" in tipo: es_elec = 0
    else: dropped["sin_tipo"] += 1; continue
    X_raw.append([float(precio), float(km), float(volt), float(es_elec)])
    meta.append({"precio": float(precio), "km": float(km), "voltaje": float(volt),
                 "es_electrico": es_elec, "marca": x.get("marca_detectada"),
                 "tipo_uso": x.get("tipo_uso")})

print(f"Descartados: {dropped}")
X = np.array(X_raw)
print(f"Completos para clustering: {len(X)}")

if len(X) < 20:
    print("ERROR: muy pocos datos completos para clustering.")
    raise SystemExit(1)

scaler = RobustScaler()
Xs = scaler.fit_transform(X)

print("\nk  silhouette")
sils = []
for k in range(2, 9):
    labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(Xs)
    if len(set(labels)) < 2: continue
    s = silhouette_score(Xs, labels)
    sils.append((k, s))
    print(f"{k}  {s:.4f}")

best_k, best_sil = max(sils, key=lambda t: t[1])
print(f"\nMejor k={best_k}, silhouette={best_sil:.4f}")

labels_final = KMeans(n_clusters=best_k, n_init=10, random_state=42).fit_predict(Xs)
Z = linkage(Xs, method="ward")

fig, ax = plt.subplots(1, 2, figsize=(14, 5))
ks = [k for k, _ in sils]; ss = [s for _, s in sils]
ax[0].plot(ks, ss, marker="o")
ax[0].axhline(0.25, color="red", ls="--", label="0.25")
ax[0].set_xlabel("k"); ax[0].set_ylabel("silhouette")
ax[0].set_title("Silhouette vs k (KMeans)"); ax[0].legend()
dendrogram(Z, ax=ax[1], truncate_mode="lastp", p=20, show_leaf_counts=True)
ax[1].set_title("Dendrograma (Ward)")
plt.tight_layout(); plt.savefig(OUT / "clustering_anuncios.png", dpi=150); plt.close()

print(f"\nPerfil de {best_k} clusters:")
perfiles = []
for c in range(best_k):
    idxs = [i for i, l in enumerate(labels_final) if l == c]
    sub = [meta[i] for i in idxs]
    precios = [m["precio"] for m in sub]
    kms = [m["km"] for m in sub]
    volts = [m["voltaje"] for m in sub]
    elecs = [m["es_electrico"] for m in sub]
    marcas = {}
    for m in sub:
        marcas[m["marca"]] = marcas.get(m["marca"], 0) + 1
    top = max(marcas.items(), key=lambda t: t[1]) if marcas else ("?", 0)
    p = {"cluster": c, "n": len(idxs), "precio_med": float(np.median(precios)),
         "km_med": float(np.median(kms)), "volt_med": float(np.median(volts)),
         "%electrico": float(100*np.mean(elecs)),
         "marca_top": top[0], "marca_top_n": top[1]}
    perfiles.append(p)
    print(f"  C{c}: n={p['n']}, precio={p['precio_med']:.0f}, km={p['km_med']:.0f}, "
          f"volt={p['volt_med']:.0f}, %elec={p['%electrico']:.0f}%, top={p['marca_top']}")

lines = ["# Clustering de anuncios Revolico (757)\n",
         f"- Total entradas: {len(d)}",
         f"- En USD: {len(usd)}",
         f"- Completos: {len(X)}",
         f"- Descartados: {dropped}\n",
         "## Silhouette vs k\n",
         "| k | silhouette |", "|---|---|"]
for k, s in sils:
    lines.append(f"| {k} | {s:.4f} |")
lines.append(f"\n**Mejor k = {best_k}, silhouette = {best_sil:.4f}**\n")
if best_sil < 0.2:
    lines.append("**Conclusión:** silhouette < 0.2 → **sin estructura latente**. Confirma el informe (§1: la marca domina).")
elif best_sil < 0.25:
    lines.append("**Conclusión:** silhouette < 0.25 → estructura débil. Confirma el informe con matices.")
elif best_sil < 0.4:
    lines.append("**Conclusión:** silhouette moderado → estructura parcial. Revisar perfiles.")
else:
    lines.append("**Conclusión:** silhouette > 0.4 → **hay estructura latente**. Investigar antes de seguir.")
lines.append("\n## Perfil de clusters\n")
lines.append("| cluster | n | precio_med | km_med | volt_med | %elec | marca_top |")
lines.append("|---|---|---|---|---|---|---|")
for p in perfiles:
    lines.append(f"| {p['cluster']} | {p['n']} | {p['precio_med']:.0f} | {p['km_med']:.0f} | {p['volt_med']:.0f} | {p['%electrico']:.0f}% | {p['marca_top']} ({p['marca_top_n']}) |")

(OUT / "clustering_anuncios.md").write_text("\n".join(lines), encoding="utf-8")
print(f"\nOutputs: {OUT}/clustering_anuncios.md y clustering_anuncios.png")
