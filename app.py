from flask import Flask, render_template, request
from datetime import datetime

app = Flask(__name__)

# Modulo predictivo
def calcular_regresion_historica():
    y = [
        36.08, 39.02, 35.28, 31.69, 25.55, 45.55, 26.73, 30.25,
        40.58, 31.18, 27.71, 45.59, 36.04, 36.61, 41.03, 22.71,
        43.67, 33.27, 42.75, 47.52, 37.63, 42.97, 34.45, 25.72,
        27.38, 36.18, 47.37, 24.24
    ]

    x = list(range(1, len(y) + 1))
    mean_x = sum(x) / len(x)
    mean_y = sum(y) / len(y)

    numerador = 0
    denominador = 0
    for i in range(len(x)):
        numerador += (x[i] - mean_x) * (y[i] - mean_y)
        denominador += (x[i] - mean_x) ** 2

    if denominador == 0:
        return None

    pendiente = numerador / denominador
    intercepto = mean_y - (pendiente * mean_x)

    siguiente_x = len(x) + 1
    prediccion_lineal = pendiente * siguiente_x + intercepto

    ss_res = 0
    ss_tot = 0
    for i in range(len(x)):
        y_pred = pendiente * x[i] + intercepto
        ss_res += (y[i] - y_pred) ** 2
        ss_tot += (y[i] - mean_y) ** 2

    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

    c0 = 3000941 / 96744
    c1 = -145105 / 768037
    c2 = 3473 / 550139
    c3 = -31 / 713628

    prediccion_cubica = c0 + (c1 * siguiente_x) + (c2 * (siguiente_x**2)) + (c3 * (siguiente_x**3))

    x_chart = list(range(1, len(y) + 2))
    y_real_chart = y + [None]
    y_lineal_chart = [round(pendiente * val + intercepto, 2) for val in x_chart]
    y_cubica_chart = [round(c0 + (c1*val) + (c2*(val**2)) + (c3*(val**3)), 2) for val in x_chart]

    return {
        "ecuacion": f"y = {round(pendiente, 2)}x + {round(intercepto, 2)}",
        "prediccion": round(prediccion_lineal, 2),
        "prediccion_c": round(prediccion_cubica, 2),
        "r2": round(r2, 4),
        "n_datos": len(x),
        "media_y": round(mean_y, 2),
        "labels_chart": x_chart,
        "real_chart": y_real_chart,
        "lineal_chart": y_lineal_chart,
        "cubica_chart": y_cubica_chart
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