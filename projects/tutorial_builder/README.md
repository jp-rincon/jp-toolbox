# Tutorial Builder (Alternativa a Guidde / Scribe)

Herramienta modular para crear tutoriales paso a paso de aplicaciones como **Tobo4**, generando tanto **guías interactivas (HTML/PDF)** como **videos compilados (.mp4 / .webm)** con voz sincronizada.

Resuelve el problema de las herramientas de grabación continua: **si cometes un error en un paso, solo editas o regrabas ese paso específico en segundos**, sin tener que reiniciar todo el video desde el comienzo.

---

## Características Principales

1. **Captura Rápida (`Ctrl + V`):**
   - Tomas la captura de la pantalla con `PrtScn` o la herramienta de recortes de Windows.
   - En la aplicación, solo presionas `Ctrl + V` en el paso deseado y la imagen queda adjunta.
   - Botón opcional para capturar ventanas completas directamente desde el navegador.

2. **Marcador de Atención / Clic:**
   - Haz clic sobre cualquier parte de la imagen para colocar un punto rojo animado que indique exactamente dónde hacer clic.

3. **Grabación de Voz por Paso:**
   - Graba notas de audio individuales para cada instrucción con el micrófono del equipo.
   - Si te equivocas en lo que dijiste, das clic en **"Regrabar"** y solo reemplazas esos segundos de audio.
   - Opcional: Probar narración automática con voz sintética del navegador.

4. **Llamadas de Atención:**
   - Inserta tips (💡), advertencias importantes (⚠️) o notas de información (ℹ️) en cualquier paso.

5. **Doble Formato de Exportación:**
   - **Guía HTML Autocontenida:** Un único archivo `.html` con todas las capturas, textos y audios embebidos. Funciona sin internet, por correo, en red local o SharePoint. Incluye vista documento (imprimible en PDF) y modo presentador paso a paso.
   - **Video Compilado (.mp4 / .webm):** Ensambla automáticamente todas las capturas y pistas de audio en un video HD continuo generado localmente.

---

## Cómo Ejecutar en Desarrollo

Desde PowerShell en la carpeta de la aplicación:

```powershell
cd C:\Users\rinco\jp-toolbox\projects\tutorial_builder\app
npm run dev
```

Abre tu navegador en `http://localhost:5173`.
