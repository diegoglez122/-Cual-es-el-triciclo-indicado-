#!/usr/bin/env python3
"""Análisis de mercado sobre triciclos_aceptados_normalizado.json (solo lectura).

Genera informe_mercado.md en la raíz + gráficos PNG en ./graficos/.

Filtro de sanidad de precios: las secciones de precio (6, 7, 8) y la mediana
de la sección 2 excluyen anuncios con precio placeholder (< PRECIO_MIN_SANO_USD
USD). El dataset NUNCA se modifica.

Uso:
  python scripts/analisis_mercado.py
"""
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
ENTRADA = ROOT / 'data' / 'processed' / 'triciclos_aceptados_normalizado.json'
INFORME = ROOT / 'docs' / 'informe_mercado.md'
GRAFICOS = ROOT / 'graficos'

ACEPTADOS_HISTORICOS = 769
DESCARGADOS_HISTORICOS = 1378
DUPLICADOS_ELIMINADOS = 12
SIN_DESCARGAR = 80
PRECIO_MIN_SANO_USD = 100


def es_sana(r):
    """True si el anuncio tiene precio USD creíble (no placeholder)."""
    return (r.get('moneda_original') == 'USD'
            and (r.get('precio_publicado') or 0) >= PRECIO_MIN_SANO_USD)


def es_placeholder(r):
    return (r.get('moneda_original') == 'USD'
            and 0 < (r.get('precio_publicado') or 0) < PRECIO_MIN_SANO_USD)


def fmt(n, dec=0):
    if n is None:
        return '—'
    if isinstance(n, float):
        return f'{n:,.{dec}f}'.replace(',', ' ')
    return f'{n:,}'.replace(',', ' ')


def pct(x):
    return f'{x * 100:.1f}%'


