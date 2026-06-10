from flask import Flask, render_template, request
from datetime import datetime
import pandas as pd

app = Flask(__name__)

# Modulo predictivo enfocado en pH
def calcular_regresion_historica():
    try:
        ruta_csv = 'dataset_suelo_NASA_soconusco_2015_2024.xlsx - Dataset Completo.csv'
        df = pd.read_csv(ruta_csv)
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        
        # Para proyecciones diarias, ordenamos y tomamos los ultimos 30 dias registrados
        df = df.sort_values('Fecha')
        datos_recientes = df.tail(30)
        
        y = datos_recientes['pH_Suelo'].tolist()
        
    except Exception as e:
        print(f"Alerta CSV: {e}. Usando respaldo de pH.")
        # Datos sinteticos de respaldo si falla el CSV
        y = [6.2, 6.25, 6.22, 6.3, 6.31, 6.35, 6.4, 6.38, 6.42, 6.45, 
             6.48, 6.5, 6.52, 6.55, 6.51, 6.58, 6.6, 6.62, 6.65, 6.68]

    x = list(range(1, len(y) + 1))
    mean_x = sum(x) / len(x) if len(x) > 0 else 0
    mean_y = sum(y) / len(y) if len(y) > 0 else 0

    numerador = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(len(x)))
    denominador = sum((x[i] - mean_x) ** 2 for i in range(len(x)))

    pendiente = numerador / denominador if denominador != 0 else 0
    intercepto = mean_y - (pendiente * mean_x)

    ultimo_x = len(x)
    
    # Proyecciones especificas solicitadas
    prediccion_1_dia = pendiente * (ultimo_x + 1) + intercepto
    prediccion_7_dias = pendiente * (ultimo_x + 7) + intercepto

    # Calculo de metricas: R2 y Margen de Error Absoluto (MAE)
    ss_res = 0
    ss_tot = 0
    error_absoluto_total = 0

    for i in range(len(x)):
        y_pred = pendiente * x[i] + intercepto
        ss_res += (y[i] - y_pred) ** 2
        ss_tot += (y[i] - mean_y) ** 2
        error_absoluto_total += abs(y[i] - y_pred)

    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    margen_error = error_absoluto_total / len(x) if len(x) > 0 else 0

    # Preparacion de datos para Chart.js (historico + 7 dias futuros)
    x_chart = list(range(1, len(y) + 8)) 
    y_real_chart = y + [None] * 7
    y_lineal_chart_completo = [round(pendiente * val + intercepto, 2) for val in x_chart]

    return {
        "ecuacion": f"y = {round(pendiente, 4)}x + {round(intercepto, 4)}",
        "prediccion_1": round(prediccion_1_dia, 2),
        "prediccion_7": round(prediccion_7_dias, 2),
        "margen_error": round(margen_error, 4),
        "r2": round(r2, 4),
        "labels_chart": x_chart,
        "real_chart": y_real_chart,
        "lineal_chart": y_lineal_chart_completo
    }

# Modulo de diagnostico
RANGOS = {
    "ph": {"min": 6.0, "max": 7.0, "unidad": "", "label": "pH del suelo"},
    "humedad": {"min": 70, "max": 80, "unidad": "%", "label": "Humedad del suelo"},
    "n": {"min": 20, "max": 60, "unidad": "ppm", "label": "Nitrogeno (N)"},
    "p": {"min": 15, "max": 40, "unidad": "ppm", "label": "Fosforo (P)"},
    "k": {"min": 100, "max": 250, "unidad": "ppm", "label": "Potasio (K)"},
    "ce": {"min": 0.5, "max": 2.0, "unidad": "dS/m", "label": "Conductividad Electrica"},
    "temp": {"min": 23, "max": 28, "unidad": "C", "label": "Temperatura"},
    "mo": {"min": 3.0, "max": 5.0, "unidad": "%", "label": "Materia Organica (MO)"},
}

