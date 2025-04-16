# Generador de Cotizaciones - ANDA Travel

Este esqueleto de proyecto te permite generar cotizaciones personalizadas a partir de un prompt, usando IA y servicios cargados en una base de datos SQLite.

## ¿Cómo se usa?

1. Cloná el proyecto o descomprimí el zip.
2. Copiá `.env.example` como `.env` y colocá tu API Key de OpenAI.
3. Instalá los requisitos:

```bash
pip install -r requirements.txt
```

4. Ejecutá el generador:

```bash
python main.py
```

5. Ingresá un prompt como:

```
Luna de miel en Cataratas del Iguazú, deluxe, 2 personas, 3 días
```

La IA generará una propuesta técnica con IDs de servicios y la guardará como cotización.