# Notas Técnicas y Decisiones de Arquitectura

## Decisiones de Diseño

1. **Almacenamiento Local Robusto (IndexedDB con `idb-keyval`):**
   - Las capturas en alta resolución y los audios en base64 pueden superar rápidamente la cuota de 5MB de `localStorage`.
   - Se implementó `idb-keyval` para persistir múltiples tutoriales completos en IndexedDB sin límite restrictivo de almacenamiento y con autoguardado con debounce de 400ms.

2. **Compilador de Video en el Cliente (Canvas + MediaRecorder):**
   - Para evitar obligar al usuario a instalar binarios pesados de FFmpeg en Windows o configurar variables de entorno del sistema, el compilador genera el video usando el motor gráfico `<canvas>` (a 1920x1080) y la API estándar `MediaRecorder` con codecs VP9/VP8/Opus.
   - Sincroniza la duración de cada diapositiva con la duración real del archivo de audio del paso correspondiente.

3. **Guía HTML Autocontenida:**
   - La guía interactiva generada es un archivo `.html` 100% independiente.
   - No requiere servidor web, Node.js ni conexión a internet para ser abierta y consultada por cualquier usuario final en la organización.