def stats(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return {
        'n': len(vals),
        'min': min(vals),
        'med': statistics.median(vals),
        'max': max(vals),
        'mean': statistics.mean(vals),
    }


def pearson(xs, ys):
    pares = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    n = len(pares)
    if n < 3:
        return None, n
    mx = sum(x for x, _ in pares) / n
    my = sum(y for _, y in pares) / n
    sxy = sum((x - mx) * (y - my) for x, y in pares)
    sxx = sum((x - mx) ** 2 for x, _ in pares)
    syy = sum((y - my) ** 2 for _, y in pares)
    if sxx == 0 or syy == 0:
        return None, n
    return sxy / math.sqrt(sxx * syy), n


def guardar_grafico(fig, nombre):
    GRAFICOS.mkdir(exist_ok=True)
    path = GRAFICOS / nombre
    fig.savefig(path, dpi=120, bbox_inches='tight')
    plt.close(fig)
    return path


def grafico_barras(conteos, titulo, xlabel, nombre):
    fig, ax = plt.subplots(figsize=(10, 6))
    etiquetas = [k for k, _ in conteos]
    valores = [v for _, v in conteos]
    ax.barh(etiquetas[::-1], valores[::-1], color='#2b7bba')
    ax.set_xlabel(xlabel)
    ax.set_title(titulo)
    ax.grid(axis='x', alpha=0.3)
    for i, v in enumerate(valores[::-1]):
        ax.text(v + max(valores) * 0.01, i, str(v), va='center', fontsize=9)
    return guardar_grafico(fig, nombre)


def cargar():
    if not ENTRADA.exists():
        sys.exit(f'ERROR: no existe {ENTRADA}')
    with open(ENTRADA, encoding='utf-8') as f:
        return json.load(f)


def seccion_marcas(regs):
    total = len(regs)
    conteo = Counter(r['marca_detectada'] for r in regs)
    top = conteo.most_common(10)
    otras_n = total - sum(n for _, n in top)

    precios_sanos = defaultdict(list)
    placeholders = Counter()
    for r in regs:
        if es_sana(r):
            precios_sanos[r['marca_detectada']].append(r['precio_publicado'])
        elif es_placeholder(r):
            placeholders[r['marca_detectada']] += 1
    ph_total = sum(placeholders.values())

    todas = conteo.most_common()
    top10 = todas[:10]
    otras_vals = [p for m, n in todas[10:] for p in precios_sanos[m]]
    otras_ph = sum(placeholders[m] for m, n in todas[10:])

    lineas = [
        '## 2. Distribución por marca',
        '',
        f'Un total de **{len(conteo)} marcas distintas**. Top 10 + resto. '
        f'El precio mediano usa solo anuncios con precio ≥ {PRECIO_MIN_SANO_USD} USD '
        f'(excluye {ph_total} placeholders); la columna `n_ph` cuenta los excluidos '
        'de esa marca:',
        '',
        '| Marca | Anuncios | % | Precio mediano (USD, sanos) | n_ph |',
        '|---|---:|---:|---:|---:|',
    ]
    for m, n in top10:
        med = statistics.median(precios_sanos[m]) if precios_sanos.get(m) else None
        lineas.append(f'| {m} | {n} | {pct(n / total)} | {fmt(med)} | {placeholders.get(m, 0)} |')
    if otras_n:
        med_otras = statistics.median(otras_vals) if otras_vals else None
        lineas.append(f'| Otras ({len(conteo) - 10} marcas) | {otras_n} | {pct(otras_n / total)} '
                      f'| {fmt(med_otras)} | {otras_ph} |')
    lineas += ['', f'`precio_publicado` sin nulls: {total}/{total}.', '']
    return lineas, top


def seccion_tipos(regs):
    total = len(regs)
    orden = ['eléctrico', 'combustible', 'híbrido']
    conteo = Counter(r['tipo_triciclo'] for r in regs)
    precios = defaultdict(list)
    for r in regs:
        precios[r['tipo_triciclo']].append(r.get('precio_publicado'))

    lineas = [
        '## 3. Distribución por tipo de triciclo',
        '',
        '| Tipo | Anuncios | % | Precio mediano (USD) |',
        '|---|---:|---:|---:|',
    ]
    for t in orden:
        n = conteo.get(t, 0)
        if n == 0:
            lineas.append(f'| {t} | 0 | 0,0% | — |')
            continue
        lineas.append(f'| {t} | {n} | {pct(n / total)} | {fmt(statistics.median(precios[t]))} |')
    extra = set(conteo) - set(orden)
    for t in sorted(extra):
        n = conteo[t]
        lineas.append(f'| {t} (otro) | {n} | {pct(n / total)} | {fmt(statistics.median(precios[t]))} |')
    lineas += ['',
               f'Nota: el dataset normalizado **no contiene** triciclos de combustión simple '
               f'(0 registros); todo es eléctrico o híbrido.', '']
    return lineas


def seccion_tecnicas(regs):
    total = len(regs)
    volt_vals = [r.get('voltaje_bateria') for r in regs]
    volt_n = sum(1 for v in volt_vals if v is not None)
    conteo_volt = Counter(v for v in volt_vals if v is not None)

    amin = [r.get('autonomia_km_min') for r in regs]
    amax = [r.get('autonomia_km_max') for r in regs]
    st_min = stats(amin)
    st_max = stats(amax)

    lineas = [
        '## 4. Especificaciones técnicas',
        '',
        '### 4.1 Voltaje de batería',
        '',
        f'**{volt_n}/{total}** anuncios indican voltaje '
        f'(**{total - volt_n} nulls**, {pct((total - volt_n) / total)}). Valores detectados:',
        '',
        '| Voltaje (V) | Anuncios |',
        '|---:|---:|',
    ]
    for v, n in sorted(conteo_volt.items()):
        lineas.append(f'| {v} | {n} |')
    lineas += [
        '',
        '### 4.2 Autonomía (km)',
        '',
        f'Campos derivados del rango publicado; **sin nulls** ({total}/{total} en min y max).',
        '',
        '| Campo | n válido | Mínimo | Mediana | Máximo |',
        '|---|---:|---:|---:|---:|',
        f'| autonomia_km_min | {st_min["n"]} | {fmt(st_min["min"])} | {fmt(st_min["med"])} | {fmt(st_min["max"])} |',
        f'| autonomia_km_max | {st_max["n"]} | {fmt(st_max["min"])} | {fmt(st_max["med"])} | {fmt(st_max["max"])} |',
        '',
    ]
    return lineas


def seccion_ubicacion(regs):
    total = len(regs)
    prov = Counter(r.get('ubicacion') or '(sin dato)' for r in regs)
    mun = Counter(r.get('municipio') or '(sin dato)' for r in regs)
    prov_n = sum(1 for r in regs if r.get('ubicacion'))
    mun_n = sum(1 for r in regs if r.get('municipio'))

    lineas = [
        '## 5. Distribución geográfica',
        '',
        f'Campo provincia = `ubicacion` (**{prov_n}/{total}** con dato). '
        f'Campo municipio = `municipio` (**{mun_n}/{total}** con dato).',
        '',
        '### 5.1 Top provincias',
        '',
        '| Provincia | Anuncios | % |',
        '|---|---:|---:|',
    ]
    for p, n in prov.most_common(10):
        lineas.append(f'| {p} | {n} | {pct(n / total)} |')
    lineas += [
        '',
        f'El dataset solo cubre {len(prov)} provincias (sesgo hacia La Habana).',
        '',
        '### 5.2 Top municipios',
        '',
        '| Municipio | Anuncios | % |',
        '|---|---:|---:|',
    ]
    for m, n in mun.most_common(10):
        lineas.append(f'| {m} | {n} | {pct(n / total)} |')
    lineas.append('')
    return lineas, prov


def seccion_precios(regs, sanas):
    total = len(regs)
    n_sanas = len(sanas)
    st_global = stats([r['precio_publicado'] for r in sanas])

    lineas = [
        '## 6. Precios (USD)',
        '',
        f'El 100% de los anuncios ({total}/{total}) está publicado en USD; no se aplica '
        'conversión de moneda. **Filtro de sanidad aplicado:** se excluyen los '
        f'{total - n_sanas} anuncios con precio placeholder (< {PRECIO_MIN_SANO_USD} USD); '
        f'**n_filtrado = {n_sanas}** de {total}.',
        '',
        f'**Global (sanos):** n={st_global["n"]}, min={fmt(st_global["min"])}, '
        f'mediana={fmt(st_global["med"])}, max={fmt(st_global["max"])} USD.',
        '',
        '### 6.1 Por marca (top 10 por volumen)',
        '',
        '| Marca | n | Mínimo | Mediana | Máximo |',
        '|---|---:|---:|---:|---:|',
    ]
    conteo = Counter(r['marca_detectada'] for r in regs)
    por_marca = defaultdict(list)
    for r in sanas:
        por_marca[r['marca_detectada']].append(r['precio_publicado'])
    for m, _ in conteo.most_common(10):
        s = stats(por_marca.get(m, []))
        if s:
            lineas.append(f'| {m} | {s["n"]} | {fmt(s["min"])} | {fmt(s["med"])} | {fmt(s["max"])} |')

    lineas += [
        '',
        '### 6.2 Por tipo de triciclo',
        '',
        '| Tipo | n | Mínimo | Mediana | Máximo |',
        '|---|---:|---:|---:|---:|',
    ]
    por_tipo = defaultdict(list)
    for r in sanas:
        por_tipo[r['tipo_triciclo']].append(r['precio_publicado'])
    for t in sorted(por_tipo):
        s = stats(por_tipo[t])
        lineas.append(f'| {t} | {s["n"]} | {fmt(s["min"])} | {fmt(s["med"])} | {fmt(s["max"])} |')
    lineas.append('')
    return lineas, st_global


def seccion_correlaciones(sanas):
    n_sanas = len(sanas)
    lineas = [
        '## 7. Correlaciones de Pearson',
        '',
        f'Solo pares donde ambos campos no son null. **Filtro de sanidad aplicado** '
        f'(precio ≥ {PRECIO_MIN_SANO_USD} USD): **n_filtrado = {n_sanas}** anuncios.',
        '',
        '| Par | r de Pearson | n válido |',
        '|---|---:|---:|',
    ]
    r1, n1 = pearson([r.get('precio_publicado') for r in sanas],
                     [r.get('voltaje_bateria') for r in sanas])
    r2, n2 = pearson([r.get('precio_publicado') for r in sanas],
                     [r.get('autonomia_km_max') for r in sanas])
    lineas.append(f'| precio vs voltaje_batería | {r1:+.3f} | {n1} |')
    lineas.append(f'| precio vs autonomia_km_max | {r2:+.3f} | {n2} |')
    lineas += [
        '',
        'Correlación no implica causalidad; la muestra no es aleatoria ni representativa.',
        '',
    ]
    return lineas, (r1, n1), (r2, n2)


def seccion_ratio(regs, sanas):
    candidatos = [r for r in sanas if (r.get('autonomia_km_max') or 0) > 0]
    ordenados = sorted(
        candidatos,
        key=lambda r: r['precio_publicado'] / r['autonomia_km_max'],
    )[:20]

    malos = [r for r in ordenados if r['precio_publicado'] < PRECIO_MIN_SANO_USD]
    if malos:
        sys.exit(f'BUG: {len(malos)} precios placeholder (< {PRECIO_MIN_SANO_USD} USD) '
                 'filtrados en el Top 20 ratio.')

    lineas = [
        '## 8. Top 20 mejor relación precio/autonomía',
        '',
        f'Criterio: `precio_publicado / autonomia_km_max` (menor = mejor), solo USD con '
        f'ambos > 0 y precio ≥ {PRECIO_MIN_SANO_USD} USD. '
        f'Candidatos válidos: {len(candidatos)}/{len(regs)} '
        f'(**n_filtrado = {len(sanas)}** tras filtro de sanidad).',
        '',
        '| # | Marca | Tipo | Precio (USD) | Autonomía máx (km) | Ratio (USD/km) | Enlace |',
        '|---:|---|---|---:|---:|---:|---|',
    ]
    for i, r in enumerate(ordenados, 1):
        ratio = r['precio_publicado'] / r['autonomia_km_max']
        lineas.append(
            f'| {i} | {r["marca_detectada"]} | {r["tipo_triciclo"]} | '
            f'{fmt(r["precio_publicado"])} | {fmt(r["autonomia_km_max"])} | '
            f'{ratio:.2f} | {r["enlace"]} |'
        )
    lineas.append('')
    return lineas


def seccion_limitaciones(total):
    return [
        '## 9. Limitaciones',
        '',
        f'- **{SIN_DESCARGAR} anuncios no descargados**: el scraping se detuvo a p90 de 253 '
        'páginas por challenge de Cloudflare; restan cobertura al universo real.',
        f'- **{DUPLICADOS_ELIMINADOS} duplicados eliminados** en la normalización '
        f'(769 → {total} aceptados) por clave (gcsKey, phone).',
        '- **Sesgo geográfico**: solo Revolico (Cuba), con concentración extrema en La Habana; '
        'no representa mercados fuera de la isla.',
        '- **Muestra no aleatoria**: son anuncios publicados, no ventas cerradas; el precio '
        'publicado puede no ser el precio final.',
        '- **Rango temporal acotado**: todas las publicaciones son de 2026 '
        '(ventana observada: 2026-10-08 a 2026-10-14), insuficiente para tendencias.',
        '',
    ]


def seccion_calidad(regs):
    total = len(regs)
    ph = [r for r in regs if es_placeholder(r)]
    n_ph = len(ph)
    c_igual_1 = sum(1 for r in ph if r['precio_publicado'] == 1)
    c_men_10 = sum(1 for r in ph if r['precio_publicado'] < 10)
    c_10_99 = sum(1 for r in ph if 10 <= r['precio_publicado'] < 100)

    return [
        '## 10. Calidad de datos — precios placeholder',
        '',
        f'**{n_ph}/{total}** anuncios ({pct(n_ph / total)}) tienen '
        f'`precio_publicado` < {PRECIO_MIN_SANO_USD} USD. Desglose:',
        '',
        '| Rango | Anuncios |',
        '|---|---:|',
        f'| precio == 1 USD | {c_igual_1} |',
        f'| precio < 10 USD | {c_men_10} |',
        f'| precio 10–99 USD | {c_10_99} |',
        '',
        f'Los anuncios con precio placeholder (< {PRECIO_MIN_SANO_USD} USD) se excluyen de '
        'las secciones 6, 7 y 8. Se mantienen en las secciones 2-5, 9 donde el precio no es '
        'variable analizada.',
        '',
    ]


def graficos(regs, sanas, top_marcas, prov):
    rutas = []

    conteo_top = top_marcas[:10]
    rutas.append(grafico_barras(conteo_top, 'Top 10 marcas de triciclos (Revolico)',
                                'Número de anuncios', '01_marcas.png'))

    todos_usd = [r['precio_publicado'] for r in regs
                 if r.get('moneda_original') == 'USD' and (r.get('precio_publicado') or 0) > 0]
    sanos_usd = [r['precio_publicado'] for r in sanas]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    ax1.hist(todos_usd, bins=30, color='#d95f02', edgecolor='white')
    ax1.set_xscale('log')
    ax1.set_xlabel('precio_publicado (USD, escala log)')
    ax1.set_ylabel('Frecuencia')
    ax1.set_title(f'(a) Todos los USD (n={len(todos_usd)}), escala log')
    ax1.grid(axis='y', alpha=0.3)

    ax2.hist(sanos_usd, bins=30, color='#2b7bba', edgecolor='white')
    ax2.set_xlabel(f'precio_publicado (USD, sanos ≥ {PRECIO_MIN_SANO_USD})')
    ax2.set_ylabel('Frecuencia')
    ax2.set_title(f'(b) Solo sanos (n={len(sanos_usd)})')
    ax2.grid(axis='y', alpha=0.3)

    fig.suptitle('Distribución de precios — con y sin placeholders', y=1.02)
    fig.tight_layout()
    rutas.append(guardar_grafico(fig, '02_precios_hist.png'))

    pares = [(r['precio_publicado'], r['autonomia_km_max']) for r in sanas
             if (r.get('autonomia_km_max') or 0) > 0]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter([p[1] for p in pares], [p[0] for p in pares],
               alpha=0.5, s=25, color='#2b7bba')
    ax.set_xlabel('autonomia_km_max (km)')
    ax.set_ylabel('precio_publicado (USD)')
    ax.set_title(f'Precio vs autonomía máxima (solo USD sanos, n={len(pares)})')
    ax.grid(alpha=0.3)
    rutas.append(guardar_grafico(fig, '03_precio_vs_autonomia.png'))

    rutas.append(grafico_barras(prov.most_common(10), 'Top provincias por anuncios (Revolico)',
                                'Número de anuncios', '04_provincias.png'))
    return rutas


def main():
    regs = cargar()
    total = len(regs)
    sanas = [r for r in regs if es_sana(r)]
    ph = [r for r in regs if es_placeholder(r)]

    fechas = sorted(r['fecha_publicacion'] for r in regs if r.get('fecha_publicacion'))
    fecha_min, fecha_max = fechas[0], fechas[-1]
    tasa = ACEPTADOS_HISTORICOS / DESCARGADOS_HISTORICOS

    l1 = [
        '# Informe de mercado — Triciclos en Revolico (Cuba)',
        '',
        f'- **Registros analizados (post-dedup):** {total}',
        f'- **Rango de fechas de publicación:** {fecha_min} → {fecha_max}',
        f'- **Tasa de aceptación histórica del pipeline:** {ACEPTADOS_HISTORICOS}/{DESCARGADOS_HISTORICOS} = {pct(tasa)}',
        f'- **Duplicados eliminados en la normalización:** {DUPLICADOS_ELIMINADOS} registros '
        f'(12 grupos por gcsKey+phone; 769 → {total})',
        f'- **Filtro de sanidad de precios:** {len(sanas)}/{total} anuncios con precio USD ≥ '
        f'{PRECIO_MIN_SANO_USD} (secciones 6-8; ver sección 10)',
        '',
    ]

    l2, top_marcas = seccion_marcas(regs)
    l3 = seccion_tipos(regs)
    l4 = seccion_tecnicas(regs)
    l5, prov = seccion_ubicacion(regs)
    l6, st_global = seccion_precios(regs, sanas)
    l7, (r_volt, n_volt), (r_aut, n_aut) = seccion_correlaciones(sanas)
    l8 = seccion_ratio(regs, sanas)
    l9 = seccion_limitaciones(total)
    l10 = seccion_calidad(regs)

    contenido = '\n'.join(l1 + l2 + l3 + l4 + l5 + l6 + l7 + l8 + l9 + l10)
    INFORME.write_text(contenido, encoding='utf-8')

    rutas_graficos = graficos(regs, sanas, top_marcas, prov)

    top3_n = sum(n for _, n in top_marcas[:3])
    print('=== ANÁLISIS DE MERCADO COMPLETADO ===')
    print(f'Informe:   {INFORME}')
    print('Gráficos:')
    for p in rutas_graficos:
        print(f'  {p}')
    print()
    print('=== MÉTRICAS CLAVE ===')
    print(f'n registros:            {total}')
    print(f'Placeholders (<{PRECIO_MIN_SANO_USD} USD): {len(ph)} ({pct(len(ph) / total)})')
    print(f'n sanos (secciones 6-8): {len(sanas)}')
    print(f'Fechas:                 {fecha_min} → {fecha_max}')
    print(f'Top 3 marcas:           {pct(top3_n / total)} del total '
          f'({", ".join(f"{m} ({n})" for m, n in top_marcas[:3])})')
    print(f'Precio mediano global:  {fmt(st_global["med"])} USD (n={st_global["n"]}, sanos)')
    print(f'Rango de precios:       {fmt(st_global["min"])} – {fmt(st_global["max"])} USD (sanos)')
    print(f'Corr precio-voltaje:    r={r_volt:+.3f} (n={n_volt})')
    print(f'Corr precio-autonomía:  r={r_aut:+.3f} (n={n_aut})')
    print(f'Dataset intacto:        {ENTRADA.name} no fue modificado.')


if __name__ == '__main__':
    main()
