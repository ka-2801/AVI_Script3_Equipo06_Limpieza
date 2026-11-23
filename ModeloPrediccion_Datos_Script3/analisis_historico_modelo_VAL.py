# -*- coding: utf-8 -*-
"""
RECONSTRUCCIÓN DEL PIPELINE DE ANÁLISIS HISTÓRICO Y MODELO PREDICTIVO DE PM10
Estación VAL (SINAICA) — periodo 2014-2024 — Sprint 3

Qué hace este script (de principio a fin):
  1. Lee las hojas anuales del Excel original (SINAICA_VAL_2014_2024_limpio.xlsx).
  2. Limpia / normaliza fechas y consolida el histórico en una malla horaria completa.
  3. Genera variables temporales, disponibilidad y estadísticas descriptivas.
  4. Construye variables de entrada (lags, variables cíclicas) y objetivos (+1h, +2h, +3h).
  5. Entrena tres modelos HistGradientBoostingRegressor (uno por horizonte),
     con separación temporal: entrenamiento <= 2023, prueba = 2024.
  6. Evalúa (MAE, RMSE, R²) contra un modelo base de persistencia.
  7. Exporta un Excel con las mismas 14 hojas del archivo de referencia.
  8. (Opcional) VALIDA el resultado contra el Excel procesado de referencia,
     hoja por hoja, y reporta diferencias reales (no copia valores).

IMPORTANTE: este código es una RECONSTRUCCIÓN reproducible. No es el código original
recuperado; se verificó que sus resultados coinciden con el Excel de referencia.

Uso:
    python analisis_historico_modelo_VAL.py
    python analisis_historico_modelo_VAL.py --entrada datos/SINAICA_VAL_2014_2024_limpio.xlsx \
        --referencia datos/Sprint3_Analisis_Historico_Modelo_VAL.xlsx --salida resultados
"""

# ----------------------------------------------------------------------------
# 1. IMPORTACIÓN DE BIBLIOTECAS
# ----------------------------------------------------------------------------
import argparse
import sys
import warnings
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

warnings.filterwarnings("ignore")

# ----------------------------------------------------------------------------
# 2. CONFIGURACIÓN (todo lo ajustable vive aquí; no hay rutas absolutas)
# ----------------------------------------------------------------------------
RANDOM_STATE = 42

# Nombres de archivo por defecto (relativos a la carpeta desde donde se ejecuta)
ARCHIVO_ENTRADA_DEFECTO = "SINAICA_VAL_2014_2024_limpio.xlsx"
ARCHIVO_REFERENCIA_DEFECTO = "Sprint3_Analisis_Historico_Modelo_VAL.xlsx"
CARPETA_SALIDA_DEFECTO = "salida_VAL"
NOMBRE_EXCEL_SALIDA = "Sprint3_Analisis_Historico_Modelo_VAL.xlsx"

ANIO_INICIO = 2014
ANIO_FIN = 2024
ANIO_ENTRENAMIENTO_HASTA = 2023   # entrenamiento: ANIO <= 2023
ANIO_PRUEBA = 2024                # prueba: ANIO == 2024

COLUMNAS_REQUERIDAS = ["STATION", "DATE", "HOUR", "DIA", "MES", "O3", "PM10", "PM2.5",
                       "ET", "IT", "RH", "WS", "WD", "PP", "UVI"]
VARIABLES_MEDICION = ["O3", "PM10", "PM2.5", "ET", "IT", "RH", "WS", "WD", "PP", "UVI"]
CONTAMINANTES = ["O3", "PM10", "PM2.5"]

# Estación del año por mes (clasificación meteorológica simple, verificada en la referencia)
ESTACION_POR_MES = {12: "Invierno", 1: "Invierno", 2: "Invierno",
                    3: "Primavera", 4: "Primavera", 5: "Primavera",
                    6: "Verano", 7: "Verano", 8: "Verano",
                    9: "Otoño", 10: "Otoño", 11: "Otoño"}

# Modelo
HORIZONTES = [1, 2, 3]                       # horas hacia el futuro
LAGS_HORAS = [1, 2, 3, 6, 12, 24]            # rezagos de PM10
FEATURES = (["PM10"] + [f"PM10_LAG_{h}H" for h in LAGS_HORAS]
            + ["HORA_SEN", "HORA_COS", "MES_SEN", "MES_COS", "DIA_SEMANA"])   # 12 variables
TARGETS = [f"PM10_OBJ_{h}H" for h in HORIZONTES]
PARAMETROS_MODELO = dict(max_iter=100, max_leaf_nodes=15, l2_regularization=1.0,
                         random_state=RANDOM_STATE)

# Orden exacto de las 14 hojas del Excel de referencia
HOJAS_SALIDA = ["Resumen", "Historico_horario", "Disponibilidad", "Estadisticas_anuales",
                "Estadisticas_mensuales", "Estadisticas_horarias", "Estadisticas_estacionales",
                "Promedios_diarios", "Correlaciones", "Dataset_modelo_completo",
                "Dataset_modelo_utilizable", f"Predicciones_{ANIO_PRUEBA}", "Metricas_modelo",
                "Diccionario_variables"]

# Tolerancias para la validación contra la referencia
TOL_ESTADISTICAS = 1e-9
TOL_MODELO = 1e-6


def mensaje(texto):
    """Imprime un mensaje de progreso."""
    print(texto, flush=True)


# ----------------------------------------------------------------------------
# 3. CARGA DE DATOS
# ----------------------------------------------------------------------------
def validar_archivo(ruta, descripcion):
    """Comprueba que el archivo exista y sea un .xlsx; devuelve la ruta como Path."""
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró {descripcion}: {ruta.resolve()}")
    if ruta.suffix.lower() not in (".xlsx", ".xlsm"):
        raise ValueError(f"{descripcion} debe ser un Excel (.xlsx): {ruta}")
    return ruta


