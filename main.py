from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import openai
import os
import json
import logging
import re
import uvicorn

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s"
)

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

USE_MOCK = False  # 🔁 Activá/desactivá fácilmente


class CotizacionRequest(BaseModel):
    prompt: str
    servicios: list


@app.post("/cotizar")
def cotizar(data: CotizacionRequest):
    try:
        logging.info("🔹 Prompt recibido: %s", data.prompt)
        logging.info("🔹 Cantidad de servicios recibidos: %d", len(data.servicios))

        if USE_MOCK:
            # 🔧 Modo mock: devolvemos servicios individuales por día
            mock_itinerario = [
                {
                    "dia": 1,
                    "servicios": [
                        {
                            "id": 1,
                            "tipo": "Transfer",
                            "descripcion": "Transfer privado al hotel",
                            "precio": 12000,
                        },
                        {
                            "id": 2,
                            "tipo": "Cena",
                            "descripcion": "Cena romántica",
                            "precio": 15000,
                        },
                    ],
                },
                {
                    "dia": 2,
                    "servicios": [
                        {
                            "id": 3,
                            "tipo": "Tour",
                            "descripcion": "Excursión de día completo",
                            "precio": 25000,
                        }
                    ],
                },
                {
                    "dia": 3,
                    "servicios": [
                        {
                            "id": 4,
                            "tipo": "Hotel",
                            "descripcion": "Hotel boutique con desayuno",
                            "precio": 30000,
                        }
                    ],
                },
            ]

            estimado_total = sum(
                servicio["precio"]
                for dia in mock_itinerario
                for servicio in dia["servicios"]
            )

            return JSONResponse(
                content={
                    "itinerario": mock_itinerario,
                    "estimado_total": estimado_total,
                },
                media_type="application/json",
            )

        # 🔁 Modo real (IA)
        contexto = ""  # 🧠 ¡ESTO FALTABA!

        for s in data.servicios:
            contexto += (
                f"Servicio ID {s.get('id')} | Tipo: {s.get('tipo')} | Descripción: {s.get('descripcion')} | "
                f"Precio: ${s.get('precio')} | ID_Destino: {s.get('idDestino')} | ID_Proveedor: {s.get('idProveedor')} | ID_Servicio: {s.get('id')}\n"
            )
        contexto = contexto.strip()

        mensajes = [
            {
                "role": "system",
                "content": (
                    "Sos un asistente de viajes. Recibís un mensaje del cliente con destino, días, personas y presupuesto. "
                    "Tenés una lista de servicios disponibles (con sus IDs reales de destino, proveedor y servicio). "
                    "Tu tarea es armar un itinerario en formato JSON, donde cada día tenga una lista de servicios como este ejemplo:\n"
                    "{'itinerario': [{'dia': 1, 'servicios': ["
                    "{'id': 1, 'tipo': 'Tour', 'descripcion': 'Texto', 'precio': 12000, 'idDestino': 3, 'idProveedor': 5, 'idServicio': 12}"
                    "]}], 'estimado_total': 99999}\n"
                    "Cada servicio debe incluir idDestino, idProveedor e idServicio reales, los cuales ya te fueron proporcionados. No inventes nuevos valores. Devolvé solo el JSON sin comentarios ni explicaciones."
                    "Los IDs deben corresponder a los servicios originales que te pasé. No inventes nuevos IDs. "
                    "No incluyas texto adicional, solo el JSON limpio."
                ),
            },
            {
                "role": "user",
                "content": f"{contexto}\n\nPrompt del cliente: {data.prompt}",
            },
        ]

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo", messages=mensajes, temperature=0.7
        )

        resultado = response.choices[0].message.content
        logging.info("✅ Respuesta cruda IA: %s", resultado)

        # Extraer JSON del texto devuelto
        itinerario_json = extraer_json_desde_texto(resultado)
        if itinerario_json is None:
            raise ValueError("No se pudo extraer un JSON válido desde la respuesta.")

        return JSONResponse(content=itinerario_json, media_type="application/json")

    except Exception as e:
        logging.error("❌ Error al procesar la cotización: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def extraer_json_desde_texto(texto):
    markdown_match = re.search(r"```json\s*(\{.*?\})\s*```", texto, re.DOTALL)
    if markdown_match:
        try:
            return json.loads(markdown_match.group(1))
        except json.JSONDecodeError:
            logging.warning("⚠️ JSON inválido desde bloque markdown.")

    matches = re.findall(r"\{.*\}", texto, re.DOTALL)
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    return None


# Iniciar el servidor con uvicorn, escuchando en todas las interfaces
if __name__ == "__main__":
    logging.info("🚀 Iniciando la aplicación en el puerto 8000.")
    uvicorn.run(app, host="0.0.0.0", port=8000)
