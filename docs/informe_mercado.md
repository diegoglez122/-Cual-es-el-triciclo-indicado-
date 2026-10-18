# Informe de mercado — Triciclos en Revolico (Cuba)

- **Registros analizados (post-dedup):** 757
- **Rango de fechas de publicación:** 2026-10-08 → 2026-10-14
- **Tasa de aceptación histórica del pipeline:** 769/1378 = 55.8%
- **Duplicados eliminados en la normalización:** 12 registros (12 grupos por gcsKey+phone; 769 → 757)
- **Filtro de sanidad de precios:** 747/757 anuncios con precio USD ≥ 100 (secciones 6-8; ver sección 10)

## 2. Distribución por marca

Un total de **39 marcas distintas**. Top 10 + resto. El precio mediano usa solo anuncios con precio ≥ 100 USD (excluye 10 placeholders); la columna `n_ph` cuenta los excluidos de esa marca:

| Marca | Anuncios | % | Precio mediano (USD, sanos) | n_ph |
|---|---:|---:|---:|---:|
| Bryderk | 102 | 13.5% | 4 400 | 0 |
| Kvitova | 80 | 10.6% | 3 600 | 1 |
| Jinpeng | 78 | 10.3% | 4 900 | 0 |
| Topmaq | 62 | 8.2% | 4 200 | 1 |
| Star | 54 | 7.1% | 4 400 | 0 |
| Mvp | 43 | 5.7% | 4 050 | 1 |
| Maf | 42 | 5.5% | 4 250 | 1 |
| Oim | 36 | 4.8% | 3 750 | 1 |
| Onebot | 34 | 4.5% | 4 740 | 0 |
| Vedca | 32 | 4.2% | 5 150 | 2 |
| Otras (29 marcas) | 194 | 25.6% | 4 400 | 3 |

`precio_publicado` sin nulls: 757/757.

## 3. Distribución por tipo de triciclo

| Tipo | Anuncios | % | Precio mediano (USD) |
|---|---:|---:|---:|
| eléctrico | 686 | 90.6% | 4 300 |
| combustible | 0 | 0,0% | — |
| híbrido | 71 | 9.4% | 4 150 |

Nota: el dataset normalizado **no contiene** triciclos de combustión simple (0 registros); todo es eléctrico o híbrido.

## 4. Especificaciones técnicas

### 4.1 Voltaje de batería

**570/757** anuncios indican voltaje (**187 nulls**, 24.7%). Valores detectados:

| Voltaje (V) | Anuncios |
|---:|---:|
| 36 | 3 |
| 60 | 186 |
| 62 | 3 |
| 72 | 376 |
| 74 | 2 |

### 4.2 Autonomía (km)

Campos derivados del rango publicado; **sin nulls** (757/757 en min y max).

| Campo | n válido | Mínimo | Mediana | Máximo |
|---|---:|---:|---:|---:|
| autonomia_km_min | 757 | 14 | 100 | 180 |
| autonomia_km_max | 757 | 14 | 100 | 180 |

## 5. Distribución geográfica

Campo provincia = `ubicacion` (**757/757** con dato). Campo municipio = `municipio` (**757/757** con dato).

### 5.1 Top provincias

| Provincia | Anuncios | % |
|---|---:|---:|
| La Habana | 730 | 96.4% |
| Artemisa | 23 | 3.0% |
| Matanzas | 3 | 0.4% |
| Holguín | 1 | 0.1% |

El dataset solo cubre 4 provincias (sesgo hacia La Habana).

### 5.2 Top municipios

| Municipio | Anuncios | % |
|---|---:|---:|
| Centro Habana | 218 | 28.8% |
| Playa | 126 | 16.6% |
| Diez de Octubre | 62 | 8.2% |
| Plaza | 62 | 8.2% |
| La Lisa | 56 | 7.4% |
| Cerro | 42 | 5.5% |
| Boyeros | 32 | 4.2% |
| Marianao | 32 | 4.2% |
| Arroyo Naranjo | 27 | 3.6% |
| Habana del Este | 26 | 3.4% |

## 6. Precios (USD)

El 100% de los anuncios (757/757) está publicado en USD; no se aplica conversión de moneda. **Filtro de sanidad aplicado:** se excluyen los 10 anuncios con precio placeholder (< 100 USD); **n_filtrado = 747** de 757.