def listar_hojas_anuales(ruta_excel, anio_inicio=ANIO_INICIO, anio_fin=ANIO_FIN):
    """Devuelve las hojas cuyo nombre es un año del rango (p. ej. '2014'...'2024').
    Ignora hojas auxiliares (Reporte_limpieza, Estadisticas, Matriz_*, Graficas)."""
    nombres = pd.ExcelFile(ruta_excel).sheet_names
    anuales = [n for n in nombres if str(n).isdigit() and anio_inicio <= int(n) <= anio_fin]
    faltantes = [a for a in range(anio_inicio, anio_fin + 1) if str(a) not in anuales]
    if faltantes:
        raise ValueError(f"Faltan hojas anuales en el archivo original: {faltantes}")
    return sorted(anuales, key=int)


def cargar_datos_originales(ruta_excel):
    """Lee cada hoja anual y valida que existan las columnas necesarias."""
    ruta_excel = validar_archivo(ruta_excel, "el Excel de datos originales")
    hojas = {}
    for nombre in listar_hojas_anuales(ruta_excel):
        df = pd.read_excel(ruta_excel, sheet_name=nombre)
        faltan = [c for c in COLUMNAS_REQUERIDAS if c not in df.columns]
        if faltan:
            raise KeyError(f"La hoja {nombre} no tiene las columnas: {faltan}")
        hojas[int(nombre)] = df[COLUMNAS_REQUERIDAS].copy()
        mensaje(f"  Hoja {nombre}: {len(df):,} filas leídas")
    return hojas


# ----------------------------------------------------------------------------
# 4. INSPECCIÓN INICIAL
# ----------------------------------------------------------------------------
def inspeccion_inicial(hojas):
    """Resumen por hoja: filas, fechas, duplicados, saltos temporales y nulos por variable."""
    filas = []
    for anio, df in hojas.items():
        fechas = pd.to_datetime(df["DATE"], errors="coerce")
        esperadas = 8784 if pd.Timestamp(year=anio, month=1, day=1).is_leap_year else 8760
        saltos = int((fechas.sort_values().diff().dropna() != pd.Timedelta(hours=1)).sum())
        fila = {"ANIO": anio, "FILAS": len(df), "FILAS_ESPERADAS": esperadas,
                "FECHAS_NULAS": int(fechas.isna().sum()),
                "DUPLICADOS_DATE": int(fechas.duplicated().sum()),
                "SALTOS_NO_HORARIOS": saltos,
                "FECHA_MIN": fechas.min(), "FECHA_MAX": fechas.max(),
                "ESTACIONES": ",".join(sorted(df["STATION"].dropna().astype(str).unique()))}
        for var in VARIABLES_MEDICION:
            fila[f"NULOS_{var}_%"] = round(float(df[var].isna().mean() * 100), 2)
        filas.append(fila)
    informe = pd.DataFrame(filas)
    mensaje(f"  Años: {informe['ANIO'].min()}-{informe['ANIO'].max()} | "
            f"filas totales: {informe['FILAS'].sum():,} | "
            f"duplicados: {informe['DUPLICADOS_DATE'].sum()} | "
            f"saltos no horarios: {informe['SALTOS_NO_HORARIOS'].sum()}")
    return informe


# ----------------------------------------------------------------------------
# 5. LIMPIEZA Y NORMALIZACIÓN
# ----------------------------------------------------------------------------
def limpiar_y_normalizar(hojas):
    """Normaliza fechas y tipos de las hojas anuales y las concatena.

    Reglas (todas verificables en el Excel de referencia):
      * DATE ya trae la hora; DATETIME = DATE. Solo si DATE no tuviera hora (todo a
        medianoche) se sumaría HOUR. Nunca se suma dos veces.
      * Valores no numéricos -> NaN. NO se imputa ni se inventa ninguna medición.
      * Se eliminan filas con fecha inválida, fuera del año de su hoja y duplicados.
    """
    bloques, reporte = [], []
    for anio, df in hojas.items():
        df = df.copy()
        df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
        invalidas = int(df["DATE"].isna().sum())
        df = df.dropna(subset=["DATE"])

        solo_medianoche = (df["DATE"].dt.hour == 0).all() and df["HOUR"].max() > 0
        if solo_medianoche:
            df["DATETIME"] = df["DATE"] + pd.to_timedelta(df["HOUR"], unit="h")
            mensaje(f"  {anio}: DATE sin hora; se construyó DATETIME = DATE + HOUR")
        else:
            df["DATETIME"] = df["DATE"]

        fuera = int((df["DATETIME"].dt.year != anio).sum())
        df = df[df["DATETIME"].dt.year == anio]

        for var in VARIABLES_MEDICION:
            df[var] = pd.to_numeric(df[var], errors="coerce")
        bloques.append(df)
        reporte.append({"ANIO": anio, "FECHAS_INVALIDAS": invalidas, "FILAS_FUERA_DE_ANIO": fuera,
                        "DATE_SIN_HORA": bool(solo_medianoche)})

    consolidado = pd.concat(bloques, ignore_index=True)
    duplicados = int(consolidado.duplicated(subset="DATETIME").sum())
    consolidado = consolidado.drop_duplicates(subset="DATETIME", keep="first")
    estaciones = consolidado["STATION"].dropna().unique()
    if len(estaciones) > 1:
        mensaje(f"  AVISO: hay varias estaciones en los datos: {list(estaciones)}")
    mensaje(f"  Registros tras limpieza: {len(consolidado):,} | duplicados eliminados: {duplicados}")
    return consolidado, pd.DataFrame(reporte), duplicados


