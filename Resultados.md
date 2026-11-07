**Resultados: Diferencias entre los datasets originales y los datasets limpios (VAL, 2014 a 2024)**

*Datasets originales: `BD_2014.xlsx` a `BD_2024.xlsx`* Hoja `Data`.

| Año  | Días | Horas esperadas por estación | Filas del original | Filas de VAL en el limpio |
| ---- | ---- | ---------------------------- | ------------------ | ------------------------- |
| 2014 | 365  | 8,760                        | [completar]        | 8,760                     |
| 2015 | 365  | 8,760                        | [completar]        | 8,760                     |
| 2016 | 366  | 8,784 (año bisiesto)         | [completar]        | 8,784                     |
| 2017 | 365  | 8,760                        | [completar]        | 8,760                     |
| 2018 | 365  | 8,760                        | [completar]        | 8,760                     |
| 2019 | 365  | 8,760                        | [completar]        | 8,760                     |
| 2020 | 366  | 8,784 (año bisiesto)         | [completar]        | 8,784                     |
| 2021 | 365  | 8,760                        | [completar]        | 8,760                     |
| 2022 | 365  | 8,760                        | [completar]        | 8,760                     |
| 2023 | 365  | 8,760                        | [completar]        | 8,760                     |
| 2024 | 366  | 8,784 (año bisiesto)         | [completar]        | 8,784                     |

1. Son 11 archivos, uno por año, con datos de varias estaciones de la red SINAICA.
2. No están filtrados por estación ni por el alcance del análisis.
3. Cada archivo se lee por separado y el año se toma del nombre del archivo.

*Datasets limpios: `BD_VAL_AAAA_limpio.xlsx` (hoja `VAL_AAAA`) y `SINAICA_VAL_2014_2024_limpio.xlsx` (libro consolidado)*

1. Una sola estación (VAL): 96,432 filas en total (8 años de 8,760 y 3 años bisiestos de 8,784).
2. 15 columnas idénticas y en el mismo orden en los 11 años: `STATION`, `DATE`, `HOUR`, `DIA`, `MES`, `O3`, `PM10`, `PM2.5`, `ET`, `IT`, `RH`, `WS`, `WD`, `PP`, `UVI`.
3. Tipos estandarizados: mediciones en numérico, códigos `-999` y `-9999` convertidos a `NaN`, `HOUR`/`DIA`/`MES` en entero y derivados de `DATE`.
4. Secuencia horaria completa, sin huecos ni duplicados, y con rangos físicos validados.
5. El libro consolidado incluye una hoja por año y hojas de análisis: `Reporte_limpieza`, `Estadisticas`, `Matriz_promedios`, `Matriz_disponibilidad`, `Matriz_correlacion`, `Mensual_O3`, `Mensual_PM10`, `Mensual_PM25`, `Promedios_diarios` y `Graficas`.

*Qué se eliminó*

| Columnas eliminadas                   | Motivo                                                                                                                                                                                         |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `NO`, `NO2`, `NOX`, `SO2`, `CO`       | VAL no tiene esos sensores según `Param` (2023 y 2024). Con datos en el original: ver tabla siguiente.                                                                                         |
| `ATM`, `RS`                           | Fuera del alcance (presión atmosférica y radiación solar); el script no las conserva.                                                                                                          |
| Variables del alcance con 0% de datos | Ninguna se eliminó: las 10 variables tienen datos en al menos un año. Cuando una variable está vacía en un año, la columna se mantiene vacía para que los 11 años tengan la misma estructura. |

Porcentaje de datos que traían en VAL las columnas eliminadas (`-` = 0% o sin aviso):

