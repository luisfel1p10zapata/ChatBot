
import re
import unicodedata
from pysentimiento import create_analyzer


# ─── CARGA DE MODELOS ───────────────────────────────────

print("🔄 Cargando modelos de pysentimiento...")

emotion_analyzer = create_analyzer(task="emotion", lang="es")
hate_analyzer = create_analyzer(task="hate_speech", lang="es")

print("✅ Modelos cargados correctamente")


# ─── NORMALIZACIÓN ──────────────────────────────────────

def normalizar(texto):
    """
    Convierte el texto a minúsculas, elimina tildes
    y normaliza espacios.
    """
    texto = texto.lower().strip()

    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        caracter for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )

    texto = re.sub(r"\s+", " ", texto)

    return texto


def contiene_patron(texto, patrones):
    """
    Busca expresiones completas para evitar coincidencias
    accidentales dentro de otras palabras.
    """
    return any(
        re.search(patron, texto)
        for patron in patrones
    )


# ─── DETECCIÓN DE INTENCIÓN ─────────────────────────────

PATRONES_INTENCION = {

    "agresion": [
        r"\bte odio\b",
        r"\bmaldito\b",
        r"\bmaldita\b",
        r"\bestupid[oa]s?\b",
        r"\bidiotas?\b",
        r"\bimbeciles?\b",
        r"\binutil(?:es)?\b",
        r"\bcallate\b",
        r"\bno sirves para nada\b",
        r"\bvete a la mierda\b",
        r"\bque asco das\b",
        r"\bme tienes hart[oa]\b",
        r"\bdejame en paz\b",
        r"\bno te soporto\b",
    ],

    "ruptura": [
        r"\bquiero terminar\b",
        r"\bterminemos\b",
        r"\bterminar la relacion\b",
        r"\bno quiero seguir\b",
        r"\bno quiero estar contigo\b",
        r"\besto se acabo\b",
        r"\bse acabo lo nuestro\b",
        r"\bhasta aqui llegamos\b",
        r"\bquiero dejarte\b",
        r"\bquiero que terminemos\b",
        r"\bya no quiero estar contigo\b",
    ],

    "manipulacion": [
        r"\bsi me quisieras\b",
        r"\bsi realmente me amaras\b",
        r"\bsi de verdad te importara\b",
        r"\bdespues de todo lo que hice por ti\b",
        r"\bpor tu culpa\b",
        r"\bsi no haces eso\b",
        r"\bsi no estas conmigo\b",
        r"\bnunca haces nada por mi\b",
        r"\bsiempre me haces lo mismo\b",
        r"\bvas a ver lo que pasa si\b",
        r"\bme haces sentir culpable\b",
    ],

    "control": [
        r"\bdonde estas\b",
        r"\bcon quien estas\b",
        r"\bcon quien andas\b",
        r"\bdime exactamente donde estas\b",
        r"\benviame tu ubicacion\b",
        r"\bmandame tu ubicacion\b",
        r"\bquiero saber donde estas\b",
        r"\bpor que no me dices donde estas\b",
        r"\bcon quien hablas\b",
        r"\bmandame una foto para saber donde estas\b",
    ],

    "celos": [
        r"\bcon quien estabas\b",
        r"\bquien es esa persona\b",
        r"\bquien es esa mujer\b",
        r"\bquien es ese hombre\b",
        r"\bte vi con alguien\b",
        r"\bte vi con otra persona\b",
        r"\bestabas con alguien mas\b",
        r"\btienes a alguien mas\b",
        r"\bquien te escribio\b",
        r"\bpor que le hablas\b",
        r"\bpor que hablas con el\b",
        r"\bpor que hablas con ella\b",
        r"\bestas saliendo con alguien\b",
    ],

    "reclamo": [
        r"\bpor que no me respondes\b",
        r"\bpor que no contestas\b",
        r"\bme estas ignorando\b",
        r"\bme ignoras\b",
        r"\bnunca me escribes\b",
        r"\bya no me escribes\b",
        r"\bsiempre tengo que buscarte\b",
        r"\bsoy siempre yo quien te busca\b",
        r"\bya no me prestas atencion\b",
        r"\bno tienes tiempo para mi\b",
        r"\bantes no eras asi\b",
        r"\bya no eres como antes\b",
        r"\bparece que no te importo\b",
        r"\bni siquiera preguntas por mi\b",
        r"\bsiempre me dejas esperando\b",
        r"\bpor que tardas tanto en responder\b",
        r"\bte cuesta tanto responder\b",
    ],

    "desinteres": [
        r"\bno quiero hablar contigo\b",
        r"\bno me interesa hablar\b",
        r"\bno tengo ganas de hablar\b",
        r"\bdejemos de hablar\b",
        r"\bno quiero seguir hablando\b",
        r"\bhablamos otro dia\b",
        r"\bmejor dejemos asi\b",
        r"\bno tengo nada que decirte\b",
        r"\bya no me interesa\b",
        r"\bno me importa lo que hagas\b",
        r"\bhaz lo que quieras\b",
        r"\bcomo quieras\b",
        r"\bda igual lo que pase\b",
        r"\bno importa, dejalo asi\b",
    ],

    "tristeza": [
        r"\bme siento triste\b",
        r"\bestoy triste\b",
        r"\bme siento solo\b",
        r"\bme siento sola\b",
        r"\bme siento mal\b",
        r"\bestoy deprimido\b",
        r"\bestoy deprimida\b",
        r"\bno dejo de llorar\b",
        r"\bme duele mucho\b",
        r"\bme siento vacio\b",
        r"\bme siento vacia\b",
        r"\bnadie me entiende\b",
        r"\bme siento abandonado\b",
        r"\bme siento abandonada\b",
        r"\bestoy pasando por un mal momento\b",
    ],

    "afecto": [
        r"\bte quiero\b",
        r"\bte amo\b",
        r"\bte adoro\b",
        r"\bme encantas\b",
        r"\bme gustas\b",
        r"\bte extraño\b",
        r"\bte extrano mucho\b",
        r"\bte necesito\b",
        r"\beres importante para mi\b",
        r"\bme haces feliz\b",
        r"\bquiero estar contigo\b",
        r"\bme haces falta\b",
        r"\bme encanta estar contigo\b",
        r"\bquiero verte\b",
        r"\bpienso mucho en ti\b",
    ],

    "curiosidad": [
        r"\bcomo estas\b",
        r"\bque tal estas\b",
        r"\bcomo te va\b",
        r"\bque cuentas\b",
        r"\bque has hecho\b",
        r"\ben que andas\b",
        r"\bcomo estuvo tu dia\b",
        r"\bque tal tu dia\b",
        r"\bque haces de bueno\b",
        r"\bque planes tienes\b",
        r"\bcomo te fue\b",
        r"\bque paso\b",
    ],
}


