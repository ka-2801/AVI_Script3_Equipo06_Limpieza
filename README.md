# AVI_Script3_Eq06_Limpieza

Limpieza, validación y comparación de datos SINAICA (calidad del aire) para la estación Vallarta (VAL), Jalisco, años 2014 a 2024: de 11 archivos anuales con varias estaciones a 96,432 filas horarias validadas y estandarizadas (8,760 por año; 8,784 en años bisiestos), con estadísticas, matrices y gráficas comparativas entre años.

**Limpieza de dataset SINAICA - Estación Vallarta (VAL), 2014 a 2024**

Limpieza y estandarización de datos de calidad del aire y meteorología de la red SINAICA para la estación VAL, del 1 de enero al 31 de diciembre de cada año entre 2014 y 2024. Cada año se procesa por separado con la misma función y todos quedan con las mismas columnas, para poder compararlos.

*Contenido del repositorio*

1. `Script3_AVI.ipynb` - notebook con el script (función `limpiar_anio`, estadísticas y gráficas)
2. `BD_2014_2024/` - datasets originales (entrada): `BD_2014.xlsx` a `BD_2024.xlsx`
3. `BD_VAL_limpias/` - datasets limpios (salida): 11 archivos `BD_VAL_AAAA_limpio.xlsx` y el libro consolidado `SINAICA_VAL_2014_2024_limpio.xlsx`
4. `graficas/` - 7 gráficas comparativas entre años (PNG)
5. `Resultados.md` - comparación entre originales y limpios

*Requisitos:* Python 3, pandas, numpy, openpyxl, matplotlib (`pip install pandas numpy openpyxl matplotlib`)

*Uso:* el script se corrió en Google Colab. La primera celda descomprime `BD_2014_2024.zip`; el resto lee la carpeta `BD_2014_2024`, y escribe los resultados en `BD_VAL_limpias`.

**Datos de entrada**

| Archivo                      | Hoja   | Contenido                  |
| ---------------------------- | ------ | -------------------------- |
| `BD_2014.xlsx` a `BD_2024.xlsx` | `Data` | Un año por archivo (365 o 366 días) |

Los años 2016, 2020 y 2024 son bisiestos (8,784 horas); los demás tienen 8,760. El script toma el año del nombre del archivo y, si la hoja `Data` no existe, usa la primera hoja. Los originales no están filtrados por estación ni por el alcance del análisis, y solo se leen las columnas necesarias.

VAL solo mide O3, PM10 y PM2.5 (contaminantes) y ET, IT, RH, WS, WD, PP y UVI (meteorología).

**Qué hace el script**

1. *Carga*: busca los archivos `BD_AAAA` en la carpeta de entrada, lee la hoja `Data` y normaliza nombres de columnas (`PM2,5` y `PM25` pasan a `PM2.5`) y de `STATION`.
2. *Filtrado*: deja solo `STATION == "VAL"`.
3. *Fechas*: convierte `DATE` a fecha; si solo trae el día y `HOUR` trae la hora, los combina. Descarta fechas inválidas y registros que no son del año del archivo.
4. *Contaminantes fuera del alcance*: elimina `NO`, `NO2`, `NOX`, `SO2`, `CO`, imprimiendo un aviso si tenían datos en VAL.
5. *Alcance*: conserva identificadores y las 10 variables de interés. Si una variable no existe en un año, se crea vacía, para que los 11 años tengan la misma estructura.
6. *Tipos*: convierte mediciones a numérico (`errors="coerce"`) y los códigos `-999` y `-9999` (sin dato) pasan a `NaN`.
7. *Duplicados*: elimina fechas repetidas y conserva la primera.
8. *Consistencia temporal*: reconstruye el año completo hora por hora (8,760 u 8,784 registros); las horas faltantes quedan como fila vacía. `HOUR`, `DIA` y `MES` se derivan siempre de `DATE`.
9. *Rangos físicos*: valores fuera de rango pasan a `NaN` (O3, PM10, PM2.5, WS, PP y UVI no negativos; RH entre 0 y 100; WD entre 0 y 360).
10. *Columnas vacías*: elimina variables con 0% de datos en los 11 años a la vez.
11. *Comparación entre años*: calcula disponibilidad, estadísticos, promedios anuales, promedios mensuales de O3, PM10 y PM2.5, matriz de correlación y promedios diarios, y genera 7 gráficas.
12. *Guardado*: un archivo limpio por año (hoja `VAL_AAAA`) y un libro consolidado con una hoja por año, las hojas de análisis (`Reporte_limpieza`, `Estadisticas`, `Matriz_promedios`, `Matriz_disponibilidad`, `Matriz_correlacion`, `Mensual_O3`, `Mensual_PM10`, `Mensual_PM25`, `Promedios_diarios`) y la hoja `Graficas` con las imágenes.
13. *Resumen en terminal*: registros, validaciones y disponibilidad por año y variable.