**Global (sanos):** n=747, min=500, mediana=4 300, max=6 900 USD.

### 6.1 Por marca (top 10 por volumen)

| Marca | n | Mínimo | Mediana | Máximo |
|---|---:|---:|---:|---:|
| Bryderk | 102 | 500 | 4 400 | 5 500 |
| Kvitova | 79 | 3 150 | 3 600 | 5 650 |
| Jinpeng | 78 | 3 000 | 4 900 | 5 500 |
| Topmaq | 61 | 1 111 | 4 200 | 5 950 |
| Star | 54 | 4 000 | 4 400 | 5 200 |
| Mvp | 42 | 3 600 | 4 050 | 4 800 |
| Maf | 41 | 1 750 | 4 250 | 6 000 |
| Oim | 35 | 3 300 | 3 750 | 5 450 |
| Onebot | 34 | 3 000 | 4 740 | 5 450 |
| Vedca | 30 | 1 500 | 5 150 | 6 900 |

### 6.2 Por tipo de triciclo

| Tipo | n | Mínimo | Mediana | Máximo |
|---|---:|---:|---:|---:|
| eléctrico | 677 | 520 | 4 350 | 6 900 |
| híbrido | 70 | 500 | 4 165 | 5 950 |

## 7. Correlaciones de Pearson

Solo pares donde ambos campos no son null. **Filtro de sanidad aplicado** (precio ≥ 100 USD): **n_filtrado = 747** anuncios.

| Par | r de Pearson | n válido |
|---|---:|---:|
| precio vs voltaje_batería | +0.045 | 561 |
| precio vs autonomia_km_max | +0.232 | 747 |

Correlación no implica causalidad; la muestra no es aleatoria ni representativa.

## 8. Top 20 mejor relación precio/autonomía

Criterio: `precio_publicado / autonomia_km_max` (menor = mejor), solo USD con ambos > 0 y precio ≥ 100 USD. Candidatos válidos: 747/757 (**n_filtrado = 747** tras filtro de sanidad).

| # | Marca | Tipo | Precio (USD) | Autonomía máx (km) | Ratio (USD/km) | Enlace |
|---:|---|---|---:|---:|---:|---|
| 1 | Bryderk | híbrido | 500 | 80 | 6.25 | https://www.revolico.com/item/triciclo-electrico-bryderk-topmaqprecio-electrico-5000-usd-precio-con-hibrido-con-extensor-5350-usd-57663357 |
| 2 | QLife | eléctrico | 520 | 50 | 10.40 | https://www.revolico.com/item/triciclo-electronico-57434009 |
| 3 | QLife | eléctrico | 615 | 50 | 12.30 | https://www.revolico.com/item/triciclo-marca-qlife-57321548 |
| 4 | Topmaq | eléctrico | 1 111 | 90 | 12.34 | https://www.revolico.com/item/triciclo-vedca-y-bicimotos-56999548 |
| 5 | Vedca | eléctrico | 1 500 | 100 | 15.00 | https://www.revolico.com/item/motos-bicimotos-triciclos-electricos-58099263 |
| 6 | Maf | eléctrico | 1 800 | 120 | 15.00 | https://www.revolico.com/item/triciclos-electricos-marca-maf-de-paseo-pequenos-nuevos-0km-56910334 |
| 7 | Jinpeng | híbrido | 3 970 | 180 | 22.06 | https://www.revolico.com/item/triciclo-58053003 |
| 8 | Jinpeng | híbrido | 4 950 | 180 | 27.50 | https://www.revolico.com/item/triciclos-hibridos-jinpeng-ty150uk-0kmlis-56357002 |
| 9 | Jinpeng | híbrido | 5 000 | 180 | 27.78 | https://www.revolico.com/item/triciclo-jimpeng-hibrido-nuevo-listo-a-estrenar-por-usted-6-meses-de-garantia-57048532 |
| 10 | TRICICLOS | eléctrico | 3 450 | 120 | 28.75 | https://www.revolico.com/item/triciclos-58082306 |
| 11 | Maf | eléctrico | 1 750 | 60 | 29.17 | https://www.revolico.com/item/triciclo-maf-de-paseo-p0530-av011-57216472 |
| 12 | Jinpeng | híbrido | 5 250 | 180 | 29.17 | https://www.revolico.com/item/triciclo-jimpeng-hibrido-ty150uk-0-km-57110399 |
| 13 | TRICICLOS | eléctrico | 3 600 | 120 | 30.00 | https://www.revolico.com/item/triciclo-57989098 |
| 14 | Kvitova | eléctrico | 3 600 | 120 | 30.00 | https://www.revolico.com/item/triciclos-kvitova-58098644 |
| 15 | Maf | eléctrico | 1 800 | 60 | 30.00 | https://www.revolico.com/item/triciclo-electrico-marca-maf-de-paseo-58092413 |
| 16 | Maf | eléctrico | 1 830 | 60 | 30.50 | https://www.revolico.com/item/triciclo-electrico-58099864 |
| 17 | Jinpeng | híbrido | 5 500 | 180 | 30.56 | https://www.revolico.com/item/triciclo-jimpeng-hibrido-56494231 |
| 18 | MOTOR | eléctrico | 4 000 | 130 | 30.77 | https://www.revolico.com/item/ganga-triciclo-58113763 |
| 19 | Star | eléctrico | 4 000 | 130 | 30.77 | https://www.revolico.com/item/tricicloooooo-gangaaaaaa-56461303 |
| 20 | Kvitova | eléctrico | 3 700 | 120 | 30.83 | https://www.revolico.com/item/triciclo-kvitova-58058695 |