# ----------------------------------------------------------------------------
# 6. CONSOLIDACIÓN HISTÓRICA
# ----------------------------------------------------------------------------
def consolidar_malla_horaria(df):
    """Ordena cronológicamente y reindexa a una malla horaria COMPLETA.
    Las horas faltantes quedan como filas con NaN (no se interpolan)."""
    df = df.sort_values("DATETIME").set_index("DATETIME")
    inicio = pd.Timestamp(year=df.index.min().year, month=1, day=1, hour=0)
    fin = pd.Timestamp(year=df.index.max().year, month=12, day=31, hour=23)
    malla = pd.date_range(inicio, fin, freq="h", name="DATETIME")
    faltantes = len(malla.difference(df.index))
    df = df.reindex(malla)
    estacion = df["STATION"].dropna().iloc[0]
    df["STATION"] = df["STATION"].fillna(estacion)
    df["DATE"] = df.index
    df["HOUR"] = df.index.hour
    df["DIA"] = df.index.day
    df["MES"] = df.index.month
    df = df.reset_index()
    orden = ["DATETIME", "STATION", "DATE", "HOUR", "DIA", "MES"] + VARIABLES_MEDICION
    mensaje(f"  Malla horaria: {len(df):,} horas | horas faltantes como fila: {faltantes}")
    return df[orden], faltantes


def agregar_variables_temporales(df):
    """Año, hora, día de la semana (lunes=0), día del año y estación del año."""
    df = df.copy()
    df["ANIO"] = df["DATETIME"].dt.year
    df["HORA"] = df["DATETIME"].dt.hour
    df["DIA_SEMANA"] = df["DATETIME"].dt.dayofweek
    df["DIA_ANIO"] = df["DATETIME"].dt.dayofyear
    df["ESTACION"] = df["MES"].map(ESTACION_POR_MES)
    return df


def calcular_disponibilidad(df):
    """N° de datos válidos y % de disponibilidad por año y variable."""
    esperados = df.groupby("ANIO").size().rename("REGISTROS_ESPERADOS")
    validos = df.groupby("ANIO")[VARIABLES_MEDICION].count()
    porcentaje = validos.div(esperados, axis=0).mul(100).round(2)
    validos.columns = [f"{c}_N_VALIDOS" for c in validos.columns]
    porcentaje.columns = [f"{c}_DISPONIBILIDAD_%" for c in porcentaje.columns]
    return pd.concat([esperados, validos, porcentaje], axis=1).reset_index()


# ----------------------------------------------------------------------------
# 7-8. ESTADÍSTICAS
# ----------------------------------------------------------------------------
def _aplanar(tabla):
    tabla.columns = [f"{variable}_{estadistico}" for variable, estadistico in tabla.columns]
    return tabla.reset_index()


def p95(serie):
    return serie.quantile(0.95)


def estadisticas_anuales(df):
    """count, mean, median, std, min, p95 y max por año."""
    f = ["count", "mean", "median", "std", "min", p95, "max"]
    return _aplanar(df.groupby("ANIO")[VARIABLES_MEDICION].agg(f))


def estadisticas_mensuales(df):
    f = ["count", "mean", "median", "std", "min", "max"]
    return _aplanar(df.groupby(["ANIO", "MES"])[VARIABLES_MEDICION].agg(f))


def estadisticas_horarias(df):
    f = ["count", "mean", "median", "std", "min", "max"]
    return _aplanar(df.groupby("HORA")[VARIABLES_MEDICION].agg(f))


def estadisticas_estacionales(df):
    f = ["count", "mean", "median", "std"]
    return _aplanar(df.groupby("ESTACION")[VARIABLES_MEDICION].agg(f))


def promedios_diarios(df):
    """Promedio diario de cada variable (los NaN se ignoran en el promedio)."""
    d = df.set_index("DATETIME")[VARIABLES_MEDICION].resample("D").mean().reset_index()
    d.insert(1, "ANIO", d["DATETIME"].dt.year)
    return d


def matriz_correlacion(df):
    """Correlación de Pearson (por pares, ignorando NaN) sobre datos horarios."""
    c = df[VARIABLES_MEDICION].corr()
    c.index.name = "VARIABLE"
    return c.reset_index()


# ----------------------------------------------------------------------------
# 9-10. INGENIERÍA DE CARACTERÍSTICAS Y OBJETIVOS
# ----------------------------------------------------------------------------
def construir_features(hist):
    """Variables de entrada: PM10 actual, lags (por desplazamiento sobre la malla
    horaria completa, por lo que 'lag 3' es SIEMPRE 3 horas reales atrás) y codificación
    cíclica de hora y mes: sen(2π·x/periodo), cos(2π·x/periodo)."""
    d = pd.DataFrame({"DATETIME": hist["DATETIME"], "PM10": hist["PM10"],
                      "ANIO": hist["ANIO"], "MES": hist["MES"], "DIA": hist["DIA"],
                      "HORA": hist["HORA"], "DIA_SEMANA": hist["DIA_SEMANA"],
                      "DIA_ANIO": hist["DIA_ANIO"]})
    for h in LAGS_HORAS:
        d[f"PM10_LAG_{h}H"] = d["PM10"].shift(h)       # valor de hace h horas (pasado)
    d["HORA_SEN"] = np.sin(2 * np.pi * d["HORA"] / 24)
    d["HORA_COS"] = np.cos(2 * np.pi * d["HORA"] / 24)
    d["MES_SEN"] = np.sin(2 * np.pi * d["MES"] / 12)
    d["MES_COS"] = np.cos(2 * np.pi * d["MES"] / 12)
    return d