| Año  | `NO`  | `NO2` | `NOX` | `SO2` | `CO`  |
| ---- | ----- | ----- | ----- | ----- | ----- |
| 2014 | -     | 83.3% | -     | 76.7% | -     |
| 2015 | -     | 82.9% | -     | 90.3% | 90.2% |
| 2016 | -     | 92.3% | -     | 70.9% | 71.9% |
| 2017 | -     | 82.5% | -     | 84.4% | 84.1% |
| 2018 | -     | 48.4% | -     | 84.0% | 46.0% |
| 2019 | -     | 55.9% | -     | 61.2% | 57.1% |
| 2020 | -     | 30.6% | -     | 12.5% | 94.4% |
| 2021 | -     | 55.3% | -     | 83.8% | 64.4% |
| 2022 | -     | -     | -     | 11.7% | -     |
| 2023 | -     | -     | -     | 64.5% | -     |
| 2024 | 31.3% | 30.9% | 31.3% | -     | 24.5% |

Entre 2014 y 2021 estas columnas traen bastantes datos para VAL, lo que no concuerda del todo con la ficha técnica de 2023 y 2024. Se eliminaron por quedar fuera del alcance.

*Correcciones y validaciones*

| Año  | Registros esperados vs. obtenidos | Horas faltantes / duplicados | Valores fuera de rango a NaN |
| ---- | --------------------------------- | ---------------------------- | ---------------------------- |
| 2014 | 8,760 vs. 8,760                   | 0 / 0                        | 0                            |
| 2015 | 8,760 vs. 8,760                   | 0 / 0                        | 0                            |
| 2016 | 8,784 vs. 8,784                   | 0 / 0                        | 0                            |
| 2017 | 8,760 vs. 8,760                   | 0 / 0                        | 0                            |
| 2018 | 8,760 vs. 8,760                   | 0 / 0                        | 0                            |
| 2019 | 8,760 vs. 8,760                   | 0 / 0                        | 0                            |
| 2020 | 8,784 vs. 8,784                   | 0 / 0                        | 0                            |
| 2021 | 8,760 vs. 8,760                   | 0 / 0                        | 0                            |
| 2022 | 8,760 vs. 8,760                   | 0 / 0                        | 0                            |
| 2023 | 8,760 vs. 8,760                   | 0 / 0                        | 0                            |
| 2024 | 8,784 vs. 8,784                   | 0 / 0                        | 4                            |

Los únicos valores corregidos por rango físico son 4 en 2024, que coinciden con las 4 horas de `RH` mayor a 100% (máx. 100.1) detectadas en la corrida del Script2; ahora pasan a `NaN`. Los resultados de 2023 y 2024 coinciden con los de esa corrida.

*Disponibilidad de datos en el dataset limpio (% de horas con dato)*

| Año  | O3   | PM10 | PM2.5 | ET   | IT   | RH   | WS   | WD   | PP   | UVI  |
| ---- | ---- | ---- | ----- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| 2014 | 97.6 | 95.7 | 0.0   | 97.8 | 0.0  | 98.0 | 98.0 | 62.5 | 0.0  | 0.0  |
| 2015 | 99.1 | 98.4 | 0.0   | 99.5 | 0.0  | 99.5 | 99.5 | 99.5 | 0.0  | 99.5 |
| 2016 | 95.3 | 44.2 | 0.0   | 99.8 | 0.0  | 99.8 | 99.8 | 99.8 | 0.0  | 99.8 |
| 2017 | 81.6 | 58.0 | 27.0  | 84.8 | 0.0  | 84.8 | 84.8 | 84.8 | 0.0  | 0.0  |
| 2018 | 48.3 | 47.9 | 0.0   | 48.6 | 0.0  | 48.6 | 48.6 | 48.6 | 0.0  | 0.0  |
| 2019 | 62.0 | 50.1 | 0.0   | 62.0 | 61.9 | 62.0 | 62.0 | 62.0 | 0.0  | 0.0  |
| 2020 | 91.2 | 93.4 | 4.3   | 97.1 | 99.0 | 97.1 | 99.2 | 97.3 | 99.7 | 86.4 |
| 2021 | 89.0 | 80.7 | 2.7   | 96.3 | 96.5 | 99.3 | 99.1 | 96.4 | 99.3 | 99.3 |
| 2022 | 88.4 | 44.0 | 27.1  | 14.3 | 96.2 | 77.2 | 77.2 | 14.3 | 86.7 | 97.6 |
| 2023 | 59.5 | 70.9 | 59.3  | 82.5 | 79.6 | 82.5 | 84.3 | 52.8 | 45.9 | 40.9 |
| 2024 | 92.0 | 91.7 | 63.1  | 92.2 | 92.5 | 50.3 | 87.6 | 50.2 | 48.1 | 28.8 |

