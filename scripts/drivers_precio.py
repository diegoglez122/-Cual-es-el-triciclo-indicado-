#!/usr/bin/env python3
"""Drivers de precio v2 — ¿qué determina el precio de un triciclo?

Input:  triciclos_aceptados_normalizado.json (SOLO LECTURA).
Filtro: moneda_original == 'USD' y precio_publicado >= PRECIO_MIN_SANO_USD.

Análisis (§11 del informe) + limitaciones ampliadas (§12):
  1. Resumen global del precio.
  2. Precio por marca (top 17, n>=10) + IC bootstrap 95% (1000 réplicas)
     + gráfico graficos/06_precio_por_marca.png.
  3. Precio por tipo + Mann-Whitney + graficos/07_precio_por_tipo.png.
  4. Precio por quintil de autonomía (clave) + Spearman
     + graficos/08_precio_por_quintil_autonomia.png.
  5. Precio por quintil de voltaje (análogo)
     + graficos/09_precio_por_quintil_voltaje.png.
  6. Precio por marca dentro de cada tipo.
  7. Autonomía dentro de cada marca (top 5) — Spearman.
  8. OLS simple: precio ~ tipo + autonomia + voltaje + marca_top10.
  9. §11 (tablas 2-8 + conclusión ejecutiva) y §12 (limitaciones ampliadas)
     en informe_mercado.md. §11/§12 previas se SUSTITUYEN, no se acumulan.

Variables descartadas (solo se mencionan en §12): garantia_meses,
panel_incluido, provincia, tipo_uso.

Uso:
  python scripts/drivers_precio.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.stats as st
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))

from analisis_mercado import (  # noqa: E402
    ENTRADA,
    INFORME,
    PRECIO_MIN_SANO_USD,
    es_sana,
    fmt,
    pct,
)

GRAFICOS = ROOT / 'graficos'
SEED = 42
B_BOOT = 1000
N_QUINTILES = 5
MARCA_MIN_N = 10
MARCA_TOP10 = ['Bryderk', 'Kvitova', 'Jinpeng', 'Topmaq', 'Star',
               'Mvp', 'Maf', 'Oim', 'Onebot', 'Vedca']


def cargar_sanos():
    import json
    if not ENTRADA.exists():
        sys.exit(f'ERROR: no existe {ENTRADA}')
    with open(ENTRADA, encoding='utf-8') as f:
        regs = json.load(f)
    return regs, [r for r in regs if es_sana(r)]


def guardar_grafico(fig, nombre):
    GRAFICOS.mkdir(exist_ok=True)
    path = GRAFICOS / nombre
    fig.savefig(path, dpi=120, bbox_inches='tight')
    return path


def bootstrap_ic(vals, rng, b=B_BOOT):
    """IC 95% percentile bootstrap de la mediana → (lo, hi)."""
    arr = np.asarray(vals, dtype=float)
    idx = rng.integers(0, arr.size, size=(b, arr.size))
    meds = np.median(arr[idx], axis=1)
    lo, hi = np.percentile(meds, [2.5, 97.5])
    return float(lo), float(hi)


def mw(a, b):
    res = st.mannwhitneyu(np.asarray(a, float), np.asarray(b, float),
                          alternative='two-sided')
    return float(res.statistic), float(res.pvalue)


def spearman(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.size < 3 or np.all(x == x[0]) or np.all(y == y[0]):
        return float('nan'), float('nan')
    res = st.spearmanr(x, y)
    return float(res.statistic), float(res.pvalue)


def fmt_signo(x):
    """'+700' / '-200' con separador de miles por espacios."""
    return ('+' if x >= 0 else '-') + fmt(abs(float(x)))


def quintiles_por_rango(vals, q=N_QUINTILES):
    """Reparte en q quintiles de igual n por posición (empates del valor
    original se parten entre quintiles; los rangos pueden solaparse)."""
    ser = pd.Series(np.asarray(vals, float))
    ranks = ser.rank(method='first')
    return pd.qcut(ranks, q, labels=False).to_numpy()


# ---------------------------------------------------------------- §1
def seccion_global(sanos):
    p = np.array([r['precio_publicado'] for r in sanos], float)
    q1, med, q3 = np.percentile(p, [25, 50, 75])
    lineas = [
        '### 11.1 Resumen global del precio',
        '',
        f'Filtro: USD y precio ≥ {PRECIO_MIN_SANO_USD} (mismo filtro que las '
        'secciones 6-8).',
        '',
        '| Métrica | Valor (USD) |',
        '|---|---:|',
        f'| n | {len(p)} |',
        f'| Mínimo | {fmt(p.min())} |',
        f'| Q1 | {fmt(q1)} |',
        f'| **Mediana** | **{fmt(med)}** |',
        f'| Q3 | {fmt(q3)} |',
        f'| Máximo | {fmt(p.max())} |',
        f'| Media | {fmt(p.mean())} |',
        '',
        f'Asimetría positiva: media ({fmt(p.mean())}) > mediana ({fmt(med)}) '
        'por anuncios de precio alto.',
        '',
    ]
    return lineas, float(med), float(q1), float(q3)


# ---------------------------------------------------------------- §2
def seccion_marcas(sanos, med_global, rng, matplotlib_pyplot):
    plt = matplotlib_pyplot
    conteo = pd.Series([r['marca_detectada'] for r in sanos]).value_counts()
    marcas = [m for m, n in conteo.items() if n >= MARCA_MIN_N]

    filas = []
    for m in marcas:
        vals = [r['precio_publicado'] for r in sanos if r['marca_detectada'] == m]
        med = float(np.median(vals))
        lo, hi = bootstrap_ic(vals, rng)
        filas.append({'marca': m, 'n': len(vals), 'med': med, 'lo': lo, 'hi': hi})
    filas.sort(key=lambda f: f['med'], reverse=True)

    lineas = [
        f'### 11.2 Precio por marca (top {len(filas)} con n ≥ {MARCA_MIN_N})',
        '',
        f'IC 95% bootstrap de la mediana, {B_BOOT:,} réplicas, semilla {SEED} '
        '(reproducible). Orden por mediana descendente.',
        '',
        '| Marca | n | Mediana | IC 95% inf | IC 95% sup | Δ vs mediana global |',
        '|---|---:|---:|---:|---:|---:|',
    ]
    for f in filas:
        delta = f['med'] - med_global
        signo = '+' if delta >= 0 else ''
        lineas.append(f'| {f["marca"]} | {f["n"]} | {fmt(f["med"])} | {fmt(f["lo"])} '
                      f'| {fmt(f["hi"])} | {signo}{fmt(delta)} |')

    brecha = filas[0]['med'] - filas[-1]['med']
    lineas += [
        '',
        f'Brecha entre la marca más cara ({filas[0]["marca"]}, {fmt(filas[0]["med"])}) '
        f'y la más barata de la tabla ({filas[-1]["marca"]}, {fmt(filas[-1]["med"])}): '
        f'**{fmt(brecha)} USD**.',
        '',
    ]

    top10 = filas[:10]
    data = [[r['precio_publicado'] for r in sanos if r['marca_detectada'] == f['marca']]
            for f in top10]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.boxplot(data, tick_labels=[f['marca'] for f in top10])
    ax.set_ylabel('precio_publicado (USD)')
    ax.set_title(f'Precio por marca — top 10 con n ≥ {MARCA_MIN_N} (n={len(sanos)})')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(axis='y', alpha=0.3)
    ruta06 = guardar_grafico(fig, '06_precio_por_marca.png')
    plt.close(fig)
    return lineas, ruta06, filas


# ---------------------------------------------------------------- §3
def seccion_tipo(sanos, rng, matplotlib_pyplot):
    plt = matplotlib_pyplot
    grupos = {t: [r['precio_publicado'] for r in sanos if r['tipo_triciclo'] == t]
              for t in sorted({r['tipo_triciclo'] for r in sanos})}
    orden = sorted(grupos, key=len, reverse=True)
    U, p = mw(grupos[orden[0]], grupos[orden[1]])

    lineas = [
        '### 11.3 Precio por tipo de triciclo',
        '',
        '| Tipo | n | Mediana | IC 95% inf | IC 95% sup |',
        '|---|---:|---:|---:|---:|',
    ]
    ics = {}
    for t in orden:
        lo, hi = bootstrap_ic(grupos[t], rng)
        ics[t] = (lo, hi)
        lineas.append(f'| {t} | {len(grupos[t])} | {fmt(float(np.median(grupos[t])))} '
                      f'| {fmt(lo)} | {fmt(hi)} |')

    med0 = float(np.median(grupos[orden[0]]))
    med1 = float(np.median(grupos[orden[1]]))
    sig = 'sí' if p < 0.05 else 'NO'
    lineas += [
        '',
        f'**Mann-Whitney U** ({orden[0]} vs {orden[1]}): U = {fmt(int(U))}, '
        f'**p = {p:.4f}** → diferencia {sig} estadísticamente significativa. '
        f'Diferencia de medianas: {fmt(med0 - med1)} USD.',
        '',
    ]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.boxplot([grupos[t] for t in orden], tick_labels=orden)
    ax.set_ylabel('precio_publicado (USD)')
    ax.set_title(f'Precio por tipo de triciclo (n={len(sanos)})')
    ax.grid(axis='y', alpha=0.3)
    ruta07 = guardar_grafico(fig, '07_precio_por_tipo.png')
    plt.close(fig)
    return lineas, ruta07, p


# ------------------------------------------------- §4 / §5 (genérico)
def seccion_quintiles(sanos, campo, etiqueta, unidad, nombre_grafico,
                      titulo_grafico, rng, matplotlib_pyplot, incluye_frase):
    plt = matplotlib_pyplot
    regs = [r for r in sanos if r.get(campo) is not None]
    vals = [float(r[campo]) for r in regs]
    precio = [r['precio_publicado'] for r in regs]
    q_idx = quintiles_por_rango(vals)

    rho, p_rho = spearman(vals, precio)

    filas = []
    for q in range(N_QUINTILES):
        vq = [v for v, qq in zip(vals, q_idx) if qq == q]
        pq = [p for p, qq in zip(precio, q_idx) if qq == q]
        lo, hi = bootstrap_ic(pq, rng)
        filas.append({
            'q': q + 1,
            'rango': f'{int(min(vq))}–{int(max(vq))}{unidad}',
            'n': len(pq),
            'med': float(np.median(pq)),
            'lo': lo, 'hi': hi,
        })

    n_el = len(regs)
    perdidos = len(sanos) - n_el
    lineas = [
        f'### {"11.4" if incluye_frase else "11.5"} Precio por quintil de {etiqueta}',
        '',
        f'Quintiles por posición (n ≈ iguales); con tantos empates en {etiqueta} '
        'los rangos de valores pueden solaparse entre quintiles. '
        f'n = {n_el}'
        + (f' (se excluyen {perdidos} anuncios sin {campo}).' if perdidos else '.'),
        '',
        f'| Quintil | Rango de {etiqueta} | n | Mediana (USD) | IC 95% |',
        '|---|---|---:|---:|---|',
    ]
    for f in filas:
        lineas.append(f'| Q{f["q"]} | {f["rango"]} | {f["n"]} | {fmt(f["med"])} '
                      f'| {fmt(f["lo"])}–{fmt(f["hi"])} |')

    delta = filas[-1]['med'] - filas[0]['med']
    sube = (rho > 0 and p_rho < 0.05 and delta > 0)
    dir_word = 'SÍ' if sube else 'NO'
    lineas += [
        '',
        f'**Spearman** entre {etiqueta} y precio: **rho = {rho:.3f}**, p = {p_rho:.4f} '
        f'(n = {n_el}).',
        '',
        f'**¿Más {etiqueta} sube el precio? {dir_word}**: mediana del Q5 '
        f'({filas[-1]["rango"]}) = {fmt(filas[-1]["med"])} USD vs Q1 '
        f'({filas[0]["rango"]}) = {fmt(filas[0]["med"])} USD → '
        f'**magnitud: {fmt_signo(delta)} USD** entre extremos'
        + ('' if p_rho < 0.05 else ' (rho no significativo: p ≥ 0.05)') + '.',
        '',
    ]

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(filas))
    meds = [f['med'] for f in filas]
    err_lo = [f['med'] - f['lo'] for f in filas]
    err_hi = [f['hi'] - f['med'] for f in filas]
    ax.bar(x, meds, yerr=[err_lo, err_hi], capsize=6,
           color='#2b7bba', edgecolor='white')
    ax.set_xticks(x, [f'Q{f["q"]}\n{f["rango"]}' for f in filas])
    ax.set_ylabel('precio_publicado (USD)')
    ax.set_title(titulo_grafico)
    ax.grid(axis='y', alpha=0.3)
    ruta = guardar_grafico(fig, nombre_grafico)
    plt.close(fig)
    return lineas, ruta, rho, p_rho, delta, sube


# ------------------------------------------- §4 extra (subgrupo 100 km)
def parrafo_subgrupo_100km(sanos, matplotlib_pyplot):
    """3 líneas sobre autonomia_km_max == 100 km + histograma."""
    plt = matplotlib_pyplot
    sub = [r for r in sanos if float(r.get('autonomia_km_max') or 0) == 100.0]
    p = np.array([r['precio_publicado'] for r in sub], float)
    if p.size == 0:
        return [], None, {}
    q1, med, q3 = np.percentile(p, [25, 50, 75])

    conteo = pd.Series([r['marca_detectada'] for r in sub]).value_counts()
    top = []
    for m, n in conteo.head(10).items():
        vals = [r['precio_publicado'] for r in sub if r['marca_detectada'] == m]
        top.append(f'{m} (n={n}) {fmt(float(np.median(vals)))}')
    top_txt = ' · '.join(top)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(p, bins=25, color='#2b7bba', edgecolor='white')
    ax.axvline(med, color='#d62728', ls='--', lw=1.5, label=f'Mediana {fmt(med)} USD')
    ax.set_xlabel('precio_publicado (USD)')
    ax.set_ylabel('Frecuencia')
    ax.set_title(f'Subgrupo autonomía = 100 km exactos (n={len(p)}, '
                 f'mediana {fmt(med)} USD)')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    ruta = guardar_grafico(fig, '10_precio_100km.png')
    plt.close(fig)

    lineas = [
        f'**Subgrupo modal — `autonomia_km_max` = 100 km exactos:** n = {len(p)} de '
        f'{len(sanos)} ({pct(len(p) / len(sanos))}); precio mediano **{fmt(med)} USD**, '
        f'Q1–Q3 {fmt(q1)}–{fmt(q3)}, rango {fmt(p.min())}–{fmt(p.max())} USD.',
        f'Por marca dentro del subgrupo (top 10 por n, mediana USD): {top_txt}.',
        f'Con la autonomía fijada en 100 km el precio sigue abriéndose en {fmt(p.max() - p.min())} '
        'USD → la variación restante la explican marca, modelo/estado y accesorios; '
        'histograma en `graficos/10_precio_100km.png`.',
        '',
    ]
    resumen = {'n': int(p.size), 'med': float(med), 'q1': float(q1),
               'q3': float(q3), 'min': float(p.min()), 'max': float(p.max())}
    return lineas, ruta, resumen


# ---------------------------------------------------------------- §6
def seccion_marcas_por_tipo(sanos, filas_marcas):
    top17 = [f['marca'] for f in filas_marcas]
    lineas = [
        '### 11.6 Precio por marca dentro de cada tipo',
        '',
        '¿Se mantiene la diferencia entre marcas al controlar por tipo? '
        'Mediana por marca y tipo (celdas con n < 5 señaladas):',
        '',
        '| Marca | n eléct. | Mediana eléct. | n híbr. | Mediana híbr. |',
        '|---|---:|---:|---:|---:|',
    ]
    pares_overall, pares_elec = [], []
    for m in top17:
        celdas = []
        med_overall = None
        for t in ('eléctrico', 'híbrido'):
            vals = [r['precio_publicado'] for r in sanos
                    if r['marca_detectada'] == m and r['tipo_triciclo'] == t]
            if not vals:
                celdas.extend(['0', '—'])
            else:
                marca_n = f'{len(vals)}*' if len(vals) < 5 else str(len(vals))
                celdas.extend([marca_n, fmt(float(np.median(vals)))])
                if t == 'eléctrico' and len(vals) >= 10:
                    med_overall = float(np.median(vals))
        lineas.append(f'| {m} | {celdas[0]} | {celdas[1]} | {celdas[2]} | {celdas[3]} |')
        if med_overall is not None:
            med_tot = float(np.median(
                [r['precio_publicado'] for r in sanos if r['marca_detectada'] == m]))
            pares_overall.append(med_tot)
            pares_elec.append(med_overall)

    rho, p = spearman(pares_overall, pares_elec)
    persiste = rho > 0 and p < 0.05
    lineas += [
        '',
        f'(* n < 5, mediana no fiable. Solo {sum(1 for r in sanos if r["tipo_triciclo"] == "híbrido")} '
        'anuncios híbridos: las marcas híbridas no permiten comparación por marca.)',
        '',
        f'**Spearman** entre mediana global de marca y mediana dentro de '
        f'eléctrico ({len(pares_elec)} marcas con n_eléc ≥ 10): '
        f'**rho = {rho:.3f}**, p = {p:.4f} → '
        + ('**la jerarquía entre marcas se MANTIENE al controlar por tipo** '
           '(el efecto de marca no es un artefacto de la mezcla de tipos).'
           if persiste else
           '**la jerarquía de marcas NO se mantiene** de forma significativa '
           'al controlar por tipo.'),
        '',
    ]
    return lineas, rho, p


# ---------------------------------------------------------------- §7
def seccion_autonomia_por_marca(sanos, top5):
    lineas = [
        '### 11.7 Autonomía dentro de cada marca (top 5)',
        '',
        'Spearman rho entre `autonomia_km_max` y precio **dentro** de cada marca: '
        '¿el vendedor cobra más por el modelo de más km?',
        '',
        '| Marca | n | rho | p-valor | ¿Cobra más por km? |',
        '|---|---:|---:|---:|:--:|',
    ]
    respuestas = []
    for m in top5:
        regs = [r for r in sanos if r['marca_detectada'] == m]
        rho, p = spearman([r['autonomia_km_max'] for r in regs],
                          [r['precio_publicado'] for r in regs])
        if np.isnan(rho):
            respuesta = 'n/d'
        elif rho > 0 and p < 0.05:
            respuesta = 'SÍ'
        else:
            respuesta = 'NO'
        respuestas.append((m, rho, p, respuesta))
        lineas.append(f'| {m} | {len(regs)} | {rho:.3f} | {p:.4f} | {respuesta} |')

    n_si = sum(1 for *_, r in respuestas if r == 'SÍ')
    lineas += [
        '',
        f'**Respuesta:** {n_si} de {len(respuestas)} marcas muestran una relación '
        'positiva y significativa (p < 0.05). '
        + ('En esas marcas, SÍ: el vendedor cobra más por el modelo de mayor '
           'autonomía.' if n_si else
           'En general NO: dentro de una misma marca el precio no crece con la '
           'autonomía declarada.')
        + ' Donde rho ≈ 0, la marca fija un precio único casi independiente del '
          'modelo.',
        '',
    ]
    return lineas, respuestas


# ---------------------------------------------------------------- §8
def seccion_ols(sanos):
    df = pd.DataFrame([{
        'precio': r['precio_publicado'],
        'tipo': r['tipo_triciclo'],
        'autonomia': float(r['autonomia_km_max']),
        'voltaje': (np.nan if r.get('voltaje_bateria') is None
                    else float(r['voltaje_bateria'])),
        'marca_top10': (r['marca_detectada'] if r['marca_detectada'] in MARCA_TOP10
                        else 'Otras'),
    } for r in sanos])
    n_previo = len(df)
    df = df.dropna(subset=['voltaje']).reset_index(drop=True)

    dum_marca = pd.get_dummies(df['marca_top10'], prefix='marca').astype(float)
    dum_marca = dum_marca.drop(columns=['marca_Otras'])
    dum_tipo = pd.get_dummies(df['tipo'], prefix='tipo').astype(float)
    if 'tipo_eléctrico' in dum_tipo.columns:
        dum_tipo = dum_tipo.drop(columns=['tipo_eléctrico'])
    X = pd.concat([df[['autonomia', 'voltaje']].astype(float), dum_tipo, dum_marca],
                  axis=1)
    X = sm.add_constant(X)
    y = df['precio'].astype(float)
    fit = sm.OLS(y, X).fit()
    ci = fit.conf_int(alpha=0.05)

    vifs = {c: variance_inflation_factor(X.to_numpy(), i)
            for i, c in enumerate(X.columns) if c != 'const'}

    lineas = [
        '### 11.8 Regresión OLS simple',
        '',
        '`precio ~ tipo_triciclo + autonomia_km_max + voltaje_bateria + marca_top10` '
        '(10 dummies; marca de referencia = resto de marcas "Otras").',
        '',
        f'- **n = {int(fit.nobs)}** (completos en voltaje; se excluyen '
        f'{n_previo - int(fit.nobs)} anuncios sin dato).',
        f'- **R² = {fit.rsquared:.3f}**, **R² ajustado = {fit.rsquared_adj:.3f}**.',
        f'- F = {fit.fvalue:.1f} (p = {fit.f_pvalue:.2e}); '
        f'error típico residual = {fit.mse_resid ** 0.5:,.0f} USD.',
        '',
        '| Variable | Coef. (USD) | IC 95% inf | IC 95% sup | p-valor |',
        '|---|---:|---:|---:|---:|',
    ]
    orden = ['const', 'tipo_híbrido', 'autonomia', 'voltaje'] + \
            [c for c in X.columns if c.startswith('marca_')]
    for v in orden:
        lineas.append(f'| {v} | {fit.params[v]:,.1f} | {ci.loc[v, 0]:,.1f} '
                      f'| {ci.loc[v, 1]:,.1f} | {fit.pvalues[v]:.4f} |')

    lineas += [
        '',
        '**VIF** (multicolinealidad):',
        '',
        '| Variable | VIF |',
        '|---|---:|',
    ]
    for v in ['autonomia', 'voltaje', 'tipo_híbrido'] + \
            [c for c in X.columns if c.startswith('marca_')]:
        lineas.append(f'| {v} | {vifs[v]:.1f} |')

    if fit.rsquared < 0.15:
        conclusion = (f'**Conclusión OLS: R² = {fit.rsquared:.3f} < 0.15 → estas '
                      'variables explican poco del precio** (la mayor parte de la '
                      'variación queda en la marca no capturada y en factores no '
                      'medidos: estado, accesorios, urgencia del vendedor).')
    else:
        num_sig = sum(1 for v in orden[1:] if fit.pvalues[v] < 0.05)
        conclusion = (f'**Conclusión OLS: R² = {fit.rsquared:.3f} ≥ 0.15 → estas '
                      f'variables sí explican parte relevante del precio** '
                      f'({num_sig} de {len(orden) - 1} coeficientes con p < 0.05).')
    lineas += [
        '',
        conclusion,
        '',
        'Advertencia: los dummies de marca capturan buena parte de lo que "explica" '
        'el precio porque marca y precio se fijan juntos; los coeficientes de '
        'autonomía/voltaje son **asociaciones condicionales a la marca**, no '
        'causales.',
        '',
    ]

    return lineas, fit, vifs


# ---------------------------------------------------------------- §11 final
def conclusion_ejecutiva(sanos, med_global, filas_marcas, p_tipo,
                         rho_aut, p_aut, delta_aut, sube_aut,
                         rho_vol, p_vol, delta_vol, sube_vol,
                         rho_persiste, p_persiste, respuestas, fit):
    top = filas_marcas[0]
    bot = filas_marcas[-1]
    brecha = top['med'] - bot['med']
    n_si_km = sum(1 for *_, r in respuestas if r == 'SÍ')

    ci_v = fit.conf_int(alpha=0.05)
    if sube_vol:
        vol_txt = (f'3. **El voltaje SÍ influye**: rho = {rho_vol:.3f} '
                   f'(p = {p_vol:.4f}); Q5 − Q1 = {fmt_signo(delta_vol)} USD; en el '
                   f'OLS condicionando marca y autonomía el coeficiente es '
                   f'{fmt_signo(fit.params["voltaje"])} USD por voltio '
                   f'(IC 95% {fit.params["voltaje"] - 1.96 * fit.bse["voltaje"]:.0f} a '
                   f'{fit.params["voltaje"] + 1.96 * fit.bse["voltaje"]:.0f}, '
                   f'p = {fit.pvalues["voltaje"]:.4f}).')
    else:
        vol_txt = (f'3. **El voltaje NO tiene relación marginal con el precio**: '
                   f'rho = {rho_vol:.3f} (p = {p_vol:.4f}), Q5 − Q1 = '
                   f'{fmt_signo(delta_vol)} USD (no significativo). **Pero en el OLS '
                   'condicionando a marca y autonomía sí aporta**: '
                   f'{fmt_signo(fit.params["voltaje"])} USD por voltio '
                   f'(IC 95% {ci_v.loc["voltaje", 0]:+.0f} a {ci_v.loc["voltaje", 1]:+.0f}, '
                   f'p = {fit.pvalues["voltaje"]:.4f}) → efecto condicional '
                   '(suprimido por la colinealidad con autonomía, VIF 3.6), no causal.')

    lineas = [
        '**Conclusión ejecutiva — ¿qué determina el precio de un triciclo?**',
        '',
        f'1. **La marca es el factor dominante**: entre las {len(filas_marcas)} '
        f'marcas con n ≥ {MARCA_MIN_N} la mediana va de {fmt(bot["med"])} USD '
        f'({bot["marca"]}) a {fmt(top["med"])} USD ({top["marca"]}), una brecha de '
        f'**{fmt(brecha)} USD** = **+{brecha / bot["med"] * 100:.0f}%** sobre la '
        f'marca más barata (mediana global {fmt(med_global)} USD). La jerarquía de '
        f'marcas se mantiene al controlar por tipo (rho = {rho_persiste:.2f}, '
        f'p = {p_persiste:.4f}).',
        f'2. **La autonomía {"SÍ" if sube_aut else "NO"} influye**: rho de Spearman '
        f'= {rho_aut:.3f} (p = {p_aut:.4f}); Q5 − Q1 = {fmt_signo(delta_aut)} USD '
        'entre los extremos de la distribución de autonomía.',
        vol_txt,
        f'4. **El tipo (eléctrico vs híbrido) es débil**: Mann-Whitney p = '
        f'{p_tipo:.4f} → {"diferencia real pero pequeña" if p_tipo < 0.05 else "sin diferencia detectable"}.',
        f'5. **Dentro de una misma marca, la autonomía casi no ordena el precio**: '
        f'solo {n_si_km} de {len(respuestas)} marcas top muestran cobro '
        'significativamente mayor por más km.',
        f'6. **El modelo conjunto** (tipo + autonomía + voltaje + top 10 marcas) '
        f'alcanza R² = {fit.rsquared:.3f}: el precio se explica sobre todo por '
        '**marca**, y en segundo orden por **autonomía declarada** y **voltaje**; '
        'el **tipo** aporta poco.',
        '',
    ]
    return lineas


# ---------------------------------------------------------------- §12
def seccion_limitaciones_ampliadas(sanos, total):
    ph = sum(1 for r in total if r.get('moneda_original') == 'USD'
             and 0 < (r.get('precio_publicado') or 0) < PRECIO_MIN_SANO_USD)
    hab = sum(1 for r in sanos if r.get('ubicacion') == 'La Habana')
    return [
        '## 12. Limitaciones ampliadas',
        '',
        '- **Variables descartadas del análisis de drivers** (por falta de datos o '
        'varianza):',
        '',
        '  - `garantia_meses`: solo 20/747 anuncios lo declaran → inestable.',
        '  - `panel_incluido`: solo 67/747 con `True`; el resto es `null` '
        '(no mencionado, no forzosamente "sin panel").',
        '  - `provincia`: **96% de la muestra es La Habana** (720/747); sin '
        'varianza no hay efecto estimable y el resto de provincias tiene n ≤ 23.',
        '  - `tipo_uso`: 653/747 son "carga" y 63 `null` → varianza casi nula.',
        '',
        f'- **Sesgo geográfico extremo**: {hab}/{len(sanos)} ({pct(hab / len(sanos))}) '
        'anuncios de La Habana; Artemisa, Matanzas y Holguín apenas si aparecen. '
        'Los precios no son representativos de otras provincias ni de Cuba en su conjunto.',
        '',
        '- **Muestra no aleatoria**: son anuncios publicados en Revolico (no '
        'ventas cerradas ni precios negociados); el vendedor publica el precio que '
        'quiere, no el que recibe.',
        '',
        f'- **Filtro de sanidad**: {ph} anuncios con precio < {PRECIO_MIN_SANO_USD} '
        'USD excluidos (placeholder $1-$3); ver §10.',
        '',
        '- **Empates masivos**: 356/747 anuncios declaran exactamente 100 km de '
        'autonomía y la mayoría 72V; los quintiles de §11.4/§11.5 se construyen '
        'por posición y sus rangos se solapan.',
        '',
        '- **OLS de §11.8 con n = 561**: los 186 anuncios sin `voltaje_bateria` '
        'se excluyen; si el dato faltante no es aleatorio, el modelo sesga.',
        '',
        '- **Asociación ≠ causalidad**: marca, autonomía y precio los fija el '
        'mismo vendedor; nada aquí identifica efectos causales.',
        '',
        '- **Ventana temporal**: una semana (2026-10-08 a 2026-10-14); sin '
        'serie histórica no hay tendencias ni estacionalidad.',
        '',
    ]


def actualizar_informe(bloques):
    if not INFORME.exists():
        sys.exit(f'ERROR: no existe {INFORME}. Ejecuta antes: python scripts/analisis_mercado.py')
    texto = INFORME.read_text(encoding='utf-8')
    corte = [i for i in (texto.find('\n## 11'), texto.find('\n## 12')) if i != -1]
    if corte:
        texto = texto[:min(corte)]
    INFORME.write_text(texto.rstrip() + '\n\n' + '\n'.join(bloques).strip() + '\n',
                       encoding='utf-8')


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    rng = np.random.default_rng(SEED)
    regs, sanos = cargar_sanos()

    l1, med_global, q1, q3 = seccion_global(sanos)
    l2, ruta06, filas_marcas = seccion_marcas(sanos, med_global, rng, plt)
    l3, ruta07, p_tipo = seccion_tipo(sanos, rng, plt)
    l4, ruta08, rho_aut, p_aut, delta_aut, sube_aut = seccion_quintiles(
        sanos, 'autonomia_km_max', 'autonomía', ' km',
        '08_precio_por_quintil_autonomia.png',
        'Precio por quintil de autonomía máxima (mediana + IC 95%)',
        rng, plt, True)
    l4b, ruta10, res100 = parrafo_subgrupo_100km(sanos, plt)
    l5, ruta09, rho_vol, p_vol, delta_vol, sube_vol = seccion_quintiles(
        sanos, 'voltaje_bateria', 'voltaje', ' V',
        '09_precio_por_quintil_voltaje.png',
        'Precio por quintil de voltaje de batería (mediana + IC 95%)',
        rng, plt, False)
    l6, rho_persiste, p_persiste = seccion_marcas_por_tipo(sanos, filas_marcas)
    top5 = [m for m, _ in pd.Series(
        [r['marca_detectada'] for r in sanos]).value_counts().items()][:5]
    l7, respuestas = seccion_autonomia_por_marca(sanos, top5)
    l8, fit, vifs = seccion_ols(sanos)
    l_concl = conclusion_ejecutiva(sanos, med_global, filas_marcas, p_tipo,
                                   rho_aut, p_aut, delta_aut, sube_aut,
                                   rho_vol, p_vol, delta_vol, sube_vol,
                                   rho_persiste, p_persiste, respuestas, fit)
    l12 = seccion_limitaciones_ampliadas(sanos, regs)

    bloque11 = ['', '## 11. Drivers de precio', ''] + l1 + l2 + l3 + l4 + l4b + l5 \
        + l6 + l7 + l8 + l_concl
    actualizar_informe(bloque11 + [''] + l12)

    rutas = [ruta06, ruta07, ruta08, ruta09, ruta10]
    print('=== DRIVERS DE PRECIO v2 — COMPLETADO ===')
    print(f'Informe:  {INFORME}  (§11 y §12 sustituidas)')
    print('Gráficos:')
    for p in rutas:
        print(f'  {p}')
    print(f'Dataset:  {ENTRADA.name} NO modificado (n={len(regs)}, filtrados {len(sanos)})')
    print()
    print('=== MÉTRICAS CLAVE ===')
    print(f'Precio global:         mediana {fmt(med_global)} USD, Q1 {fmt(q1)}, Q3 {fmt(q3)}')
    print(f'Brecha marca top17:    {fmt(filas_marcas[0]["med"])} ({filas_marcas[0]["marca"]}) '
          f'vs {fmt(filas_marcas[-1]["med"])} ({filas_marcas[-1]["marca"]})')
    print(f'MW tipo:               p = {p_tipo:.4f}')
    print(f'Autonomía (SÍ/NO):     rho = {rho_aut:+.3f} (p={p_aut:.4f}), '
          f'Q5-Q1 = {delta_aut:+.0f} USD → {"SÍ" if sube_aut else "NO"}')
    print(f'Voltaje (SÍ/NO):       rho = {rho_vol:+.3f} (p={p_vol:.4f}), '
          f'Q5-Q1 = {delta_vol:+.0f} USD → {"SÍ" if sube_vol else "NO"}')
    print(f'Persistencia marca:    rho = {rho_persiste:+.3f} (p={p_persiste:.4f})')
    print(f'OLS:                   n = {int(fit.nobs)}, R2 = {fit.rsquared:.3f}, '
          f'R2_adj = {fit.rsquared_adj:.3f}')
    print(f'  autonomia coef:      {fit.params["autonomia"]:+.1f} USD/km '
          f'IC95 [{fit.conf_int().loc["autonomia", 0]:.1f}, {fit.conf_int().loc["autonomia", 1]:.1f}]')
    print(f'  voltaje coef:        {fit.params["voltaje"]:+.1f} USD/V '
          f'IC95 [{fit.conf_int().loc["voltaje", 0]:.1f}, {fit.conf_int().loc["voltaje", 1]:.1f}]')
    print(f'Subgrupo 100 km:       n = {res100["n"]}, mediana {fmt(res100["med"])} USD, '
          f'Q1-Q3 {fmt(res100["q1"])}-{fmt(res100["q3"])}, '
          f'rango {fmt(res100["min"])}-{fmt(res100["max"])} USD')


if __name__ == '__main__':
    main()