def construir_objetivos(d):
    """Objetivos: PM10 dentro de h horas (desplazamiento NEGATIVO = futuro).
    Las variables de entrada solo usan t, t-1, ... t-24; el objetivo es t+h."""
    d = d.copy()
    for h in HORIZONTES:
        d[f"PM10_OBJ_{h}H"] = d["PM10"].shift(-h)
    columnas = (["DATETIME", "PM10", "ANIO", "MES", "DIA", "HORA", "DIA_SEMANA", "DIA_ANIO"]
                + [f"PM10_LAG_{h}H" for h in LAGS_HORAS] + TARGETS
                + ["HORA_SEN", "HORA_COS", "MES_SEN", "MES_COS"])
    return d[columnas]


def seleccionar_utilizable(dataset_completo):
    """Filas con las 12 variables de entrada y los 3 objetivos presentes."""
    return dataset_completo.dropna(subset=FEATURES + TARGETS).reset_index(drop=True)


# ----------------------------------------------------------------------------
# 11-13. ENTRENAMIENTO, EVALUACIÓN Y PREDICCIONES
# ----------------------------------------------------------------------------
def dividir_temporal(dataset, horizonte):
    """Separación temporal (NO aleatoria). Para cada horizonte se exige que existan las
    12 variables de entrada y el objetivo de ESE horizonte."""
    objetivo = f"PM10_OBJ_{horizonte}H"
    base = dataset.dropna(subset=FEATURES + [objetivo])
    entrenamiento = base[base["ANIO"] <= ANIO_ENTRENAMIENTO_HASTA]
    prueba = base[base["ANIO"] == ANIO_PRUEBA]
    # Controles anti-fuga: ninguna fila de 2024 en entrenamiento y sin solape de índices
    assert entrenamiento["DATETIME"].dt.year.max() <= ANIO_ENTRENAMIENTO_HASTA
    assert prueba["DATETIME"].dt.year.min() == ANIO_PRUEBA
    assert entrenamiento["DATETIME"].max() < prueba["DATETIME"].min()
    assert len(entrenamiento) > 0 and len(prueba) > 0, "Conjunto de entrenamiento o prueba vacío"
    return entrenamiento, prueba, objetivo


def calcular_metricas(y_real, y_pred):
    return {"MAE": float(mean_absolute_error(y_real, y_pred)),
            "RMSE": float(np.sqrt(mean_squared_error(y_real, y_pred))),
            "R2": float(r2_score(y_real, y_pred))}


def entrenar_y_evaluar(dataset_completo):
    """Entrena un modelo por horizonte y evalúa en 2024. Devuelve métricas, predicciones,
    modelos e información adicional del entrenamiento."""
    filas_metricas, tablas_pred, modelos, info = [], [], {}, []
    for h in HORIZONTES:
        entrenamiento, prueba, objetivo = dividir_temporal(dataset_completo, h)
        modelo = HistGradientBoostingRegressor(**PARAMETROS_MODELO)
        modelo.fit(entrenamiento[FEATURES], entrenamiento[objetivo])
        prediccion = modelo.predict(prueba[FEATURES])
        real = prueba[objetivo]
        m = calcular_metricas(real, prediccion)
        # Modelo base de persistencia: "PM10 dentro de h horas = PM10 ahora"
        mb = calcular_metricas(real, prueba["PM10"])
        etiqueta = f"+{h} hora" if h == 1 else f"+{h} horas"
        filas_metricas.append({"HORIZON": etiqueta, "N_ENTRENAMIENTO": len(entrenamiento),
                               f"N_PRUEBA_{ANIO_PRUEBA}": len(prueba),
                               "MAE": m["MAE"], "RMSE": m["RMSE"], "R2": m["R2"],
                               "MAE_BASELINE_PERSISTENCIA": mb["MAE"],
                               "RMSE_BASELINE_PERSISTENCIA": mb["RMSE"],
                               "R2_BASELINE_PERSISTENCIA": mb["R2"]})
        tabla = pd.DataFrame({"DATETIME": prueba["DATETIME"].values})
        if h == 1:   # la columna ORIGEN se toma del conjunto +1h (igual que la referencia)
            tabla["PM10_OBSERVADO_ORIGEN"] = prueba["PM10"].values
        tabla[f"PM10_OBSERVADO_MAS_{h}H"] = real.values
        tabla[f"PM10_PREDICHO_MAS_{h}H"] = prediccion
        tabla[f"ERROR_MAS_{h}H"] = real.values - prediccion      # observado - predicho
        tablas_pred.append(tabla)
        modelos[h] = modelo
        info.append({"HORIZONTE_H": h, "ITERACIONES_USADAS": int(modelo.n_iter_),
                     "MAX_ITER": PARAMETROS_MODELO["max_iter"],
                     "ENTRENAMIENTO_DESDE": entrenamiento["DATETIME"].min(),
                     "ENTRENAMIENTO_HASTA": entrenamiento["DATETIME"].max(),
                     "PRUEBA_DESDE": prueba["DATETIME"].min(),
                     "PRUEBA_HASTA": prueba["DATETIME"].max()})
        mensaje(f"  +{h}h | N_train={len(entrenamiento):,} N_test={len(prueba):,} | "
                f"MAE={m['MAE']:.3f} RMSE={m['RMSE']:.3f} R2={m['R2']:.3f} | "
                f"persistencia R2={mb['R2']:.3f} | iteraciones={modelo.n_iter_}")

    predicciones = tablas_pred[0]
    for t in tablas_pred[1:]:
        predicciones = predicciones.merge(t, on="DATETIME", how="outer")
    predicciones = predicciones.sort_values("DATETIME").reset_index(drop=True)
    return pd.DataFrame(filas_metricas), predicciones, modelos, pd.DataFrame(info)