## 9. Limitaciones

- **80 anuncios no descargados**: el scraping se detuvo a p90 de 253 páginas por challenge de Cloudflare; restan cobertura al universo real.
- **12 duplicados eliminados** en la normalización (769 → 757 aceptados) por clave (gcsKey, phone).
- **Sesgo geográfico**: solo Revolico (Cuba), con concentración extrema en La Habana; no representa mercados fuera de la isla.
- **Muestra no aleatoria**: son anuncios publicados, no ventas cerradas; el precio publicado puede no ser el precio final.
- **Rango temporal acotado**: todas las publicaciones son de 2026 (ventana observada: 2026-10-08 a 2026-10-14), insuficiente para tendencias.

## 10. Calidad de datos — precios placeholder

**10/757** anuncios (1.3%) tienen `precio_publicado` < 100 USD. Desglose:

| Rango | Anuncios |
|---|---:|
| precio == 1 USD | 9 |
| precio < 10 USD | 10 |
| precio 10–99 USD | 0 |

Los anuncios con precio placeholder (< 100 USD) se excluyen de las secciones 6, 7 y 8. Se mantienen en las secciones 2-5, 9 donde el precio no es variable analizada.

## 11. Drivers de precio

### 11.1 Resumen global del precio

Filtro: USD y precio ≥ 100 (mismo filtro que las secciones 6-8).

| Métrica | Valor (USD) |
|---|---:|
| n | 747 |
| Mínimo | 500 |
| Q1 | 3 800 |
| **Mediana** | **4 300** |
| Q3 | 4 750 |
| Máximo | 6 900 |
| Media | 4 336 |

Asimetría positiva: media (4 336) > mediana (4 300) por anuncios de precio alto.

### 11.2 Precio por marca (top 17 con n ≥ 10)

IC 95% bootstrap de la mediana, 1,000 réplicas, semilla 42 (reproducible). Orden por mediana descendente.

| Marca | n | Mediana | IC 95% inf | IC 95% sup | Δ vs mediana global |
|---|---:|---:|---:|---:|---:|
| Jmd | 14 | 6 200 | 6 200 | 6 300 | +1 900 |
| Vedca | 30 | 5 150 | 4 850 | 6 800 | +850 |
| Jinpeng | 78 | 4 900 | 4 600 | 4 950 | +600 |
| Onebot | 34 | 4 740 | 4 500 | 5 000 | +440 |
| Mishozuki | 20 | 4 675 | 4 600 | 4 700 | +375 |
| Portobello | 17 | 4 500 | 4 450 | 4 600 | +200 |
| Power Red | 13 | 4 500 | 4 500 | 4 500 | +200 |
| Bryderk | 102 | 4 400 | 4 370 | 4 475 | +100 |
| Star | 54 | 4 400 | 4 300 | 4 400 | +100 |
| Maf | 41 | 4 250 | 4 200 | 4 400 | -50 |
| Topmaq | 61 | 4 200 | 4 100 | 4 500 | -100 |
| Traktion | 28 | 4 175 | 4 100 | 4 300 | -125 |
| Mvp | 42 | 4 050 | 3 900 | 4 100 | -250 |
| Oim | 35 | 3 750 | 3 650 | 4 050 | -550 |
| Kvitova | 79 | 3 600 | 3 600 | 3 650 | -700 |
| Llc | 10 | 3 500 | 3 400 | 3 625 | -800 |
| Viento Rapido | 25 | 3 400 | 3 250 | 3 600 | -900 |

