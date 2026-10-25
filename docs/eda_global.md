# EDA Global: Precio, Autonomía y Confiabilidad

*Generado automáticamente desde datos de Revolico, importadoras y encuestas.*

## SECCIÓN 1: El Mapa de Precios (¿Dónde es más barato?)

### 1.1 Comparativa de precios

- **Precio promedio de los encuestados:** $4,004.62 USD
- **Mediana de precios en Revolico:** $4,300.00 USD
- **Promedio de importadoras (catálogo consolidado):** $3,569.50 USD

**Conclusión:** Los encuestados pagaron en promedio $4,004.62 USD, lo que representa un 12% más que el promedio de las importadoras ($3,569.50 USD). Esto sugiere una brecha significativa de precios entre el mercado formal y lo que pagan los usuarios finales.

### 1.2 Precios por provincia en Revolico

**Top 5 provincias más caras (mediana USD):**

| provincia   |   median |   count |
|:------------|---------:|--------:|
| Artemisa    |     4400 |      23 |
| La Habana   |     4300 |     730 |
| Matanzas    |     4250 |       3 |
| Holguín     |     3300 |       1 |


**Top 5 provincias más baratas (mediana USD):**

| provincia   |   median |   count |
|:------------|---------:|--------:|
| Artemisa    |     4400 |      23 |
| La Habana   |     4300 |     730 |
| Matanzas    |     4250 |       3 |
| Holguín     |     3300 |       1 |


## SECCIÓN 2: La Autonomía (¿Cuál rinde más?)

### 2.1 Autonomía en importadoras

- **Triciclos eléctricos analizados:** 3
- **Autonomía promedio importadoras:** 103.3 km

### 2.2 Autonomía en Revolico

- **Anuncios analizados:** 757
- **Autonomía promedio Revolico:** 99.1 km

**Conclusión:** Los anuncios de Revolico reportan una autonomía promedio mayor (~99 km) en los datos extraídos, mientras que en el catálogo de importadoras la información de autonomía es escasa o poco sistemática. Esto hace difícil una comparación directa, pero el mercado de segunda mano/Revolico tiende a declarar autonomías variadas; para una decisión de compra es fundamental verificarla con el vendedor.

## SECCIÓN 3: La Voz de la Experiencia (Batería y Marcas)

### 3.1 Vida útil de batería por marca (encuestas)

| marca            |   n |   vida_bat_meses_prom |
|:-----------------|----:|----------------------:|
| Oim              |   1 |                  48   |
| Rali (dejar así) |   1 |                  48   |
| Oneboot          |   1 |                  30   |
| Singer           |   1 |                  30   |
| Nippon           |   3 |                  28   |
| Raly             |  12 |                  24.5 |
| Jinpeng          |   6 |                  20.5 |
| ACC              |   3 |                  18   |
| mishozuki        |   1 |                  18   |
| Kvitova          |   1 |                  18   |
| Izuki            |   2 |                  18   |
| Cem              |   1 |                  18   |
| VEDCA            |   2 |                  18   |
| Onebot           |   2 |                  13.5 |
| Fénix            |   1 |                   9   |
| Topmaq           |   1 |                   9   |


### 3.2 Cruce con ranking de fallas

| marca            |   total_encuestados |   fallas_bateria |   fallas_gomas |   fallas_motor |   total_fallas |
|:-----------------|--------------------:|-----------------:|---------------:|---------------:|---------------:|
| Raly             |                  12 |                3 |              8 |              1 |             12 |
| Jinpeng          |                   6 |                2 |              4 |              1 |              7 |
| Nippon           |                   3 |                3 |              3 |              0 |              6 |
| ACC              |                   3 |                1 |              2 |              1 |              4 |
| Oneboot          |                   1 |                1 |              1 |              0 |              2 |
| Rali (dejar así) |                   1 |                1 |              1 |              0 |              2 |
| Onebot           |                   2 |                1 |              0 |              0 |              1 |
| Oim              |                   1 |                1 |              0 |              0 |              1 |
| Cem              |                   1 |                0 |              1 |              0 |              1 |
| VEDCA            |                   2 |                0 |              1 |              0 |              1 |
| Xinger           |                   1 |                0 |              1 |              0 |              1 |
| Singer           |                   1 |                0 |              1 |              0 |              1 |
| Fénix            |                   1 |                0 |              0 |              0 |              0 |
| Kvitova          |                   1 |                0 |              0 |              0 |              0 |
| Izuki            |                   2 |                0 |              0 |              0 |              0 |
| Topmaq           |                   1 |                0 |              0 |              0 |              0 |
| mishozuki        |                   1 |                0 |              0 |              0 |              0 |



**Recomendación:** Las marcas con mayor vida útil declarada y menor incidencia de fallas son las más confiables para compra. Basado en los datos, **Jinpeng** y **ACC** muestran buen balance entre experiencia declarada y menor volumen relativo de fallas, mientras que **Raly** concentra el mayor número de quejas/fallas reportadas y debe revisarse con mayor cautela. Siempre se recomienda verificar estado de batería al momento de compra independientemente de la marca.

## SECCIÓN 4: Correlaciones Matemáticas

### 4.1 Correlación precio vs capacidad de carga

- **Coeficiente de correlación (Pearson):** -0.054
- **Interpretación:** Correlación débil; otros factores (marca, tipo, equipamiento) influyen más en el precio.

### 4.2 Correlación precio vs autonomía

- **Coeficiente de correlación (Pearson):** 0.666
- **Interpretación:** Existe una correlación moderada entre autonomía y precio.