def sensibilidad_frontera(dataset_completo):
    """Análisis de sensibilidad: en el corte 2023/2024 las últimas 1-3 horas de 2023 tienen
    como OBJETIVO una medición de 2024. Se reentrena excluyéndolas ('purga') y se compara."""
    corte = pd.Timestamp(year=ANIO_PRUEBA, month=1, day=1)
    filas = []
    for h in HORIZONTES:
        entrenamiento, prueba, objetivo = dividir_temporal(dataset_completo, h)
        purgado = entrenamiento[entrenamiento["DATETIME"] + pd.Timedelta(hours=h) < corte]
        modelo = HistGradientBoostingRegressor(**PARAMETROS_MODELO).fit(purgado[FEATURES], purgado[objetivo])
        m = calcular_metricas(prueba[objetivo], modelo.predict(prueba[FEATURES]))
        filas.append({"HORIZONTE_H": h, "FILAS_PURGADAS": len(entrenamiento) - len(purgado),
                      "MAE_PURGADO": m["MAE"], "RMSE_PURGADO": m["RMSE"], "R2_PURGADO": m["R2"]})
    return pd.DataFrame(filas)


# ----------------------------------------------------------------------------
# 14. TEXTOS DE DOCUMENTACIÓN INCLUIDOS EN EL EXCEL
# ----------------------------------------------------------------------------
def generar_resumen(hist, disp):
    """Hoja 'Resumen'. Las cifras se calculan; los textos describen decisiones del Sprint 3."""
    glob = hist[CONTAMINANTES].notna().mean() * 100
    anios_pm10 = int((disp["PM10_N_VALIDOS"] > 0).sum())
    filas = [
        ("Periodo analizado", f"{hist['DATETIME'].min():%Y-%m-%d %H:%M} a {hist['DATETIME'].max():%Y-%m-%d %H:%M}"),
        ("Estación", "VAL (campo STATION)"),
        ("Registros horarios esperados", len(hist)),
        ("Duplicados temporales en consolidado", int(hist["DATETIME"].duplicated().sum())),
        ("PM10 disponibilidad global (%)", round(float(glob["PM10"]), 2)),
        ("O3 disponibilidad global (%)", round(float(glob["O3"]), 2)),
        ("PM2.5 disponibilidad global (%)", round(float(glob["PM2.5"]), 2)),
        ("Contaminante seleccionado para modelo", "PM10"),
        ("Justificación", f"PM10 presenta registros en los {anios_pm10} años. PM2.5 tiene disponibilidad nula en "
                          "varios años y baja cobertura en otros, por lo que no permite una serie histórica "
                          "continua comparable."),
        ("Modelo inicial", "HistGradientBoostingRegressor, entrenado por separado para +1, +2 y +3 horas."),
        ("Variables del modelo", "PM10 actual y rezagos de 1, 2, 3, 6, 12 y 24 horas; hora, mes y día de semana."),
        ("División temporal", f"Entrenamiento con registros hasta {ANIO_ENTRENAMIENTO_HASTA}; prueba con registros de {ANIO_PRUEBA}."),
        ("Meteorología", "No se incluyó en el primer modelo debido a su disponibilidad irregular; puede evaluarse en una segunda versión."),
        ("Limitación principal", "La disponibilidad de PM10 es desigual: algunos años tienen cerca de 44–50% de cobertura. "
                                 "Esto puede sesgar las comparaciones históricas y reduce los datos útiles para entrenamiento."),
    ]
    return pd.DataFrame(filas, columns=["ASPECTO", "RESULTADO"])


def generar_diccionario_hoja():
    """Hoja 'Diccionario_variables' (texto de la referencia)."""
    filas = [
        ("DATETIME", "Fecha y hora completa del registro; DATE ya contiene la hora, no se debe volver a sumar HOUR."),
        ("ANIO, MES, DIA, HORA", "Componentes temporales extraídos de DATETIME."),
        ("DIA_SEMANA", "Día de la semana (lunes=0)."),
        ("DIA_ANIO", "Número de día dentro del año."),
        ("ESTACION", "Clasificación meteorológica simple por mes: invierno, primavera, verano, otoño."),
        ("PM10_LAG_1H ... PM10_LAG_24H", "Concentraciones previas de PM10 mediante desplazamiento horario."),
        ("PM10_OBJ_1H, PM10_OBJ_2H, PM10_OBJ_3H", "Valores objetivo que el modelo intenta predecir a 1, 2 y 3 horas."),
        ("HORA_SEN/COS, MES_SEN/COS", "Codificación cíclica de hora y mes para representar su continuidad."),
        ("ERROR_MAS_nH", "Observado futuro menos predicho; positivo indica subestimación y negativo sobreestimación."),
    ]
    return pd.DataFrame(filas, columns=["CAMPO", "DESCRIPCION"])


# ----------------------------------------------------------------------------
# 7. GRÁFICAS (devuelven la figura; el script las guarda, el notebook las muestra)
# ----------------------------------------------------------------------------
def _plt():
    import matplotlib.pyplot as plt
    return plt


def grafica_disponibilidad(disp):
    plt = _plt()
    fig, ax = plt.subplots(figsize=(10, 4.5))
    for var, estilo in [("PM10", "o-"), ("O3", "s--"), ("PM2.5", "^:")]:
        ax.plot(disp["ANIO"], disp[f"{var}_DISPONIBILIDAD_%"], estilo, label=var)
    ax.set_title("Disponibilidad anual de contaminantes - estación VAL")
    ax.set_xlabel("Año"); ax.set_ylabel("Datos válidos (%)"); ax.set_ylim(0, 105)
    ax.set_xticks(disp["ANIO"]); ax.grid(alpha=.3); ax.legend()
    fig.tight_layout()
    return fig