Brecha entre la marca más cara (Jmd, 6 200) y la más barata de la tabla (Viento Rapido, 3 400): **2 800 USD**.

### 11.3 Precio por tipo de triciclo

| Tipo | n | Mediana | IC 95% inf | IC 95% sup |
|---|---:|---:|---:|---:|
| eléctrico | 677 | 4 350 | 4 300 | 4 400 |
| híbrido | 70 | 4 165 | 4 065 | 4 300 |

**Mann-Whitney U** (eléctrico vs híbrido): U = 27 875, **p = 0.0150** → diferencia sí estadísticamente significativa. Diferencia de medianas: 185 USD.

### 11.4 Precio por quintil de autonomía

Quintiles por posición (n ≈ iguales); con tantos empates en autonomía los rangos de valores pueden solaparse entre quintiles. n = 747.

| Quintil | Rango de autonomía | n | Mediana (USD) | IC 95% |
|---|---|---:|---:|---|
| Q1 | 14–80 km | 150 | 3 800 | 3 674–3 815 |
| Q2 | 80–100 km | 149 | 4 500 | 4 350–4 650 |
| Q3 | 100–100 km | 149 | 4 300 | 4 200–4 400 |
| Q4 | 100–120 km | 149 | 4 300 | 4 200–4 400 |
| Q5 | 120–180 km | 150 | 4 500 | 4 400–4 600 |

**Spearman** entre autonomía y precio: **rho = 0.265**, p = 0.0000 (n = 747).

**¿Más autonomía sube el precio? SÍ**: mediana del Q5 (120–180 km) = 4 500 USD vs Q1 (14–80 km) = 3 800 USD → **magnitud: +700 USD** entre extremos.

**Subgrupo modal — `autonomia_km_max` = 100 km exactos:** n = 356 de 747 (47.7%); precio mediano **4 300 USD**, Q1–Q3 3 900–4 600, rango 1 500–6 900 USD.
Por marca dentro del subgrupo (top 10 por n, mediana USD): Bryderk (n=77) 4 400 · Kvitova (n=69) 3 600 · Mvp (n=32) 4 050 · Traktion (n=25) 4 200 · Maf (n=23) 4 250 · Onebot (n=20) 4 775 · Topmaq (n=17) 4 200 · Mishozuki (n=14) 4 700 · Jmd (n=13) 6 200 · Power Red (n=12) 4 500.
Con la autonomía fijada en 100 km el precio sigue abriéndose en 5 400 USD → la variación restante la explican marca, modelo/estado y accesorios; histograma en `graficos/10_precio_100km.png`.

### 11.5 Precio por quintil de voltaje

Quintiles por posición (n ≈ iguales); con tantos empates en voltaje los rangos de valores pueden solaparse entre quintiles. n = 561 (se excluyen 186 anuncios sin voltaje_bateria).

| Quintil | Rango de voltaje | n | Mediana (USD) | IC 95% |
|---|---|---:|---:|---|
| Q1 | 36–60 V | 113 | 4 100 | 3 800–4 550 |
| Q2 | 60–72 V | 112 | 4 440 | 4 200–4 725 |
| Q3 | 72–72 V | 112 | 4 250 | 4 165–4 365 |
| Q4 | 72–72 V | 112 | 4 300 | 4 200–4 400 |
| Q5 | 72–74 V | 112 | 4 300 | 4 200–4 400 |

**Spearman** entre voltaje y precio: **rho = 0.015**, p = 0.7282 (n = 561).

**¿Más voltaje sube el precio? NO**: mediana del Q5 (72–74 V) = 4 300 USD vs Q1 (36–60 V) = 4 100 USD → **magnitud: +200 USD** entre extremos (rho no significativo: p ≥ 0.05).

### 11.6 Precio por marca dentro de cada tipo

¿Se mantiene la diferencia entre marcas al controlar por tipo? Mediana por marca y tipo (celdas con n < 5 señaladas):

