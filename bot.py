from dotenv import load_dotenv
load_dotenv()

import os
import random
from collections import Counter

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

from predict import analizar_texto


# ─── CONFIGURACIÓN ──────────────────────────────────────

TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TOKEN:
    print("❌ ERROR: Variable TELEGRAM_TOKEN no configurada")
    print("📌 Configuración:")
    print("   En PowerShell: $env:TELEGRAM_TOKEN='tu_token_aqui'")
    exit(1)


# ─── MENÚ PRINCIPAL ─────────────────────────────────────

async def enviar_menu(message):
    """Envía el menú principal. Funciona tanto desde /start como desde un botón."""
    teclado = [
        [
            InlineKeyboardButton("💬 Analizar mensaje", callback_data="analizar"),
            InlineKeyboardButton("📊 Mi resumen", callback_data="resumen")
        ],
        [
            InlineKeyboardButton("🧠 Detectar patrones", callback_data="patrones")
        ],
        [
            InlineKeyboardButton("🧮 Calculadora", callback_data="calculadora")
        ],
        [
            InlineKeyboardButton("🔄 Reiniciar análisis", callback_data="reiniciar")
        ],
        [
            InlineKeyboardButton("❓ Cómo funciona", callback_data="ayuda")
        ]
    ]

    mensaje = (
        "👋 ¡Bienvenido, soy tu detective personal!\n\n"
        "Puedo analizar tus conversaciones, identificar emociones "
        "y detectar patrones de comunicación.\n\n"
        "También puedo hacer operaciones numéricas con la calculadora.\n\n"
        "Selecciona una opción:"
    )

    await message.reply_text(
        mensaje,
        reply_markup=InlineKeyboardMarkup(teclado)
    )


async def mostrar_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await enviar_menu(update.message)


# ─── CALCULADORA ────────────────────────────────────────

OPERADORES = {
    "sumar": "+",
    "restar": "-",
    "multiplicar": "×",
    "dividir": "÷",
}


async def mostrar_calculadora(query):
    teclado = [
        [
            InlineKeyboardButton("➕ Sumar", callback_data="sumar"),
            InlineKeyboardButton("➖ Restar", callback_data="restar")
        ],
        [
            InlineKeyboardButton("✖️ Multiplicar", callback_data="multiplicar"),
            InlineKeyboardButton("➗ Dividir", callback_data="dividir")
        ],
        [
            InlineKeyboardButton("🔙 Volver al menú", callback_data="menu")
        ]
    ]

    await query.message.reply_text(
        "🧮 CALCULADORA\n\nSelecciona la operación:",
        reply_markup=InlineKeyboardMarkup(teclado)
    )