def grafica_heatmap_pm10(hist):
    import seaborn as sns
    plt = _plt()
    medias = hist.pivot_table(index="ANIO", columns="MES", values="PM10", aggfunc="mean")
    cobertura = hist.assign(v=hist["PM10"].notna()).pivot_table(index="ANIO", columns="MES", values="v", aggfunc="mean") * 100
    fig, ejes = plt.subplots(1, 2, figsize=(14, 5))
    sns.heatmap(medias, annot=True, fmt=".0f", cmap="YlOrRd", ax=ejes[0], cbar_kws={"label": "µg/m³"})
    ejes[0].set_title("PM10 - promedio mensual")
    sns.heatmap(cobertura, annot=True, fmt=".0f", cmap="Blues", vmin=0, vmax=100, ax=ejes[1], cbar_kws={"label": "%"})
    ejes[1].set_title("PM10 - cobertura mensual (% de horas con dato)")
    fig.tight_layout()
    return fig


def grafica_perfil_horario(hist):
    plt = _plt()
    fig, ejes = plt.subplots(1, 2, figsize=(13, 4.5))
    h = hist.groupby("HORA")["PM10"].agg(["mean", "median"])
    ejes[0].plot(h.index, h["mean"], "o-", label="Media"); ejes[0].plot(h.index, h["median"], "s--", label="Mediana")
    ejes[0].set_title("Perfil horario de PM10 (2014-2024)"); ejes[0].set_xlabel("Hora"); ejes[0].set_ylabel("µg/m³")
    ejes[0].legend(); ejes[0].grid(alpha=.3)
    orden = ["Invierno", "Primavera", "Verano", "Otoño"]
    datos = [hist.loc[hist["ESTACION"] == e, "PM10"].dropna() for e in orden]
    ejes[1].boxplot(datos, showfliers=False)          # compatible con matplotlib antiguo y nuevo
    ejes[1].set_xticks(range(1, len(orden) + 1)); ejes[1].set_xticklabels(orden)
    ejes[1].set_title("PM10 por estación del año"); ejes[1].set_ylabel("µg/m³"); ejes[1].grid(alpha=.3)
    fig.tight_layout()
    return fig


def grafica_correlacion(correlaciones):
    import seaborn as sns
    plt = _plt()
    c = correlaciones.set_index("VARIABLE")
    fig, ax = plt.subplots(figsize=(8, 6.5))
    sns.heatmap(c, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, ax=ax)
    ax.set_title("Matriz de correlaciones (datos horarios, por pares)")
    fig.tight_layout()
    return fig


def grafica_observado_vs_predicho(predicciones):
    plt = _plt()
    fig, ejes = plt.subplots(1, 3, figsize=(15, 4.6))
    for ax, h in zip(ejes, HORIZONTES):
        d = predicciones[[f"PM10_OBSERVADO_MAS_{h}H", f"PM10_PREDICHO_MAS_{h}H"]].dropna()
        ax.scatter(d.iloc[:, 0], d.iloc[:, 1], s=6, alpha=.3)
        tope = float(max(d.max()))
        ax.plot([0, tope], [0, tope], "r--", lw=1)
        ax.set_title(f"+{h} h (2024)"); ax.set_xlabel("Observado (µg/m³)"); ax.set_ylabel("Predicho (µg/m³)")
        ax.grid(alpha=.3)
    fig.tight_layout()
    return fig


def grafica_serie_prueba(predicciones, dias=14):
    """Serie observado vs predicho +1h en el tramo de 'dias' días con más datos de 2024."""
    plt = _plt()
    d = predicciones.set_index("DATETIME")[["PM10_OBSERVADO_MAS_1H", "PM10_PREDICHO_MAS_1H"]]
    cuenta = d["PM10_OBSERVADO_MAS_1H"].notna().rolling(dias * 24).sum()
    fin = cuenta.idxmax()
    tramo = d.loc[fin - pd.Timedelta(hours=dias * 24 - 1):fin]
    fig, ax = plt.subplots(figsize=(13, 4.2))
    ax.plot(tramo.index, tramo.iloc[:, 0], label="Observado +1h")
    ax.plot(tramo.index, tramo.iloc[:, 1], label="Predicho +1h", alpha=.85)
    ax.set_title(f"PM10 observado vs predicho (+1 h) - tramo de {dias} días con mayor cobertura en 2024")
    ax.set_ylabel("µg/m³"); ax.legend(); ax.grid(alpha=.3)
    fig.autofmt_xdate(); fig.tight_layout()
    return fig


def grafica_metricas(metricas):
    plt = _plt()
    fig, ejes = plt.subplots(1, 3, figsize=(14, 4))
    x = np.arange(len(metricas)); ancho = .38
    for ax, m in zip(ejes, ["MAE", "RMSE", "R2"]):
        ax.bar(x - ancho / 2, metricas[m], ancho, label="HistGradientBoosting")
        ax.bar(x + ancho / 2, metricas[f"{m}_BASELINE_PERSISTENCIA"], ancho, label="Persistencia")
        ax.set_xticks(x); ax.set_xticklabels(metricas["HORIZON"]); ax.set_title(m); ax.grid(alpha=.3, axis="y")
    ejes[0].legend()
    fig.tight_layout()
    return fig


def generar_graficas(hist, disp, correlaciones, predicciones, metricas):
    return {"01_disponibilidad_anual": grafica_disponibilidad(disp),
            "02_pm10_mensual_y_cobertura": grafica_heatmap_pm10(hist),
            "03_perfil_horario_estacional": grafica_perfil_horario(hist),
            "04_correlaciones": grafica_correlacion(correlaciones),
            "05_observado_vs_predicho": grafica_observado_vs_predicho(predicciones),
            "06_serie_prueba_1h": grafica_serie_prueba(predicciones),
            "07_metricas_vs_persistencia": grafica_metricas(metricas)}


