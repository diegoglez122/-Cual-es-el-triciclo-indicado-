# Clustering de anuncios Revolico (757)

- Total entradas: 757
- En USD: 757
- Completos: 570
- Descartados: {'no_usd': 0, 'sin_precio': 0, 'sin_km': 0, 'sin_voltaje': 187, 'sin_tipo': 0}

## Silhouette vs k

| k | silhouette |
|---|---|
| 2 | 0.4251 |
| 3 | 0.3754 |
| 4 | 0.3644 |
| 5 | 0.3957 |
| 6 | 0.4122 |
| 7 | 0.3973 |
| 8 | 0.4098 |

**Mejor k = 2, silhouette = 0.4251**

**Conclusión:** silhouette > 0.4 → **hay estructura latente**. Investigar antes de seguir.

## Perfil de clusters

| cluster | n | precio_med | km_med | volt_med | %elec | marca_top |
|---|---|---|---|---|---|---|
| 0 | 455 | 4400 | 100 | 72 | 93% | Bryderk (96) |
| 1 | 115 | 3550 | 80 | 60 | 83% | Oim (27) |