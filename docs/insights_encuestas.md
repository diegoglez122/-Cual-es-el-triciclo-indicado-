# Insights de Encuestas - EDA Avanzado

**Total encuestados:** 40

---

## Bloque A: Comportamiento y Negocio

### 1) Ganancias vs. Tiempo en negocio

| tendencia_ganancias | aumentado | disminuido | estable | All |
|---------------------|-----------|------------|---------|-----|
| tiempo_en_negocio   |           |            |         |     |
| 1_3a                | 1         | 2          | 4       | 7   |
| 6m_1a               | 1         | 6          | 5       | 12  |
| gt3a                | 2         | 4          | 5       | 11  |
| lt6m                | 0         | 5          | 5       | 10  |
| All                 | 4         | 17         | 19      | 40  |

### 2) Fijación de precios

**precio_pasaje_fijo:**
| precio_pasaje_fijo | count |
|--------------------|-------|
| Si                 | 21    |
| No                 | 19    |

**fijacion_precio:**
| fijacion_precio | count |
|-----------------|-------|
| choferes        | 21    |
| onat            | 13    |
| None            | 6     |

### 3) Impacto Estatal (afectado_estatales = Si)

- **n:** 15
- **Distribución de tendencia_ganancias:**
  | tendencia_ganancias | count |
  |---------------------|-------|
  | disminuido          | 10    |
  | estable             | 3     |
  | aumentado           | 2     |

- **Predominante:** disminuido

### 4) Dueño vs Chofer

**Conteo de es_duenio:**
| es_duenio | count |
|-----------|-------|
| 1.0       | 25    |
| 0.0       | 14    |
| NaN       | 1     |

**Ingreso diario promedio (CUP):**
| es_duenio | ingreso_diario_cup (promedio) |
|-----------|-------------------------------|
| 0.0       | 5073.08                       |
| 1.0       | 4120.00                       |

### 5) Costo de vida - demanda_costo_vida = Disminuido

- **n:** 18
- **Distribución de tendencia_ganancias:**
  | tendencia_ganancias | count |
  |---------------------|-------|
  | disminuido          | 10    |
  | estable             | 6     |
  | aumentado           | 2     |

### 6) Recuperación de inversión

- **Valores únicos recupero_inversion:** ['No', 'Si']

- **Por recupero_inversion:**
  | recupero_inversion | marca_top | modalidad_top | n  |
  |--------------------|-----------|---------------|----|
  | No                 | Raly      | urbano        | 29 |
  | Si                 | Raly      | mixto         | 11 |

### 7) Electricidad - costo luz y panel solar

- **Costo luz mes (CUP) - promedio (n=25):** 1764.00

- **Ingreso diario promedio por uso de panel solar:**
  | usa_panel_solar | ingreso_diario_cup (promedio) |
  |-----------------|-------------------------------|
  | No              | 4638.00                       |
  | Si              | 4035.71                       |

---

## Bloque B: Fallas y Calidad

### 8) Documentación legal - número de documentos por encuestado

| num_documentos | cantidad_encuestados |
|----------------|---------------------|
| 0              | 1                   |
| 1              | 7                   |
| 2              | 20                  |
| 3              | 9                   |
| 4              | 3                   |

*CSV guardado:* `data/processed/encuestas_eda/dw_documentos.csv`

### 9) Fallas de batería (piezas_bateria = Si)

- **n:** 13
- **Modalidad predominante:**
  | modalidad | count |
  |-----------|-------|
  | mixto     | 8     |
  | urbano    | 5     |

### 10) Fallas de gomas (piezas_gomas = Si)

- **n:** 23
- **Modalidad predominante:**
  | modalidad      | count |
  |----------------|-------|
  | mixto          | 12    |
  | urbano         | 8     |
  | intermunicipal | 3     |

### 11) Ranking de fallas por marca

| marca            | total_encuestados | fallas_bateria | fallas_gomas | fallas_motor | total_fallas |
|------------------|-------------------|----------------|--------------|--------------|--------------|
| Raly             | 12                | 3              | 8            | 1            | 12           |
| Jinpeng          | 6                 | 2              | 4            | 1            | 7            |
| Nippon           | 3                 | 3              | 3            | 0            | 6            |
| ACC              | 3                 | 1              | 2            | 1            | 4            |
| Oneboot          | 1                 | 1              | 1            | 0            | 2            |
| Rali (dejar así) | 1                 | 1              | 1            | 0            | 2            |
| Onebot           | 2                 | 1              | 0            | 0            | 1            |
| Oim              | 1                 | 1              | 0            | 0            | 1            |
| Cem              | 1                 | 0              | 1            | 0            | 1            |
| VEDCA            | 2                 | 0              | 1            | 0            | 1            |
| Xinger           | 1                 | 0              | 1            | 0            | 1            |
| Singer           | 1                 | 0              | 1            | 0            | 1            |
| Fénix            | 1                 | 0              | 0            | 0            | 0            |
| Kvitova          | 1                 | 0              | 0            | 0            | 0            |
| Izuki            | 2                 | 0              | 0            | 0            | 0            |
| Topmaq           | 1                 | 0              | 0            | 0            | 0            |
| mishozuki        | 1                 | 0              | 0            | 0            | 0            |

*CSV guardado:* `data/processed/encuestas_eda/dw_fallas_marcas.csv`

---

## Bloque C: El Cruce Maestro (Formal vs. Informal vs. Real)

### 12) Comparación de precios

- **Precio promedio encuestados (precio_vehiculo_usd):** 4004.62 USD (n=40)

- **Promedio por importadora (catálogo consolidado):**
  - MZ Products: 4654.29 USD
  - Kikihabana: 3140.44 USD
  - Nihao53: 3465.43 USD

- **Mediana Revolico (USD):** 4300.00 USD (n=757)

**CONCLUSIÓN:** Los encuestados pagaron EN PROMEDIO MÁS CARO (4005 USD) que el mercado formal/catalogado (MZ Products 4654, Kikihabana 3140, Nihao53 3465). Esto sugiere compra en el mercado informal o con márgenes de reventa/importación.
