import base64
import subprocess
import os
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
docs_dir = os.path.join(base_dir, "docs")
logo_path = os.path.join(docs_dir, "LogoTeleint_Dark.png")
with open(logo_path, "rb") as f:
    logo_b64 = base64.b64encode(f.read()).decode("utf-8")

html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  @page {{
    size: A4;
    margin: 12mm 14mm 12mm 14mm;
  }}
  * {{
    box-sizing: border-box;
  }}
  body {{
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    color: #24292e;
    line-height: 1.38;
    font-size: 10pt;
    margin: 0;
    padding: 0;
  }}
  .header {{
    border-bottom: 2.5px solid #1a56db;
    padding-bottom: 6px;
    margin-bottom: 10px;
  }}
  .header-logo {{
    margin-bottom: 4px;
  }}
  .header-logo img {{
    height: 38px;
    width: auto;
    display: block;
  }}
  .header h1 {{
    font-size: 17pt;
    color: #1e3a8a;
    margin: 0 0 2px 0;
    font-weight: 700;
    letter-spacing: -0.3px;
  }}
  .header .subtitle {{
    font-size: 10pt;
    color: #4b5563;
    font-weight: 500;
  }}
  .meta-box {{
    background-color: #f3f4f6;
    border-left: 3.5px solid #1a56db;
    padding: 6px 10px;
    margin-bottom: 10px;
    font-size: 8.5pt;
    display: flex;
    justify-content: space-between;
  }}
  h2 {{
    font-size: 11.5pt;
    color: #1e3a8a;
    border-bottom: 1.2px solid #e5e7eb;
    padding-bottom: 3px;
    margin-top: 10px;
    margin-bottom: 6px;
    page-break-after: avoid;
  }}
  h3 {{
    font-size: 10pt;
    color: #1f2937;
    margin-top: 7px;
    margin-bottom: 2px;
    page-break-after: avoid;
  }}
  p {{
    margin: 0 0 6px 0;
    text-align: justify;
    font-size: 9.5pt;
  }}
  ul, ol {{
    margin: 0 0 6px 0;
    padding-left: 18px;
  }}
  li {{
    margin-bottom: 2px;
    font-size: 9pt;
  }}
  .warning-card {{
    background-color: #fffbeb;
    border: 1px solid #fde68a;
    border-left: 3.5px solid #f59e0b;
    border-radius: 4px;
    padding: 7px 10px;
    margin: 6px 0;
    font-size: 9pt;
    line-height: 1.35;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 6px 0 8px 0;
    font-size: 8.5pt;
    page-break-inside: avoid;
  }}
  th, td {{
    border: 1px solid #d1d5db;
    padding: 5px 8px;
    text-align: left;
  }}
  th {{
    background-color: #f8fafc;
    color: #1e293b;
    font-weight: 600;
  }}
  tr:nth-child(even) {{
    background-color: #f9fafb;
  }}
  .diagram-flow {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 8px 4px;
    margin: 8px 0;
    text-align: center;
  }}
  .step-node {{
    flex: 1;
    background: #ffffff;
    border: 1.2px solid #cbd5e1;
    border-radius: 5px;
    padding: 5px 3px;
    margin: 0 2px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
  }}
  .step-node.initial {{ border-color: #ef4444; background: #fef2f2; }}
  .step-node.target {{ border-color: #10b981; background: #f0fdf4; }}
  .step-title {{ font-weight: 700; font-size: 9pt; color: #0f172a; margin-bottom: 1px; }}
  .step-sub {{ font-size: 7.5pt; color: #475569; line-height: 1.15; }}
  .step-arrow {{ font-size: 11pt; color: #94a3b8; font-weight: bold; flex: 0 0 12px; }}

  /* Estilos específicos para la tabla de Actividades e Inversión */
  .budget-table {{
    margin: 8px 0 5px 0;
    font-size: 8.5pt;
    page-break-inside: avoid;
  }}
  .budget-table th {{
    background-color: #1e3a8a;
    color: #ffffff;
    font-size: 8.5pt;
    padding: 7px 8px;
    text-align: left;
  }}
  .budget-table td {{
    padding: 6.5px 8px;
    vertical-align: middle;
  }}
  .budget-table .col-center {{
    text-align: center;
  }}
  .budget-table .col-right {{
    text-align: right;
  }}
  .budget-table .hours-badge {{
    display: inline-block;
    background-color: #eff6ff;
    color: #1d4ed8;
    border: 1px solid #bfdbfe;
    border-radius: 4px;
    padding: 2px 6px;
    font-weight: 700;
    font-size: 8.5pt;
  }}
  .budget-table .price-val {{
    font-family: 'Consolas', 'Segoe UI', monospace;
    font-weight: 600;
    color: #0f172a;
    font-size: 9pt;
  }}
  .budget-table tr.total-row {{
    background-color: #f1f5f9;
    border-top: 2px solid #1e3a8a;
    border-bottom: 2px solid #1e3a8a;
    font-size: 9.5pt;
    font-weight: 700;
  }}
  .budget-table tr.total-row td {{
    padding: 8px 8px;
    color: #1e3a8a;
  }}
  .budget-table tr.total-row .total-hours {{
    background-color: #1e3a8a;
    color: #ffffff;
    border-radius: 4px;
    padding: 3px 8px;
    display: inline-block;
    font-size: 9pt;
  }}
  .table-note {{
    font-size: 8pt;
    color: #64748b;
    margin-top: 5px;
    margin-bottom: 12px;
    font-style: italic;
    line-height: 1.3;
  }}
  .benefit-card {{
    background-color: #f8fafc;
    border-left: 3px solid #10b981;
    padding: 6px 10px;
    margin-bottom: 5px;
    font-size: 9pt;
    line-height: 1.35;
  }}
  .footer {{
    margin-top: 14px;
    border-top: 1px solid #e5e7eb;
    padding-top: 6px;
    font-size: 8pt;
    color: #6b7280;
    text-align: center;
  }}
  .page-break {{
    page-break-before: always;
  }}
</style>
</head>
<body>

<!-- PÁGINA 1: Contexto, Arquitectura y Ruta de Migración -->
<div class="header">
  <div class="header-logo">
    <img src="data:image/png;base64,{logo_b64}" alt="Teleint" />
  </div>
  <h1>Plan Técnico de Migración y Modernización Moodle</h1>
  <div class="subtitle">Estrategia de salto generacional (v2.8.2 → v4.x LTS) y modernización de motor MySQL</div>
</div>

<div class="meta-box">
  <div><strong>Estado Actual:</strong> Moodle 2.8.2 (2015) | PHP 5.6 | MySQL 5.5</div>
  <div><strong>Objetivo:</strong> Moodle 4.x LTS | PHP 8.2 | MySQL 8.0+</div>
  <div><strong>Estrategia:</strong> Migración escalonada en Docker Staging</div>
</div>

<h2>1. Resumen Ejecutivo y Objetivo</h2>
<p>
El objetivo del proyecto es actualizar la plataforma educativa Moodle desde la versión heredada <strong>2.8.2</strong> hasta la versión de soporte extendido más reciente (<strong>Moodle 4.x LTS</strong>), modernizando simultáneamente el motor de base de datos desde <strong>MySQL 5.5 a MySQL 8.0+</strong> y el entorno de ejecución a <strong>PHP 8.2</strong>.
</p>
<p>
Dado que existen más de 9 años de evolución técnica entre ambas versiones, <strong>no es posible técnicamente realizar un salto directo</strong>. Para garantizar la absoluta integridad de cursos, usuarios, historiales académicos y archivos, el proyecto se ejecutará mediante una <strong>estrategia de migración escalonada (stepping stones)</strong> utilizando contenedores <strong>Docker</strong> en entorno local de prueba/staging, asegurando cero riesgos de indisponibilidad o corrupción en la plataforma actual.
</p>

<h2>2. Ruta de Migración Obligatoria ("Stepping Stones")</h2>
<p>
El núcleo de Moodle restringe las actualizaciones a versiones intermedias mínimas obligatorias y depende estrechamente de versiones específicas de PHP y MySQL. A continuación se presenta la secuencia técnica requerida:
</p>

<div class="diagram-flow">
  <div class="step-node initial">
    <div class="step-title">Origen: v2.8.2</div>
    <div class="step-sub">PHP 5.6<br>MySQL 5.5</div>
  </div>
  <div class="step-arrow">→</div>
  <div class="step-node">
    <div class="step-title">Hito 1: v3.2.9</div>
    <div class="step-sub">PHP 7.0 / 7.1<br>MySQL 5.6</div>
  </div>
  <div class="step-arrow">→</div>
  <div class="step-node">
    <div class="step-title">Hito 2: v3.9 LTS</div>
    <div class="step-sub">PHP 7.4<br>MySQL 5.7</div>
  </div>
  <div class="step-arrow">→</div>
  <div class="step-node">
    <div class="step-title">Hito 3: v4.1 LTS</div>
    <div class="step-sub">PHP 8.0 / 8.1<br>MySQL 8.0</div>
  </div>
  <div class="step-arrow">→</div>
  <div class="step-node target">
    <div class="step-title">Meta: v4.x LTS</div>
    <div class="step-sub">PHP 8.2<br>MySQL 8.0+</div>
  </div>
</div>

<table>
  <thead>
    <tr>
      <th style="width: 14%;">Etapa</th>
      <th style="width: 18%;">Versión Moodle</th>
      <th style="width: 17%;">Versión PHP</th>
      <th style="width: 18%;">Versión MySQL</th>
      <th style="width: 33%;">Objetivo Principal</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Línea Base</strong></td>
      <td>2.8.2+</td>
      <td>PHP 5.6</td>
      <td>MySQL 5.5</td>
      <td>Levantamiento de réplica fiel y validación de datos originales.</td>
    </tr>
    <tr>
      <td><strong>Hito 1</strong></td>
      <td>3.2.9 (Bridge)</td>
      <td>PHP 7.0 / 7.1</td>
      <td>MySQL 5.6 / 5.7</td>
      <td>Transición inicial de motor; migración de tablas del núcleo.</td>
    </tr>
    <tr>
      <td><strong>Hito 2</strong></td>
      <td>3.9.x LTS</td>
      <td>PHP 7.4</td>
      <td>MySQL 5.7</td>
      <td><strong>Conversión crítica utf8mb4</strong> (Unicode completo) y Barracuda InnoDB.</td>
    </tr>
    <tr>
      <td><strong>Hito 3</strong></td>
      <td>4.1.x LTS</td>
      <td>PHP 8.1</td>
      <td>MySQL 8.0</td>
      <td>Adopción de la nueva arquitectura Moodle 4 y tema Boost.</td>
    </tr>
    <tr>
      <td><strong>Hito 4 (Meta)</strong></td>
      <td>4.5 LTS (o 4.4)</td>
      <td>PHP 8.2</td>
      <td>MySQL 8.0+</td>
      <td>Versión final con soporte a largo plazo, segura y optimizada.</td>
    </tr>
  </tbody>
</table>

<div class="page-break"></div>

<!-- PÁGINA 2: Factores Críticos y Metodología por Fases -->
<h2>3. Factores Críticos y Mitigación de Riesgos</h2>

<div class="warning-card">
  <strong>1. Codificación de Base de Datos (utf8 vs utf8mb4):</strong><br>
  Moodle 2.8 utilizaba el juego <code>utf8</code> antiguo de MySQL (3 bytes). Moodle moderno exige obligatoriamente <code>utf8mb4</code> (soporte completo Unicode y emojis). Entre el Hito 1 y 2 se ejecutará el script de sistema <code>mysql_collation.php</code> para convertir todas las tablas sin pérdida de caracteres.
</div>

<div class="warning-card">
  <strong>2. Plugins de Terceros y Temas Antiguos:</strong><br>
  Los temas de Moodle 2.8 (como Clean o Canvas) quedaron obsoletos y fueron eliminados en Moodle 4. Los temas y plugins incompatibles serán auditados previamente. Se migrará al tema estándar <em>Boost</em> para asegurar estabilidad y modernidad visual responsiva.
</div>

<div class="warning-card">
  <strong>3. Ejecución por Consola CLI (Cero Timeouts):</strong><br>
  Las actualizaciones masivas de base de datos nunca se ejecutarán a través del navegador web para evitar interrupciones por límite de tiempo (HTTP 504 / Max Execution Time). Se realizarán mediante el comando nativo <code>php admin/cli/upgrade.php</code>.
</div>

<h2>4. Metodología de Ejecución por Fases</h2>

<h3>Fase 1: Preparación del Entorno Local y Réplica en Docker</h3>
<ul>
  <li>Configuración de un entorno reproducible con <code>docker-compose</code> simulando el servidor original (PHP 5.6 + Apache + MySQL 5.5).</li>
  <li>Restauración de la copia de seguridad de la base de datos (<code>.sql</code>) y de la carpeta de archivos del sistema (<code>moodledata/filedir</code>).</li>
  <li>Validación funcional de la réplica: verificación de acceso administrador, catálogo de cursos, usuarios y recursos adjuntos.</li>
</ul>

<h3>Fase 2: Auditoría y Saneamiento Previo</h3>
<ul>
  <li>Inventario de módulos, actividades y bloques de terceros instalados en 2.8.2.</li>
  <li>Desinstalación o desactivación controlada de extensiones huérfanas que no cuenten con soporte para Moodle 4.</li>
  <li>Configuración del tema predeterminado del sistema y generación del <em>Snapshot 0</em> limpio.</li>
</ul>

<h3>Fase 3: Proceso de Migración Escalonada (Stepping Stones)</h3>
<ul>
  <li><strong>Paso 3.1:</strong> Actualización controlada a <strong>Moodle 3.2.9</strong> con PHP 7.1.</li>
  <li><strong>Paso 3.2:</strong> Ajuste de parámetros de motor MySQL (<code>innodb_large_prefix</code>, <code>innodb_file_format=Barracuda</code>) y conversión a <code>utf8mb4_unicode_ci</code>.</li>
  <li><strong>Paso 3.3:</strong> Salto a <strong>Moodle 3.9 LTS</strong> (PHP 7.4) y generación de respaldo intermedio verificado.</li>
  <li><strong>Paso 3.4:</strong> Salto a <strong>Moodle 4.1 LTS</strong> sobre MySQL 8.0 y PHP 8.1.</li>
  <li><strong>Paso 3.5:</strong> Salto final a la versión objetivo <strong>Moodle 4.x LTS</strong> (PHP 8.2).</li>
</ul>

<h3>Fase 4: Verificación de Calidad y Pruebas de Integridad (QA)</h3>
<ul>
  <li>Comprobación de integridad de cursos, matrículas de estudiantes y calificaciones históricas.</li>
  <li>Verificación del repositorio de archivos (descarga correcta de documentos y materiales didácticos).</li>
  <li>Validación del funcionamiento de tareas cron y optimización de índices de base de datos.</li>
</ul>

<h3>Fase 5: Despliegue en el Nuevo Servidor y Puesta en Marcha</h3>
<ul>
  <li>Coordinación técnica sobre el nuevo servidor destino suministrado y configurado por el cliente (con sistema operativo y certificado SSL ya habilitados).</li>
  <li>Instalación y despliegue integral de la aplicación Moodle modernizada en el entorno final.</li>
  <li>Configuración y optimización de parámetros del motor de Base de Datos (MySQL 8.0) para producción.</li>
  <li>Sincronización final de datos (delta), migración de repositorio de archivos y verificaciones funcionales de salida.</li>
</ul>

<div class="page-break"></div>

<!-- PÁGINA 3: Beneficios y Cuadro Global de Actividades e Inversión -->
<h2>5. Beneficios para la Organización</h2>

<div class="benefit-card">
  <strong>Seguridad y Cumplimiento:</strong> Eliminación de vulnerabilidades críticas asociadas a versiones sin soporte oficial.
</div>
<div class="benefit-card">
  <strong>Compatibilidad Multiplataforma:</strong> Interfaz gráfica moderna, accesible y 100% adaptable a dispositivos móviles.
</div>
<div class="benefit-card">
  <strong>Rendimiento Significativo:</strong> Mejoras drásticas en tiempos de respuesta gracias a PHP 8.2 y optimizaciones MySQL 8.0.
</div>
<div class="benefit-card">
  <strong>Cero Riesgo de Pérdida de Datos:</strong> Procedimiento con puntos de restauración garantizados mediante Docker antes de producción.
</div>

<h2>6. Cuadro General de Actividades, Tiempos e Inversión Estimada</h2>
<p>
A continuación se presenta el resumen global de las actividades requeridas para la ejecución integral del proyecto, la dedicación técnica estimada en horas y la inversión económica correspondiente calculada sobre una tarifa de <strong>US $25 / hora</strong>:
</p>

<table class="budget-table">
  <thead>
    <tr>
      <th style="width: 6%; text-align: center;">Ítem</th>
      <th style="width: 25%;">Fase / Actividad Global</th>
      <th style="width: 41%;">Alcance Global y Entregables Principales</th>
      <th style="width: 13%; text-align: center;">Tiempo Est.</th>
      <th style="width: 15%; text-align: right;">Inversión Est.</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td class="col-center"><strong>01</strong></td>
      <td><strong>Fase 1: Preparación Staging y Réplica Base</strong></td>
      <td>Levantamiento de infraestructura aislada Docker (PHP 5.6 + MySQL 5.5), restauración fiel de BD (179 MB) y moodledata (9.2 GB). Validación de accesos y estado inicial.</td>
      <td class="col-center"><span class="hours-badge">15 Horas</span></td>
      <td class="col-right"><span class="price-val">US $375</span></td>
    </tr>
    <tr>
      <td class="col-center"><strong>02</strong></td>
      <td><strong>Fase 2: Auditoría y Saneamiento Previo</strong></td>
      <td>Inventario de módulos y temas obsoletos, desinstalación de plugins no soportados para Moodle 4.x y generación de Snapshot 0 seguro de restauración.</td>
      <td class="col-center"><span class="hours-badge">20 Horas</span></td>
      <td class="col-right"><span class="price-val">US $500</span></td>
    </tr>
    <tr>
      <td class="col-center"><strong>03</strong></td>
      <td><strong>Fase 3: Migración Escalonada (Stepping Stones)</strong></td>
      <td>Actualizaciones progresivas por hitos vía CLI (2.8 → 3.2 → 3.9 → 4.1 → 4.x), conversión de esquemas a <code>utf8mb4_unicode_ci</code> y transición a MySQL 8.0.</td>
      <td class="col-center"><span class="hours-badge">40 Horas</span></td>
      <td class="col-right"><span class="price-val">US $1,000</span></td>
    </tr>
    <tr>
      <td class="col-center"><strong>04</strong></td>
      <td><strong>Fase 4: Control de Calidad y Pruebas (QA)</strong></td>
      <td>Verificación exhaustiva de 25 cursos, matrícula de 1.609 usuarios, historial académico de calificaciones, repositorios de archivos y validación del cron.</td>
      <td class="col-center"><span class="hours-badge">20 Horas</span></td>
      <td class="col-right"><span class="price-val">US $500</span></td>
    </tr>
    <tr>
      <td class="col-center"><strong>05</strong></td>
      <td><strong>Fase 5: Despliegue en Servidor y Puesta en Marcha</strong></td>
      <td>Instalación de la aplicación modernizada en servidor suministrado y preparado por el cliente, configuración de BD MySQL 8.0, migración final y verificaciones de salida.</td>
      <td class="col-center"><span class="hours-badge">20 Horas</span></td>
      <td class="col-right"><span class="price-val">US $500</span></td>
    </tr>
    <tr class="total-row">
      <td colspan="3" style="text-align: right; font-weight: 700;">TOTAL GENERAL ESTIMADO DEL PROYECTO:</td>
      <td class="col-center"><span class="total-hours">115 Horas</span></td>
      <td class="col-right" style="font-weight: 700; color: #1e3a8a;"><span class="price-val" style="color: #1e3a8a; font-size: 9.5pt;">US $2,875</span></td>
    </tr>
  </tbody>
</table>

<div class="table-note">
  * <strong>Nota:</strong> Los tiempos estimados se calculan sobre la volumetría confirmada en la réplica (25 cursos, 1.609 usuarios registrados y 9.2 GB en archivos). La tarifa profesional aplicada es de <strong>US $25 / hora</strong>. El cliente suministra el servidor destino con sistema operativo y certificado SSL debidamente configurados.
</div>

<div class="footer">
  Propuesta Técnica y Comercial • Migración Moodle 2.8.2 a Moodle 4.x LTS • Preparado por Teleint para revisión técnica y ejecutiva
</div>

</body>
</html>
"""

# Write to file
target_file = os.path.join(docs_dir, "Propuesta_Tecnica_Migracion_Moodle.html")
with open(target_file, "w", encoding="utf-8") as f:
    f.write(html_content)

print("Updated HTML written successfully to:", target_file)