def detectar_intencion(texto):

    texto = normalizar(texto)

    # Las categorías se evalúan por prioridad.
    # Una expresión específica tiene preferencia
    # sobre una expresión más general.

    prioridades = [
        "agresion",
        "ruptura",
        "manipulacion",
        "control",
        "celos",
        "reclamo",
        "desinteres",
        "tristeza",
        "afecto",
        "curiosidad",
    ]

    for intencion in prioridades:

        patrones = PATRONES_INTENCION[intencion]

        if contiene_patron(texto, patrones):
            return intencion

    return "normal"


# ─── ANÁLISIS EMOCIONAL ─────────────────────────────────

def mapear_emocion(emocion_raw):

    emocion_raw = str(emocion_raw).lower()

    emocion_map = {
        "joy": "positivo",
        "sadness": "tristeza",
        "anger": "enojo",
        "surprise": "sorpresa",
        "disgust": "disgusto",
        "fear": "miedo",
        "neutral": "neutral",
        "others": "neutral",
        "other": "neutral",
    }

    return emocion_map.get(emocion_raw, "neutral")


# ─── DETECTOR DE SEÑALES DE DISTANCIAMIENTO ─────────────

def calcular_ghosting(texto, intencion, emocion):

    texto_normalizado = normalizar(texto)

    palabras = texto_normalizado.split()

    score = 0

    # Mensajes extremadamente cortos.
    # Solo representan una señal débil.
    if len(palabras) == 1:
        score += 15

    elif len(palabras) <= 3:
        score += 8

    # Expresiones explícitas de cierre o falta de interés.
    expresiones_distancia = [
        r"\bno quiero hablar\b",
        r"\bdejame en paz\b",
        r"\bhablamos despues\b",
        r"\bno tengo ganas\b",
        r"\bmejor dejemos asi\b",
        r"\bno me interesa\b",
        r"\bya no importa\b",
    ]

    if contiene_patron(texto_normalizado, expresiones_distancia):
        score += 35

    # Intención identificada.
    if intencion == "desinteres":
        score += 30

    elif intencion == "afecto":
        score -= 15

    elif intencion == "curiosidad":
        score -= 10

    # Una emoción positiva o neutral no es señal de ghosting.
    if emocion == "positivo":
        score -= 10

    return max(0, min(score, 85))