La cobertura es muy desigual entre años y variables:

1. *Años con mejor cobertura:* 2015 (O3 99.1% y PM10 98.4%), 2014 y 2020. 
*Años con menor cobertura:* 2018 (cerca de 48% en casi todas las variables) y 2019 (cerca de 62%).
2. *PM2.5* no tiene datos en 2014, 2015, 2016, 2018 y 2019, y es muy baja en 2020 (4.3%) y 2021 (2.7%). Solo 2023 (59.3%) y 2024 (63.1%) superan la mitad de las horas.
3. *IT* no tiene datos de 2014 a 2018 y *PP* no tiene de 2014 a 2019; ambas aparecen completas a partir de 2020. *UVI* no tiene datos en 2014, 2017, 2018 ni 2019.
4. *2022* tiene `ET` y `WD` en solo 14.3% y `PM10` en 44.0%, aunque `IT`, `PP` y `UVI` están por encima de 85%. *2016* tiene `PM10` en 44.2% con el resto de variables casi completas.
5. *RH* y *WD* bajan a cerca de 50% en 2024, y *UVI* a 28.8%.

Por esto, las medias anuales de las variables con huecos largos no son directamente comparables entre años: un promedio con 4% de las horas y otro con 99% no representan el mismo periodo. Los huecos suelen ser periodos continuos, así que conviene revisar los promedios mensuales (`Mensual_O3`, `Mensual_PM10` y `Mensual_PM25`) antes de interpretar tendencias.

*Estadísticas y gráficas de comparación entre años*

Además de la limpieza, el script genera, a partir de los 11 datasets limpios:

1. *Estadísticos por año y variable* (hoja `Estadisticas`): datos válidos, disponibilidad, media, mediana, desviación estándar, mínimo, percentil 95 y máximo.
2. *Matrices* (hojas `Matriz_promedios`, `Matriz_disponibilidad`, `Matriz_correlacion` y `Mensual_*`): promedio anual, disponibilidad, correlación entre variables y promedio mensual de O3, PM10 y PM2.5 (año x mes).
3. *Promedios diarios* por día y año (hoja `Promedios_diarios`).
4. *Gráficas* (carpeta `graficas/`, también insertadas en la hoja `Graficas`):

| Archivo                               | Contenido                                         |
| ------------------------------------- | ------------------------------------------------- |
| `01_disponibilidad.png`               | Disponibilidad (%) por año y variable             |
| `02_promedio_anual_contaminantes.png` | Promedio anual de O3, PM10 y PM2.5                |
| `03_boxplot_contaminantes.png`        | Distribución de O3, PM10 y PM2.5 por año          |
| `04_mensual_O3.png`                   | Promedio mensual de O3 (año x mes)                |
| `05_mensual_PM10.png`                 | Promedio mensual de PM10 (año x mes)              |
| `06_mensual_PM25.png`                 | Promedio mensual de PM2.5 (año x mes)             |
| `07_correlacion.png`                  | Matriz de correlación entre variables (2014-2024) |


**Resumen** Los datasets originales son 11 bases crudas (2014 a 2024) con datos de varias estaciones. Los limpios son el subconjunto exacto para VAL: 96,432 filas horarias (8,760 por año y 8,784 en bisiestos), restringidas a las 10 variables del alcance, con tipos estandarizados, secuencia horaria completa y validaciones de duplicados y rangos físicos. Los 11 años tienen la misma estructura (15 columnas), por lo que se pueden combinar y comparar, y el script agrega estadísticas, matrices y 7 gráficas comparativas. La limitación principal es la cobertura: años completos sin datos de `PM2.5`, `IT`, `PP` o `UVI`, años con cobertura baja (2018 y 2019) y valores atípicos pendientes de tratar.