def diagnosticar_suelo_cacao(ph, humedad, n, p, k, ce, temp, mo):
    alertas = []
    recomendaciones = []
    semaforo = "VERDE"
    
    jerarquia = {"VERDE": 0, "AMARILLO": 1, "NARANJA": 2, "AZUL": 3, "ROJO": 4, "GRIS": -1}
    
    def actualizar_semaforo(color_actual, nuevo_color):
        if jerarquia[nuevo_color] > jerarquia[color_actual]:
            return nuevo_color
        return color_actual

    if ph is not None:
        if ph < 5.5:
            alertas.append("Acidez critica: bloqueo total de macronutrientes.")
            recomendaciones.append("Aplicar cal dolomitica 2-3 ton/ha. Incorporar al suelo 30 dias antes de fertilizar.")
            semaforo = actualizar_semaforo(semaforo, "ROJO")
        elif ph < 6.0:
            alertas.append("Acidez severa detectada.")
            recomendaciones.append("Aplicar cal agricola 1-2 ton/ha. Mezclar bien con el suelo.")
            semaforo = actualizar_semaforo(semaforo, "ROJO")
        elif ph > 7.5:
            alertas.append("Alcalinidad alta: posible bloqueo de micronutrientes.")
            recomendaciones.append("Aplicar azufre elemental (100-200 kg/ha) o compost acido.")
            semaforo = actualizar_semaforo(semaforo, "NARANJA")

    if ce is not None:
        if ce >= 2.0:
            alertas.append("Salinidad critica: presion osmotica danina para las raices.")
            recomendaciones.append("Suspender fertilizantes quimicos. Aplicar riego de lavado abundante.")
            semaforo = actualizar_semaforo(semaforo, "ROJO")
        elif ce > 1.5:
            alertas.append("Salinidad elevada: monitoreo urgente.")
            recomendaciones.append("Reducir fertilizantes salinos. Aumentar frecuencia de riego.")
            semaforo = actualizar_semaforo(semaforo, "NARANJA")

    falta_nutrientes = False
    if n is not None and n < 20:
        recomendaciones.append("Deficit de Nitrogeno: aplicar 40-60 kg/ha de urea o 100-150 kg/ha de gallinaza.")
        falta_nutrientes = True
    if p is not None and p < 15:
        recomendaciones.append("Deficit de Fosforo: aplicar 30-40 kg/ha de superfosfato simple.")
        falta_nutrientes = True
    if k is not None and k < 100:
        recomendaciones.append("Deficit de Potasio: aplicar 40-50 kg/ha de cloruro de potasio.")
        falta_nutrientes = True

    if falta_nutrientes:
        alertas.append("Deficiencia de macronutrientes (N-P-K).")
        semaforo = actualizar_semaforo(semaforo, "NARANJA")

    if humedad is not None:
        if humedad > 85:
            alertas.append("Encharcamiento severo: riesgo de pudricion radicular.")
            recomendaciones.append("Cerrar riego de inmediato. Abrir zanjas de drenaje perimetral.")
            semaforo = actualizar_semaforo(semaforo, "AZUL")
        elif humedad > 80:
            alertas.append("Exceso de humedad: riesgo de asfixia radicular.")
            recomendaciones.append("Suspender riego. Habilitar drenaje preventivo.")
            semaforo = actualizar_semaforo(semaforo, "AZUL")
        elif humedad < 60:
            alertas.append("Estres hidrico severo: punto de marchitez permanente.")
            recomendaciones.append("Riego urgente: 15-20 L/arbol/dia. Colocar mantillo organico de 10 cm.")
            semaforo = actualizar_semaforo(semaforo, "ROJO")
        elif humedad < 70:
            alertas.append("Estres hidrico: humedad por debajo del rango operativo.")
            recomendaciones.append("Iniciar riego: 10-15 L/arbol cada 3 dias. Colocar mantillo.")
            semaforo = actualizar_semaforo(semaforo, "AMARILLO")

    if temp is not None:
        if temp > 32 or temp < 20:
            alertas.append("Temperatura extrema: danina para el sistema radicular del cacao.")
            recomendaciones.append("Instalar sombra con guacimo o chalahuite. Rango ideal: 23-28 C.")
            semaforo = actualizar_semaforo(semaforo, "ROJO")
        elif temp > 28 or temp < 23:
            alertas.append("Temperatura fuera del rango optimo (23-28 C).")
            recomendaciones.append("Incorporar arboles de servicio para sombra ligera y regulacion termica.")
            semaforo = actualizar_semaforo(semaforo, "AMARILLO")

    if mo is not None:
        if mo < 2.0:
            alertas.append("Materia organica critica: suelo degradado estructuralmente.")
            recomendaciones.append("Incorporar 10-15 ton/ha de compost maduro. Evitar labranza profunda.")
            semaforo = actualizar_semaforo(semaforo, "NARANJA")
        elif mo < 3.0:
            alertas.append("Materia organica baja: capacidad de intercambio cationico reducida.")
            recomendaciones.append("Aplicar 5-8 ton/ha de compost o abono verde. Rango optimo: 3-5%.")
            semaforo = actualizar_semaforo(semaforo, "AMARILLO")

    todos_nulos = all(v is None for v in [ph, humedad, n, p, k, ce, temp, mo])

    if not alertas:
        if todos_nulos:
            alertas.append("Informacion insuficiente para el diagnostico.")
            recomendaciones.append("Ingrese al menos un parametro para ejecutar el analisis.")
            semaforo = "GRIS"
        else:
            alertas.append("Condiciones edafologicas dentro de los parametros operativos.")
            recomendaciones.append("El cultivo no requiere intervencion. Mantener las practicas de manejo actuales.")

    return {
        "semaforo": semaforo,
        "alertas": alertas,
        "acciones": recomendaciones,
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M")
    }

def procesar_entrada(valor):
    if not valor or valor.strip() == "":
        return None
    try:
        return float(valor)
    except ValueError:
        return None

# Rutas
@app.route('/', methods=['GET', 'POST'])
def index():
    resultado_actual = None
    datos_prediccion = calcular_regresion_historica()

    if request.method == 'POST':
        ph = procesar_entrada(request.form.get('ph'))
        humedad = procesar_entrada(request.form.get('humedad'))
        n = procesar_entrada(request.form.get('n'))
        p = procesar_entrada(request.form.get('p'))
        k = procesar_entrada(request.form.get('k'))
        ce = procesar_entrada(request.form.get('ce'))
        temp = procesar_entrada(request.form.get('temp'))
        mo = procesar_entrada(request.form.get('mo'))

        resultado_actual = diagnosticar_suelo_cacao(ph, humedad, n, p, k, ce, temp, mo)

    return render_template('index.html', resultado=resultado_actual, prediccion=datos_prediccion, rangos=RANGOS)

if __name__ == '__main__':
    app.run(debug=True, port=8080)