# ----------------------------------------------------------------------------
# 14. EXPORTACIÓN
# ----------------------------------------------------------------------------
def exportar_excel(hojas, ruta_salida):
    """Escribe las hojas en un único Excel con formato básico (encabezado en negrita,
    primera fila fija y ancho de columnas razonable)."""
    from openpyxl.styles import Font, PatternFill
    ruta_salida = Path(ruta_salida)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(ruta_salida, engine="openpyxl", datetime_format="yyyy-mm-dd hh:mm:ss") as escritor:
        for nombre, df in hojas.items():
            df.to_excel(escritor, sheet_name=nombre, index=False)
            ws = escritor.sheets[nombre]
            ws.freeze_panes = "A2"
            for celda in ws[1]:
                celda.font = Font(bold=True, name="Arial", color="FFFFFF")
                celda.fill = PatternFill("solid", fgColor="1F4E78")
            for i, col in enumerate(df.columns, start=1):
                largo = max(len(str(col)) + 2, 12)
                if nombre in ("Resumen", "Diccionario_variables"):
                    largo = 42 if i == 1 else 110
                ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = min(largo, 110)
    mensaje(f"  Excel guardado: {ruta_salida}")


# ----------------------------------------------------------------------------
# VALIDACIÓN CONTRA EL EXCEL DE REFERENCIA (no copia nada: solo compara)
# ----------------------------------------------------------------------------
def _comparar_tablas(rec, ref, tolerancia):
    """Compara dos DataFrames. Devuelve (estado, detalle, max_abs_diff)."""
    if list(rec.columns) != list(ref.columns):
        solo_rec = [c for c in rec.columns if c not in ref.columns]
        solo_ref = [c for c in ref.columns if c not in rec.columns]
        return "DIFERENTE", f"Columnas distintas. Solo reconstruido: {solo_rec[:5]} | solo referencia: {solo_ref[:5]}", np.nan
    if len(rec) != len(ref):
        return "DIFERENTE", f"Filas distintas: reconstruido={len(rec)} referencia={len(ref)}", np.nan
    max_dif, problemas = 0.0, []
    for col in rec.columns:
        a, b = rec[col].reset_index(drop=True), ref[col].reset_index(drop=True)
        if pd.api.types.is_datetime64_any_dtype(a) or pd.api.types.is_datetime64_any_dtype(b):
            ok = (pd.to_datetime(a).astype("datetime64[ns]").values == pd.to_datetime(b).astype("datetime64[ns]").values).all()
        elif pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b):
            af, bf = a.astype(float).values, b.astype(float).values
            if not (np.isnan(af) == np.isnan(bf)).all():
                ok = False
            else:
                dif = np.abs(af - bf)
                dif = dif[~np.isnan(dif)]
                mx = float(dif.max()) if len(dif) else 0.0
                max_dif = max(max_dif, mx)
                ok = mx <= tolerancia
        else:
            ok = (a.astype(str).values == b.astype(str).values).all()
        if not ok:
            problemas.append(col)
    if problemas:
        return "DIFERENTE", f"Columnas con diferencias: {problemas[:6]}", max_dif
    return "IGUAL", "Coincide dentro de la tolerancia", max_dif


def _comparar_resumen(rec, ref):
    """La hoja Resumen mezcla texto y números: se compara valor a valor."""
    if list(rec["ASPECTO"]) != list(ref["ASPECTO"]):
        return "DIFERENTE", "Aspectos distintos", np.nan
    malos = []
    for aspecto, a, b in zip(rec["ASPECTO"], rec["RESULTADO"], ref["RESULTADO"]):
        try:
            igual = abs(float(a) - float(b)) < 1e-9
        except (TypeError, ValueError):
            igual = str(a) == str(b)
        if not igual:
            malos.append(aspecto)
    return ("IGUAL", "Coincide", 0.0) if not malos else ("DIFERENTE", f"Difiere: {malos}", np.nan)


def validar_contra_referencia(hojas_rec, ruta_referencia):
    """Lee el Excel procesado de referencia y compara hoja por hoja con lo reconstruido."""
    ruta_referencia = validar_archivo(ruta_referencia, "el Excel procesado de referencia")
    referencia = pd.read_excel(ruta_referencia, sheet_name=None)
    filas = []
    for nombre in HOJAS_SALIDA:
        if nombre not in referencia:
            filas.append({"HOJA": nombre, "ESTADO": "NO EXISTE EN REFERENCIA", "MAX_DIF_ABS": np.nan,
                          "FILAS_RECONSTRUIDO": len(hojas_rec[nombre]), "FILAS_REFERENCIA": np.nan, "DETALLE": ""})
            continue
        rec, ref = hojas_rec[nombre], referencia[nombre].copy()
        # La referencia nombra '<lambda_0>' (artefacto de pandas) a la columna del percentil 95
        ref.columns = [c.replace("<lambda_0>", "p95") for c in ref.columns]
        if nombre == "Resumen":
            estado, detalle, dif = _comparar_resumen(rec, ref)
        else:
            tol = TOL_MODELO if nombre in (f"Predicciones_{ANIO_PRUEBA}", "Metricas_modelo") else TOL_ESTADISTICAS
            if nombre == "Metricas_modelo":      # las etiquetas de horizonte se normalizaron ('+2 hora' -> '+2 horas')
                ref["HORIZON"] = rec["HORIZON"].values
            estado, detalle, dif = _comparar_tablas(rec, ref, tol)
        filas.append({"HOJA": nombre, "ESTADO": estado, "MAX_DIF_ABS": dif, "FILAS_RECONSTRUIDO": len(rec),
                      "FILAS_REFERENCIA": len(ref), "DETALLE": detalle})
    informe = pd.DataFrame(filas)
    iguales = int((informe["ESTADO"] == "IGUAL").sum())
    mensaje(f"  Hojas idénticas a la referencia: {iguales}/{len(HOJAS_SALIDA)}")
    for _, f in informe.iterrows():
        mensaje(f"    [{f['ESTADO']:<9}] {f['HOJA']:<28} max|dif|={f['MAX_DIF_ABS']}")
    return informe