# ─── DETECTOR DE TOXICIDAD ──────────────────────────────

def detectar_toxicidad(hate_result):

    etiqueta = str(hate_result.output).lower()

    etiquetas_toxicas = {
        "hateful",
        "targeted",
    }

    return "si" if etiqueta in etiquetas_toxicas else "no"


# ─── CALCULAR RIESGO ────────────────────────────────────

def calcular_riesgo(hate_result, intencion, emocion):

    etiqueta = str(hate_result.output).lower()

    if etiqueta in {"hateful", "targeted"}:
        return "🔴 Alto"

    if intencion in {
        "agresion",
        "ruptura",
        "manipulacion",
        "control",
    }:
        return "🟡 Medio"

    if emocion in {"enojo", "disgusto"}:
        return "🟡 Medio"

    return "🟢 Bajo"


# ─── CONFIANZA DEL MODELO ───────────────────────────────

def obtener_confianza(prediccion):

    try:
        probabilidades = prediccion.probas

        if not probabilidades:
            return 0

        confianza = max(probabilidades.values())

        return round(float(confianza) * 100)

    except (AttributeError, TypeError, ValueError):
        return 0


# ─── FUNCIÓN PRINCIPAL ──────────────────────────────────

def analizar_texto(texto):

    try:

        if not texto or not texto.strip():
            return "neutral", "no", 0, "🟢 Bajo", "normal", 0

        # Análisis de emociones.
        emocion_pred = emotion_analyzer.predict(texto)

        # Análisis de lenguaje ofensivo.
        hate_pred = hate_analyzer.predict(texto)

        # Emoción.
        emocion_raw = emocion_pred.output

        emocion = mapear_emocion(emocion_raw)

        # Intención mediante expresiones completas.
        intencion = detectar_intencion(texto)

        # Toxicidad.
        toxicidad = detectar_toxicidad(hate_pred)

        # Señales individuales de distanciamiento.
        ghosting = calcular_ghosting(
            texto,
            intencion,
            emocion
        )

        # Riesgo.
        riesgo = calcular_riesgo(
            hate_pred,
            intencion,
            emocion
        )

        # Confianza emocional.
        confianza = obtener_confianza(emocion_pred)

        return (
            emocion,
            toxicidad,
            ghosting,
            riesgo,
            intencion,
            confianza
        )

    except Exception as e:

        print(f"❌ Error en analizar_texto: {e}")

        return (
            "neutral",
            "no",
            0,
            "🟢 Bajo",
            "normal",
            0
        )