**Resultado de la corrida documentada**

| Año  | Registros esperados / obtenidos | Horas faltantes como fila | Fechas duplicadas | Fuera de rango a NaN | Avisos de columnas eliminadas con datos                      |
| ---- | ------------------------------- | ------------------------- | ----------------- | -------------------- | ------------------------------------------------------------ |
| 2014 | 8,760 / 8,760                   | 0                         | 0                 | 0                    | `NO2` 83.3%, `SO2` 76.7%                                     |
| 2015 | 8,760 / 8,760                   | 0                         | 0                 | 0                    | `NO2` 82.9%, `SO2` 90.3%, `CO` 90.2%                         |
| 2016 | 8,784 / 8,784                   | 0                         | 0                 | 0                    | `NO2` 92.3%, `SO2` 70.9%, `CO` 71.9%                         |
| 2017 | 8,760 / 8,760                   | 0                         | 0                 | 0                    | `NO2` 82.5%, `SO2` 84.4%, `CO` 84.1%                         |
| 2018 | 8,760 / 8,760                   | 0                         | 0                 | 0                    | `NO2` 48.4%, `SO2` 84.0%, `CO` 46.0%                         |
| 2019 | 8,760 / 8,760                   | 0                         | 0                 | 0                    | `NO2` 55.9%, `SO2` 61.2%, `CO` 57.1%                         |
| 2020 | 8,784 / 8,784                   | 0                         | 0                 | 0                    | `NO2` 30.6%, `SO2` 12.5%, `CO` 94.4%                         |
| 2021 | 8,760 / 8,760                   | 0                         | 0                 | 0                    | `NO2` 55.3%, `SO2` 83.8%, `CO` 64.4%                         |
| 2022 | 8,760 / 8,760                   | 0                         | 0                 | 0                    | `SO2` 11.7%                                                  |
| 2023 | 8,760 / 8,760                   | 0                         | 0                 | 0                    | `SO2` 64.5%                                                  |
| 2024 | 8,784 / 8,784                   | 0                         | 0                 | 4                    | `NO` 31.3%, `NO2` 30.9%, `NOX` 31.3%, `CO` 24.5%             |

Columnas finales (15), iguales en los 11 años: `STATION, DATE, HOUR, DIA, MES, O3, PM10, PM2.5, ET, IT, RH, WS, WD, PP, UVI`.

Disponibilidad final por variable (% de horas con dato):

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

**Gráficas generadas**

| Archivo                                  | Contenido                                                  |
| ---------------------------------------- | ---------------------------------------------------------- |
| `01_disponibilidad.png`                  | Disponibilidad (%) por año y variable                      |
| `02_promedio_anual_contaminantes.png`    | Promedio anual de O3, PM10 y PM2.5                         |
| `03_boxplot_contaminantes.png`           | Distribución de O3, PM10 y PM2.5 por año                   |
| `04_mensual_O3.png`                      | Promedio mensual de O3 (año x mes)                         |
| `05_mensual_PM10.png`                    | Promedio mensual de PM10 (año x mes)                       |
| `06_mensual_PM25.png`                    | Promedio mensual de PM2.5 (año x mes)                      |
| `07_correlacion.png`                     | Matriz de correlación entre variables (2014-2024)          |

**Notas importantes**

*`NO`, `NO2`, `NOX`, `SO2` y `CO` se eliminan por alcance, no por falta de datos:* VAL no tiene esos sensores según la ficha `Param` de los datasets de 2023 y 2024. Sin embargo, entre 2014 y 2021 el original sí trae datos de esas columnas para VAL (hasta 94%), por lo que conviene confirmar en `Param` si la estación las medía en esos años. `ATM` y `RS` tampoco se conservan por estar fuera del alcance.

*Ninguna variable se eliminó por estar vacía en los 11 años*, pero varias están vacías en años completos: `PM2.5` tiene 0% en 2014, 2015, 2016, 2018 y 2019; `IT` en 2014 a 2018; `PP` en 2014 a 2019; y `UVI` en 2014, 2017, 2018 y 2019. Esas columnas se mantienen (vacías) para que todos los años tengan la misma estructura.

*La cobertura es desigual entre años* (2018 y 2019 son los más bajos, cerca de 48% y 62%), así que los promedios anuales no son directamente comparables entre todos los años (ver `Resultados.md`).

*El bloque de rangos físicos* corrigió 4 valores en 2024 y ninguno en los demás años. Los resultados de 2023 y 2024 coinciden con los de la corrida del Script1 y 2.