| Marca | n eléct. | Mediana eléct. | n híbr. | Mediana híbr. |
|---|---:|---:|---:|---:|
| Jmd | 13 | 6 200 | 1* | 5 150 |
| Vedca | 30 | 5 150 | 0 | — |
| Jinpeng | 70 | 4 900 | 8 | 4 975 |
| Onebot | 34 | 4 740 | 0 | — |
| Mishozuki | 20 | 4 675 | 0 | — |
| Portobello | 16 | 4 500 | 1* | 4 600 |
| Power Red | 13 | 4 500 | 0 | — |
| Bryderk | 98 | 4 400 | 4* | 4 185 |
| Star | 32 | 4 400 | 22 | 4 200 |
| Maf | 41 | 4 250 | 0 | — |
| Topmaq | 59 | 4 200 | 2* | 5 750 |
| Traktion | 28 | 4 175 | 0 | — |
| Mvp | 42 | 4 050 | 0 | — |
| Oim | 34 | 3 750 | 1* | 3 650 |
| Kvitova | 71 | 3 600 | 8 | 4 300 |
| Llc | 0 | — | 10 | 3 500 |
| Viento Rapido | 25 | 3 400 | 0 | — |

(* n < 5, mediana no fiable. Solo 70 anuncios híbridos: las marcas híbridas no permiten comparación por marca.)

**Spearman** entre mediana global de marca y mediana dentro de eléctrico (16 marcas con n_eléc ≥ 10): **rho = 1.000**, p = 0.0000 → **la jerarquía entre marcas se MANTIENE al controlar por tipo** (el efecto de marca no es un artefacto de la mezcla de tipos).

### 11.7 Autonomía dentro de cada marca (top 5)

Spearman rho entre `autonomia_km_max` y precio **dentro** de cada marca: ¿el vendedor cobra más por el modelo de más km?

| Marca | n | rho | p-valor | ¿Cobra más por km? |
|---|---:|---:|---:|:--:|
| Bryderk | 102 | -0.103 | 0.3048 | NO |
| Kvitova | 79 | 0.462 | 0.0000 | SÍ |
| Jinpeng | 78 | 0.585 | 0.0000 | SÍ |
| Topmaq | 61 | 0.090 | 0.4918 | NO |
| Star | 54 | -0.131 | 0.3469 | NO |

**Respuesta:** 2 de 5 marcas muestran una relación positiva y significativa (p < 0.05). En esas marcas, SÍ: el vendedor cobra más por el modelo de mayor autonomía. Donde rho ≈ 0, la marca fija un precio único casi independiente del modelo.

### 11.8 Regresión OLS simple

`precio ~ tipo_triciclo + autonomia_km_max + voltaje_bateria + marca_top10` (10 dummies; marca de referencia = resto de marcas "Otras").

- **n = 561** (completos en voltaje; se excluyen 186 anuncios sin dato).
- **R² = 0.394**, **R² ajustado = 0.380**.
- F = 27.4 (p = 1.63e-51); error típico residual = 613 USD.

| Variable | Coef. (USD) | IC 95% inf | IC 95% sup | p-valor |
|---|---:|---:|---:|---:|
| const | 391.5 | -602.8 | 1,385.7 | 0.4396 |
| tipo_híbrido | -120.4 | -311.8 | 71.1 | 0.2174 |
| autonomia | 11.9 | 8.3 | 15.5 | 0.0000 |
| voltaje | 41.5 | 25.2 | 57.8 | 0.0000 |
| marca_Bryderk | -121.7 | -339.3 | 96.0 | 0.2726 |
| marca_Jinpeng | 511.2 | 313.9 | 708.4 | 0.0000 |
| marca_Kvitova | -852.5 | -1,081.6 | -623.4 | 0.0000 |
| marca_Maf | -302.1 | -607.2 | 3.0 | 0.0523 |
| marca_Mvp | -662.8 | -955.7 | -369.9 | 0.0000 |
| marca_Oim | 2.5 | -268.9 | 273.8 | 0.9857 |
| marca_Onebot | 205.8 | -75.6 | 487.2 | 0.1514 |
| marca_Star | -331.4 | -628.2 | -34.5 | 0.0288 |
| marca_Topmaq | -277.9 | -516.2 | -39.5 | 0.0224 |
| marca_Vedca | 1,353.0 | 1,080.5 | 1,625.4 | 0.0000 |