# ----------------------------------------------------------------------------
# ORQUESTACIÓN
# ----------------------------------------------------------------------------
def ejecutar_pipeline(ruta_entrada, ruta_referencia, carpeta_salida, guardar_graficas=True):
    """Ejecuta todo el procedimiento y devuelve un diccionario con los resultados."""
    carpeta_salida = Path(carpeta_salida)
    carpeta_salida.mkdir(parents=True, exist_ok=True)

    mensaje("[1/9] Cargando datos originales...")
    hojas_anuales = cargar_datos_originales(ruta_entrada)
    mensaje("[2/9] Inspección inicial...")
    inspeccion = inspeccion_inicial(hojas_anuales)
    mensaje("[3/9] Limpieza y normalización...")
    limpio, reporte_limpieza, duplicados = limpiar_y_normalizar(hojas_anuales)
    mensaje("[4/9] Consolidación histórica en malla horaria...")
    hist, faltantes = consolidar_malla_horaria(limpio)
    hist = agregar_variables_temporales(hist)
    disp = calcular_disponibilidad(hist)
    mensaje("[5/9] Estadísticas descriptivas...")
    est_anuales, est_mensuales = estadisticas_anuales(hist), estadisticas_mensuales(hist)
    est_horarias, est_estacionales = estadisticas_horarias(hist), estadisticas_estacionales(hist)
    diarios, correlaciones = promedios_diarios(hist), matriz_correlacion(hist)
    mensaje("[6/9] Ingeniería de características y objetivos...")
    completo = construir_objetivos(construir_features(hist))
    utilizable = seleccionar_utilizable(completo)
    mensaje(f"  Dataset completo: {len(completo):,} | utilizable (12 variables + 3 objetivos): {len(utilizable):,}")
    mensaje("[7/9] Entrenamiento y evaluación (separación temporal)...")
    metricas, predicciones, modelos, info_entrenamiento = entrenar_y_evaluar(completo)
    sensibilidad = sensibilidad_frontera(completo)

    hojas = {"Resumen": generar_resumen(hist, disp), "Historico_horario": hist, "Disponibilidad": disp,
             "Estadisticas_anuales": est_anuales, "Estadisticas_mensuales": est_mensuales,
             "Estadisticas_horarias": est_horarias, "Estadisticas_estacionales": est_estacionales,
             "Promedios_diarios": diarios, "Correlaciones": correlaciones,
             "Dataset_modelo_completo": completo, "Dataset_modelo_utilizable": utilizable,
             f"Predicciones_{ANIO_PRUEBA}": predicciones, "Metricas_modelo": metricas,
             "Diccionario_variables": generar_diccionario_hoja()}

    mensaje("[8/9] Exportando resultados...")
    exportar_excel(hojas, carpeta_salida / NOMBRE_EXCEL_SALIDA)
    figuras = {}
    if guardar_graficas:
        matplotlib.use("Agg")
        figuras = generar_graficas(hist, disp, correlaciones, predicciones, metricas)
        carpeta_graf = carpeta_salida / "graficas"
        carpeta_graf.mkdir(exist_ok=True)
        for nombre, fig in figuras.items():
            fig.savefig(carpeta_graf / f"{nombre}.png", dpi=110)
            _plt().close(fig)
        mensaje(f"  {len(figuras)} gráficas guardadas en {carpeta_graf}")

    mensaje("[9/9] Validación contra el Excel procesado de referencia...")
    validacion = None
    if ruta_referencia and Path(ruta_referencia).exists():
        validacion = validar_contra_referencia(hojas, ruta_referencia)
    else:
        mensaje("  Referencia no encontrada: se omite la validación (el análisis sí se completó).")

    # Informe auxiliar con inspección, validación, sensibilidad e información de entrenamiento
    with pd.ExcelWriter(carpeta_salida / "Validacion_reconstruccion_VAL.xlsx", engine="openpyxl") as w:
        (validacion if validacion is not None else pd.DataFrame({"AVISO": ["Sin referencia"]})).to_excel(w, sheet_name="Validacion_vs_referencia", index=False)
        sensibilidad.to_excel(w, sheet_name="Sensibilidad_frontera", index=False)
        info_entrenamiento.to_excel(w, sheet_name="Info_entrenamiento", index=False)
        inspeccion.to_excel(w, sheet_name="Inspeccion_original", index=False)
        reporte_limpieza.to_excel(w, sheet_name="Reporte_limpieza_script", index=False)

    return {"hojas": hojas, "validacion": validacion, "sensibilidad": sensibilidad,
            "info_entrenamiento": info_entrenamiento, "modelos": modelos, "figuras": figuras}


def main(argumentos=None):
    parser = argparse.ArgumentParser(description="Reconstrucción del análisis histórico y modelo PM10 - estación VAL")
    parser.add_argument("--entrada", default=ARCHIVO_ENTRADA_DEFECTO, help="Excel de datos originales")
    parser.add_argument("--referencia", default=ARCHIVO_REFERENCIA_DEFECTO,
                        help="Excel procesado de referencia para validar (opcional)")
    parser.add_argument("--salida", default=CARPETA_SALIDA_DEFECTO, help="Carpeta de resultados")
    parser.add_argument("--sin-graficas", action="store_true", help="No generar PNG")
    args = parser.parse_args(argumentos)
    try:
        resultado = ejecutar_pipeline(args.entrada, args.referencia, args.salida, not args.sin_graficas)
    except (FileNotFoundError, KeyError, ValueError, AssertionError) as error:
        mensaje(f"ERROR: {error}")
        return 2
    v = resultado["validacion"]
    if v is not None and (v["ESTADO"] != "IGUAL").any():
        mensaje("AVISO: hay hojas que NO coinciden con la referencia; revise Validacion_reconstruccion_VAL.xlsx")
        return 1
    mensaje("Proceso terminado correctamente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