async def manejar_calculadora(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    opcion = query.data

    if opcion == "calculadora":
        await mostrar_calculadora(query)
        return

    if opcion in OPERADORES:
        context.user_data["operacion"] = opcion
        context.user_data["esperando_numeros"] = True

        await query.message.reply_text(
            f"Seleccionaste: {opcion.upper()}\n\n"
            "Envíame los dos números separados por un espacio.\n\n"
            "Ejemplo: 20 5"
        )


async def procesar_calculadora(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Devuelve True si el mensaje fue manejado por la calculadora."""
    if not context.user_data.get("esperando_numeros"):
        return False

    texto = update.message.text.strip()
    operacion = context.user_data.get("operacion")

    # Validar entrada
    try:
        partes = texto.replace(",", ".").split()

        if len(partes) != 2:
            raise ValueError

        num1, num2 = map(float, partes)

    except ValueError:
        await update.message.reply_text(
            "⚠️ Ingresa exactamente dos números.\n"
            "Ejemplo: 15 3"
        )
        return True  # sigue esperando números

    # Calcular
    if operacion == "sumar":
        resultado = num1 + num2
    elif operacion == "restar":
        resultado = num1 - num2
    elif operacion == "multiplicar":
        resultado = num1 * num2
    elif operacion == "dividir":
        if num2 == 0:
            await update.message.reply_text(
                "❌ No se puede dividir entre cero.\n"
                "Envíame otros dos números."
            )
            return True  # sigue esperando números
        resultado = num1 / num2
    else:
        context.user_data.pop("esperando_numeros", None)
        context.user_data.pop("operacion", None)
        return False

    await update.message.reply_text(
        f"🧮 RESULTADO\n\n"
        f"Operación: {num1:g} {OPERADORES[operacion]} {num2:g}\n"
        f"Resultado: {resultado:g}"
    )

    # Limpiar estado de la calculadora
    context.user_data.pop("esperando_numeros", None)
    context.user_data.pop("operacion", None)

    return True


# ─── BOTONES DEL MENÚ ───────────────────────────────────

async def manejar_botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    opcion = query.data

    if opcion == "analizar":
        # Cancelar la calculadora si estaba activa
        context.user_data.pop("esperando_numeros", None)
        context.user_data.pop("operacion", None)
        context.user_data["esperando_mensaje"] = True
        await query.message.reply_text(
            "💬 Envíame el mensaje que quieres analizar."
        )

    elif opcion in ("resumen", "patrones"):
        historial = context.user_data.get("historial", [])
        await query.message.reply_text(
            generar_resumen(historial),
            parse_mode="Markdown"
        )

    elif opcion == "reiniciar":
        context.user_data.clear()
        await query.message.reply_text(
            "🔄 Tu historial de análisis ha sido reiniciado."
        )

    elif opcion == "ayuda":
        await query.message.reply_text(
            "Analizo emociones, intenciones, discurso de odio "
            "y señales de distanciamiento en los mensajes.\n\n"
            "También tengo una calculadora para sumar, restar, "
            "multiplicar y dividir."
        )

    elif opcion == "menu":
        # Cancelar la calculadora si estaba activa
        context.user_data.pop("esperando_numeros", None)
        context.user_data.pop("operacion", None)
        await enviar_menu(query.message)


# ─── INTERPRETACIONES ───────────────────────────────────

INTERPRETACIONES = {
    "reclamo": [
        "📢 La persona se siente ignorada y reclama tu atención.",
        "😤 Hay frustración porque esperaba una respuesta y no llegó.",
        "💢 Percibe que la estás descuidando o ignorando.",
    ],
    "celos": [
        "😒 Siente inseguridad y teme que haya un tercero.",
        "🔍 Necesita confirmar que sigue siendo importante para ti.",
        "🤨 Desconfía de tus acciones o amistades.",
    ],
    "agresion": [
        "⚠️ Está muy enojado y busca herir o provocar.",
        "🔥 El conflicto puede escalar si respondes de forma similar.",
        "💥 Hay agresividad que debes manejar con cuidado.",
    ],
    "tristeza": [
        "😢 Está pasando por un momento difícil o de dolor.",
        "🫂 Necesita apoyo emocional y contención.",
        "💔 Hay vulnerabilidad, no lo ignores.",
    ],
    "manipulacion": [
        "🎭 Está usando culpa o condiciones para obtener lo que quiere.",
        "⛓️ Quiere presionarte emocionalmente para que actúes.",
        "⚠️ Ten cuidado con responder desde la culpa.",
    ],
    "control": [
        "🔒 Quiere saber todo lo que haces y con quién.",
        "👁️ Hay una necesidad excesiva de controlarte.",
        "📱 No confía plenamente en ti.",
    ],
    "ruptura": [
        "💔 Está considerando seriamente terminar la relación.",
        "😩 Hay agotamiento emocional acumulado.",
        "🚪 Quiere distancia o poner un punto final.",
    ],
    "desinteres": [
        "😐 No muestra interés en seguir la conversación.",
        "❄️ Hay distancia emocional o está ocupado.",
        "📉 Probablemente no quiere profundizar.",
    ],
    "inseguridad": [
        "😟 Tiene dudas sobre la relación o sobre sí mismo.",
        "🤔 Necesita reafirmación y seguridad.",
        "🌀 Busca calmar su ansiedad con respuestas claras.",
    ],
    "afecto": [
        "💕 Está expresando cariño y buenos sentimientos.",
        "🤗 Quiere acercarse y fortalecer el vínculo.",
        "🌸 Hay conexión emocional positiva.",
    ],
    "curiosidad": [
        "🤔 Tiene interés genuino en ti y tu vida.",
        "💬 Quiere iniciar o mantener una conversación.",
        "🔍 Busca conocer más sobre ti.",
    ],
    "normal": [
        "💬 Es una conversación cotidiana sin carga emocional.",
        "✅ No hay señales de conflicto ni urgencia.",
        "📝 Todo fluye con normalidad.",
    ],
}


# ─── SUGERENCIAS ────────────────────────────────────────

SUGERENCIAS = {
    "reclamo": [
        "🗣️ Responde: 'Entiendo que te sientes ignorado, no fue mi intención. Hablemos.'",
        "⏸️ Reconoce su molestia antes de dar explicaciones: 'Tienes razón, no respondí rápido.'",
        "🤝 Pregunta: '¿Qué puedo hacer para que no te sientas así?'",
    ],
    "celos": [
        "🧠 Responde con calma: 'No hay nadie más, pero entiendo tu inseguridad.'",
        "💬 Valida su emoción: 'Veo que esto te preocupa, hablemos sin pelear.'",
        "🔐 Reafirma: 'Eres importante para mí. ¿Podemos hablar de esto tranquilos?'",
    ],
    "agresion": [
        "🌬️ No respondas con agresión. Di: 'Esto se está poniendo feo, hablemos más tarde.'",
        "🚫 Establece límite: 'No voy a responder si me hablas así.'",
        "⏰ Tómate un tiempo: 'Mejor hablamos cuando estemos más calmados.'",
    ],
    "tristeza": [
        "👥 Responde: 'Estoy aquí para ti. ¿Quieres hablar de lo que pasa?'",
        "💬 Muestra apoyo: 'Lamento que te sientas así, cuentas conmigo.'",
        "🤗 Ofrece compañía: '¿Necesitas desahogarte o prefieres distraerte?'",
    ],
    "manipulacion": [
        "🚩 No cedas por culpa. Di: 'No me gusta que me condiciones así.'",
        "🗣️ Marca límite: 'Si me quieres pedir algo, hazlo sin chantajes.'",
        "⚖️ Responde neutro: 'Te escucho, pero no voy a reaccionar desde la culpa.'",
    ],
    "control": [
        "🤝 Responde: 'Confío en ti y espero que tú confíes en mí.'",
        "📱 Marca espacio: 'Está bien que quieras saber, pero también necesito mi espacio.'",
        "🧘 Tranquiliza: 'No pasa nada, pero no puedo responder todo el tiempo.'",
    ],
    "ruptura": [
        "💬 Responde: 'Hablemos esto en persona, es importante.'",
        "🤔 Pide tiempo: 'No tomemos decisiones en caliente. Hablemos mañana.'",
        "🕊️ Si es firme: 'Lo respeto si es tu decisión, pero me duele.'",
    ],
    "desinteres": [
        "🧐 Pregunta: '¿Estás bien? Parece que no tienes ganas de hablar.'",
        "💬 Dale espacio: 'Cuando quieras hablar, aquí estoy.'",
        "⏸️ No insistas: 'Ok, hablamos cuando tengas tiempo.'",
    ],
    "inseguridad": [
        "🔍 Responde: 'Estoy contigo, no tienes nada que temer.'",
        "💬 Tranquiliza: 'Si algo te preocupa, pregúntame sin miedo.'",
        "📖 Reafirma: 'Me importas y no tengo nada que ocultar.'",
    ],
    "afecto": [
        "🌸 Corresponde: 'Yo también te quiero mucho ❤️'",
        "💌 Agradece: 'Qué bonito mensaje, gracias por tus palabras.'",
        "🎁 Sorprende: 'Me hiciste el día, te quiero igual.'",
    ],
    "curiosidad": [
        "🔍 Responde con entusiasmo: 'Todo bien, ¿y tú? Cuéntame.'",
        "💬 Aprovecha: 'Justo pensaba en ti. ¿Qué has hecho?'",
        "🌟 Sigue la conversación: 'Me alegra que preguntes, te cuento...'",
    ],
    "normal": [
        "👍 Responde con naturalidad: 'Todo bien, ¿y tú?'",
        "💬 Sigue la conversación: 'Qué bueno, seguimos hablando.'",
        "🌟 Mantén el tono: 'Genial, cualquier cosa me dices.'",
    ],
}


# ─── EMOJIS ─────────────────────────────────────────────

EMOJIS = {
    "reclamo": "😔",
    "celos": "😒",
    "agresion": "⚠️",
    "tristeza": "😢",
    "manipulacion": "🚩",
    "control": "🔒",
    "ruptura": "💔",
    "desinteres": "😶",
    "inseguridad": "😟",
    "afecto": "💕",
    "curiosidad": "🤔",
    "normal": "💬",
}

EMOJIS_EMOCION = {
    "positivo": "😊",
    "tristeza": "😢",
    "enojo": "😠",
    "sorpresa": "😲",
    "disgusto": "😖",
    "miedo": "😨",
    "neutral": "😐",
}


# ─── CONFIGURACIÓN DE MEMORIA ───────────────────────────

MAX_HISTORIAL = 30

EMOCIONES_NEGATIVAS = {
    "tristeza",
    "enojo",
    "miedo",
    "disgusto"
}


# ─── FUNCIONES AUXILIARES ───────────────────────────────

def construir_barra(valor: int) -> str:
    bloques = max(0, min(10, valor // 10))
    return "█" * bloques + "░" * (10 - bloques)


def obtener_texto(diccionario, clave, default="normal"):
    return random.choice(diccionario.get(clave, diccionario[default]))


def formatear_respuesta(datos: dict) -> str:
    return (
        f"{datos['emoji_principal']} *Análisis del mensaje que te enviaron*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{datos['emoji_emocion']} *Emoción detectada:* {datos['emocion']}\n"
        f"🚩 *Discurso de odio:* {datos['toxicidad']}\n"
        f"🧠 *Intención:* {datos['intencion']}\n"
        f"📉 *Señales de distanciamiento:* {datos['ghosting_bar']} {datos['ghosting']}%\n"
        f"🔥 *Riesgo:* {datos['riesgo']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 *Qué significa:*\n{datos['interpretacion']}\n\n"
        f"💬 *Cómo responder:*\n{datos['sugerencia']}"
    )


# ─── MEMORIA INTELIGENTE ─────────────────────────────────

def guardar_en_historial(context, texto, datos):

    historial = context.user_data.setdefault("historial", [])

    historial.append({
        "texto": texto,
        "emocion": datos["emocion"].lower(),
        "intencion": datos["intencion"].lower(),
        "toxicidad": datos["toxicidad"],
        "riesgo": datos["riesgo"]
    })

    if len(historial) > MAX_HISTORIAL:
        del historial[:-MAX_HISTORIAL]


# ─── DETECTOR DE PATRONES ───────────────────────────────

def analizar_patrones(historial):

    if not historial:
        return "Todavía no hay suficientes mensajes para analizar."

    total = len(historial)

    emociones = Counter(
        mensaje["emocion"] for mensaje in historial
    )

    intenciones = Counter(
        mensaje["intencion"] for mensaje in historial
    )

    mensajes_toxicos = sum(
        1 for mensaje in historial
        if mensaje["toxicidad"] == "🔴 Alta"
    )

    mensajes_negativos = sum(
        1 for mensaje in historial
        if mensaje["emocion"] in EMOCIONES_NEGATIVAS
    )

    resultados = []

    # Emoción predominante
    emocion_principal, cantidad = emociones.most_common(1)[0]

    resultados.append(
        f"🧠 Emoción predominante: {emocion_principal.capitalize()} "
        f"({cantidad}/{total} mensajes)"
    )

    # Intención predominante
    intencion_principal, frecuencia = intenciones.most_common(1)[0]

    resultados.append(
        f"🎯 Intención más detectada: {intencion_principal.capitalize()} "
        f"({frecuencia} veces)"
    )

    # Toxicidad
    porcentaje_toxicidad = round(
        (mensajes_toxicos / total) * 100
    )

    resultados.append(
        f"🚩 Mensajes con toxicidad alta: {porcentaje_toxicidad}%"
    )

    # Emociones negativas
    porcentaje_negativo = round(
        (mensajes_negativos / total) * 100
    )

    resultados.append(
        f"📉 Mensajes con emociones negativas: {porcentaje_negativo}%"
    )

    # Patrones repetidos
    if frecuencia >= 3:
        resultados.append(
            f"🔁 Patrón repetido: se detectó {intencion_principal} "
            f"en {frecuencia} ocasiones."
        )

    if porcentaje_toxicidad >= 40:
        resultados.append(
            "⚠️ Hay una frecuencia importante de mensajes "
            "clasificados con toxicidad alta."
        )

    if porcentaje_negativo >= 60:
        resultados.append(
            "💔 Predominan las emociones negativas en el historial."
        )

    # Evolución emocional
    if total >= 4:

        mitad = total // 2

        primeros = historial[:mitad]
        ultimos = historial[mitad:]

        negativos_inicio = sum(
            1 for mensaje in primeros
            if mensaje["emocion"] in EMOCIONES_NEGATIVAS
        )

        negativos_final = sum(
            1 for mensaje in ultimos
            if mensaje["emocion"] in EMOCIONES_NEGATIVAS
        )

        if negativos_final > negativos_inicio:
            resultados.append(
                "📈 La segunda mitad de la conversación presenta "
                "más emociones negativas."
            )

        elif negativos_final < negativos_inicio:
            resultados.append(
                "📉 La segunda mitad presenta menos emociones negativas."
            )

        else:
            resultados.append(
                "➖ La presencia de emociones negativas se mantiene estable."
            )

    return "\n".join(resultados)


# ─── GENERAR RESUMEN ────────────────────────────────────

def generar_resumen(historial):

    total = len(historial)

    if total == 0:
        return "📭 Todavía no tienes mensajes guardados."

    patrones = analizar_patrones(historial)

    return (
        "🕵️ *DETECTIVE DE CONVERSACIONES*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📩 Mensajes analizados: {total}\n\n"
        "*📊 Patrones detectados:*\n"
        f"{patrones}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 Estos resultados son orientativos y dependen "
        "de los mensajes analizados."
    )


# ─── HANDLER PRINCIPAL ──────────────────────────────────

async def responder(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    try:

        # Si la calculadora está esperando números, la maneja ella
        if await procesar_calculadora(update, context):
            return

        texto = update.message.text
        context.user_data.pop("esperando_mensaje", None)

        emocion, toxicidad, ghosting, riesgo, intencion, confianza = (
            analizar_texto(texto)
        )

        datos = {
            "emoji_principal": EMOJIS.get(intencion, "💬"),
            "emoji_emocion": EMOJIS_EMOCION.get(emocion, "😐"),
            "emocion": emocion.capitalize(),
            "toxicidad": (
                "🔴 Alta" if toxicidad == "si" else "🟢 Baja"
            ),
            "intencion": intencion.capitalize(),
            "ghosting": ghosting,
            "ghosting_bar": construir_barra(ghosting),
            "riesgo": riesgo,
            "interpretacion": obtener_texto(
                INTERPRETACIONES,
                intencion
            ),
            "sugerencia": obtener_texto(
                SUGERENCIAS,
                intencion
            ),
        }

        # Guardar mensaje
        guardar_en_historial(
            context,
            texto,
            datos
        )

        respuesta = formatear_respuesta(datos)

        historial = context.user_data.get("historial", [])

        # Comparación con el mensaje anterior
        if len(historial) >= 2:

            emocion_anterior = historial[-2]["emocion"]
            emocion_actual = historial[-1]["emocion"]

            if emocion_anterior != emocion_actual:

                respuesta += (
                    "\n\n🔄 *Cambio emocional detectado:*\n"
                    f"La emoción cambió de {emocion_anterior} "
                    f"a {emocion_actual}."
                )

        # Activación del detective
        if len(historial) >= 5:

            respuesta += (
                "\n\n🕵️ *Detective:* Ya tengo suficiente historial "
                "para comenzar a detectar patrones. "
                "Escribe /resumen para verlos."
            )

        await update.message.reply_text(
            respuesta,
            parse_mode="Markdown"
        )

    except Exception as e:

        print(f"❌ Error: {e}")

        await update.message.reply_text(
            "⚠️ Ocurrió un error al procesar el mensaje."
        )


# ─── COMANDO RESUMEN ────────────────────────────────────

async def comando_resumen(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    historial = context.user_data.get("historial", [])

    respuesta = generar_resumen(historial)

    await update.message.reply_text(
        respuesta,
        parse_mode="Markdown"
    )


# ─── COMANDO REINICIAR ──────────────────────────────────

async def comando_reiniciar(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["historial"] = []

    await update.message.reply_text(
        "🧹 *Memoria reiniciada correctamente.*\n\n"
        "He borrado el historial de esta conversación. "
        "Puedes comenzar un nuevo análisis.",
        parse_mode="Markdown"
    )


# ─── INICIALIZACIÓN ─────────────────────────────────────

def main():

    print("🤖 Bot de análisis de mensajes activo...")
    print("📌 Analizo los mensajes que TE ENVÍAN.")
    print("🧠 Memoria inteligente activada.")
    print("📊 Comandos disponibles: /resumen y /reiniciar")

    app = ApplicationBuilder().token(TOKEN).build()

    # Comandos
    app.add_handler(CommandHandler("start", mostrar_menu))
    app.add_handler(CommandHandler("resumen", comando_resumen))
    app.add_handler(CommandHandler("reiniciar", comando_reiniciar))

    # Botones: cada handler solo recibe SUS callbacks gracias al pattern
    app.add_handler(
        CallbackQueryHandler(
            manejar_calculadora,
            pattern="^(calculadora|sumar|restar|multiplicar|dividir)$"
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            manejar_botones,
            pattern="^(analizar|resumen|patrones|reiniciar|ayuda|menu)$"
        )
    )

    # Mensajes de texto (calculadora + análisis)
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            responder
        )
    )

    print("🟢 Bot corriendo... Esperando mensajes.")

    app.run_polling()


if __name__ == "__main__":
    main()