**VIF** (multicolinealidad):

| Variable | VIF |
|---|---:|
| autonomia | 1.6 |
| voltaje | 3.6 |
| tipo_híbrido | 1.2 |
| marca_Bryderk | 2.7 |
| marca_Jinpeng | 1.5 |
| marca_Kvitova | 2.2 |
| marca_Maf | 1.5 |
| marca_Mvp | 1.4 |
| marca_Oim | 1.3 |
| marca_Onebot | 1.6 |
| marca_Star | 1.7 |
| marca_Topmaq | 2.0 |
| marca_Vedca | 1.4 |

**Conclusión OLS: R² = 0.394 ≥ 0.15 → estas variables sí explican parte relevante del precio** (8 de 13 coeficientes con p < 0.05).

Advertencia: los dummies de marca capturan buena parte de lo que "explica" el precio porque marca y precio se fijan juntos; los coeficientes de autonomía/voltaje son **asociaciones condicionales a la marca**, no causales.

**Conclusión ejecutiva — ¿qué determina el precio de un triciclo?**

1. **La marca es el factor dominante**: entre las 17 marcas con n ≥ 10 la mediana va de 3 400 USD (Viento Rapido) a 6 200 USD (Jmd), una brecha de **2 800 USD** = **+82%** sobre la marca más barata (mediana global 4 300 USD). La jerarquía de marcas se mantiene al controlar por tipo (rho = 1.00, p = 0.0000).
2. **La autonomía SÍ influye**: rho de Spearman = 0.265 (p = 0.0000); Q5 − Q1 = +700 USD entre los extremos de la distribución de autonomía.
3. **El voltaje NO tiene relación marginal con el precio**: rho = 0.015 (p = 0.7282), Q5 − Q1 = +200 USD (no significativo). **Pero en el OLS condicionando a marca y autonomía sí aporta**: +42 USD por voltio (IC 95% +25 a +58, p = 0.0000) → efecto condicional (suprimido por la colinealidad con autonomía, VIF 3.6), no causal.
4. **El tipo (eléctrico vs híbrido) es débil**: Mann-Whitney p = 0.0150 → diferencia real pero pequeña.
5. **Dentro de una misma marca, la autonomía casi no ordena el precio**: solo 2 de 5 marcas top muestran cobro significativamente mayor por más km.
6. **El modelo conjunto** (tipo + autonomía + voltaje + top 10 marcas) alcanza R² = 0.394: el precio se explica sobre todo por **marca**, y en segundo orden por **autonomía declarada** y **voltaje**; el **tipo** aporta poco.


## 12. Limitaciones ampliadas

- **Variables descartadas del análisis de drivers** (por falta de datos o varianza):

  - `garantia_meses`: solo 20/747 anuncios lo declaran → inestable.
  - `panel_incluido`: solo 67/747 con `True`; el resto es `null` (no mencionado, no forzosamente "sin panel").
  - `provincia`: **96% de la muestra es La Habana** (720/747); sin varianza no hay efecto estimable y el resto de provincias tiene n ≤ 23.
  - `tipo_uso`: 653/747 son "carga" y 63 `null` → varianza casi nula.

- **Sesgo geográfico extremo**: 720/747 (96.4%) anuncios de La Habana; Artemisa, Matanzas y Holguín apenas si aparecen. Los precios no son representativos de otras provincias ni de Cuba en su conjunto.

- **Muestra no aleatoria**: son anuncios publicados en Revolico (no ventas cerradas ni precios negociados); el vendedor publica el precio que quiere, no el que recibe.

- **Filtro de sanidad**: 10 anuncios con precio < 100 USD excluidos (placeholder $1-$3); ver §10.

- **Empates masivos**: 356/747 anuncios declaran exactamente 100 km de autonomía y la mayoría 72V; los quintiles de §11.4/§11.5 se construyen por posición y sus rangos se solapan.

- **OLS de §11.8 con n = 561**: los 186 anuncios sin `voltaje_bateria` se excluyen; si el dato faltante no es aleatorio, el modelo sesga.

- **Asociación ≠ causalidad**: marca, autonomía y precio los fija el mismo vendedor; nada aquí identifica efectos causales.

- **Ventana temporal**: una semana (2026-10-08 a 2026-10-14); sin serie histórica no hay tendencias ni estacionalidad.
