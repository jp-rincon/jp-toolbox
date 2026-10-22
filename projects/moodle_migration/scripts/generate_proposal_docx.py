import os
import shutil
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
docs_dir = os.path.join(base_dir, "docs")
logo_path = os.path.join(docs_dir, "LogoTeleint_Dark.png")
docx_output = os.path.join(docs_dir, "Propuesta_Tecnica_Migracion_Moodle.docx")
varios_docx = r"c:\Users\rinco\Documentos\Varios\Propuesta_Tecnica_Migracion_Moodle.docx"

# Color constants
COLOR_NAVY = RGBColor(0x1E, 0x3A, 0x8A)          # #1e3a8a
COLOR_PRIMARY_BLUE = RGBColor(0x1A, 0x56, 0xDB)  # #1a56db
COLOR_DARK = RGBColor(0x24, 0x29, 0x2E)          # #24292e
COLOR_MUTED = RGBColor(0x4B, 0x55, 0x63)         # #4b5563
COLOR_GRAY_LIGHT = RGBColor(0x64, 0x74, 0x8B)    # #64748b
COLOR_FOOTER = RGBColor(0x6B, 0x72, 0x80)        # #6b7280
COLOR_CODE = RGBColor(0x0F, 0x17, 0x2A)          # #0f172a
COLOR_BLUE_HOURS = RGBColor(0x1D, 0x4E, 0xD8)    # #1d4ed8

HEX_PRIMARY_BLUE = "1A56DB"
HEX_NAVY = "1E3A8A"
HEX_BG_GRAY = "F3F4F6"
HEX_BORDER_GRAY = "E5E7EB"
HEX_TABLE_BORDER = "D1D5DB"
HEX_TABLE_HEAD_BG = "F8FAFC"
HEX_TABLE_ALT_BG = "F9FAFB"
HEX_WARN_BG = "FFFBEB"
HEX_WARN_BORDER = "FDE68A"
HEX_WARN_LEFT = "F59E0B"
HEX_BENEFIT_BG = "F8FAFC"
HEX_BENEFIT_LEFT = "10B981"
HEX_TOTAL_BG = "F1F5F9"

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=160, right=160):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def set_cell_borders(cell, top=None, bottom=None, left=None, right=None):
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(f'<w:tcBorders {nsdecls("w")}/>')
    for side, border_spec in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        if border_spec:
            val, sz, space, color = border_spec
            b_elm = parse_xml(f'<w:{side} {nsdecls("w")} w:val="{val}" w:sz="{sz}" w:space="{space}" w:color="{color}"/>')
            tcBorders.append(b_elm)
        else:
            b_elm = parse_xml(f'<w:{side} {nsdecls("w")} w:val="none"/>')
            tcBorders.append(b_elm)
    tcPr.append(tcBorders)

def prevent_row_split(row):
    trPr = row._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

def set_repeat_header(row):
    trPr = row._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))

def add_h2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Segoe UI'
    run.font.size = Pt(11.5)
    run.font.bold = True
    run.font.color.rgb = COLOR_NAVY
    
    # Bottom border on H2
    pPr = p._p.get_or_add_pPr()
    pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="8" w:space="2" w:color="{HEX_BORDER_GRAY}"/></w:pBdr>')
    pPr.append(pBdr)
    return p

def add_h3(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(7)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Segoe UI'
    run.font.size = Pt(10)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)
    return p

def add_rich_bullet(doc, segments, space_after=2):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    for seg in segments:
        text = seg.get('text', '')
        r = p.add_run(text)
        r.font.name = seg.get('font', 'Segoe UI')
        r.font.size = Pt(seg.get('size', 9))
        r.font.bold = seg.get('bold', False)
        r.font.italic = seg.get('italic', False)
        if 'color' in seg:
            r.font.color.rgb = seg['color']
        else:
            r.font.color.rgb = COLOR_DARK
    return p

def add_warning_card_rich(doc, title, segments):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    cell = tbl.cell(0, 0)
    cell.width = Inches(7.16)
    set_cell_background(cell, HEX_WARN_BG)
    set_cell_margins(cell, top=100, bottom=100, left=160, right=140)
    set_cell_borders(cell,
        top=('single', '4', '0', HEX_WARN_BORDER),
        bottom=('single', '4', '0', HEX_WARN_BORDER),
        right=('single', '4', '0', HEX_WARN_BORDER),
        left=('single', '24', '0', HEX_WARN_LEFT)
    )
    prevent_row_split(tbl.rows[0])
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.2
    
    r_title = p.add_run(title + "\n")
    r_title.font.name = 'Segoe UI'
    r_title.font.size = Pt(9)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(0x92, 0x40, 0x0E)
    
    for seg in segments:
        text = seg.get('text', '')
        r = p.add_run(text)
        r.font.name = seg.get('font', 'Segoe UI')
        r.font.size = Pt(seg.get('size', 9))
        r.font.bold = seg.get('bold', False)
        r.font.italic = seg.get('italic', False)
        if 'color' in seg:
            r.font.color.rgb = seg['color']
        else:
            r.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)
            
    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.space_after = Pt(4)

def add_benefit_card(doc, title, content):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    cell = tbl.cell(0, 0)
    cell.width = Inches(7.16)
    set_cell_background(cell, HEX_BENEFIT_BG)
    set_cell_margins(cell, top=90, bottom=90, left=150, right=140)
    set_cell_borders(cell,
        top=None,
        bottom=None,
        right=None,
        left=('single', '22', '0', HEX_BENEFIT_LEFT)
    )
    prevent_row_split(tbl.rows[0])
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.2
    
    r_title = p.add_run(title + ": ")
    r_title.font.name = 'Segoe UI'
    r_title.font.size = Pt(9)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
    
    r_text = p.add_run(content)
    r_text.font.name = 'Segoe UI'
    r_text.font.size = Pt(9)
    r_text.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
    
    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.space_after = Pt(3)

def build_docx():
    doc = docx.Document()
    
    # Page Setup: A4, 12mm top/bottom, 14mm left/right
    for section in doc.sections:
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        section.top_margin = Inches(0.47)
        section.bottom_margin = Inches(0.47)
        section.left_margin = Inches(0.55)
        section.right_margin = Inches(0.55)
    
    # Base style
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Segoe UI'
    normal_style.font.size = Pt(9.5)
    normal_style.font.color.rgb = COLOR_DARK

    # ==========================================
    # PÁGINA 1: Header, Contexto, Arquitectura y Ruta
    # ==========================================
    
    # 1. Header (Logo + Title + Subtitle)
    if os.path.exists(logo_path):
        p_logo = doc.add_paragraph()
        p_logo.paragraph_format.space_before = Pt(0)
        p_logo.paragraph_format.space_after = Pt(2)
        run_logo = p_logo.add_run()
        run_logo.add_picture(logo_path, height=Pt(28.5))
    
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(2)
    p_title.paragraph_format.keep_with_next = True
    r_title = p_title.add_run("Plan Técnico de Migración y Modernización Moodle")
    r_title.font.name = 'Segoe UI'
    r_title.font.size = Pt(17)
    r_title.font.bold = True
    r_title.font.color.rgb = COLOR_NAVY
    
    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(6)
    p_sub.paragraph_format.keep_with_next = True
    r_sub = p_sub.add_run("Estrategia de salto generacional (v2.8.2 → v4.x LTS) y modernización de motor MySQL")
    r_sub.font.name = 'Segoe UI'
    r_sub.font.size = Pt(10)
    r_sub.font.color.rgb = COLOR_MUTED
    
    # Divider line under header (2.5px solid #1a56db)
    pPr = p_sub._p.get_or_add_pPr()
    pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="18" w:space="6" w:color="{HEX_PRIMARY_BLUE}"/></w:pBdr>')
    pPr.append(pBdr)

    # 2. Meta-box (3 columns: Estado Actual, Objetivo, Estrategia)
    meta_tbl = doc.add_table(rows=1, cols=3)
    meta_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_tbl.autofit = False
    
    meta_widths = [Inches(2.55), Inches(2.25), Inches(2.36)]
    meta_data = [
        ("Estado Actual: ", "Moodle 2.8.2 (2015) | PHP 5.6 | MySQL 5.5"),
        ("Objetivo: ", "Moodle 4.x LTS | PHP 8.2 | MySQL 8.0+"),
        ("Estrategia: ", "Migración escalonada en Docker Staging")
    ]
    
    for i, (col_label, col_val) in enumerate(meta_data):
        cell = meta_tbl.cell(0, i)
        cell.width = meta_widths[i]
        set_cell_background(cell, HEX_BG_GRAY)
        set_cell_margins(cell, top=90, bottom=90, left=120, right=120)
        if i == 0:
            set_cell_borders(cell, left=('single', '24', '0', HEX_PRIMARY_BLUE))
        else:
            set_cell_borders(cell)
        
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        r_lbl = p.add_run(col_label)
        r_lbl.font.bold = True
        r_lbl.font.size = Pt(8.5)
        r_val = p.add_run(col_val)
        r_val.font.size = Pt(8.5)
    
    prevent_row_split(meta_tbl.rows[0])
    
    # Space after meta box
    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.space_after = Pt(4)

    # 3. Sección 1: Resumen Ejecutivo y Objetivo
    add_h2(doc, "1. Resumen Ejecutivo y Objetivo")
    
    p1 = doc.add_paragraph()
    p1.paragraph_format.space_before = Pt(0)
    p1.paragraph_format.space_after = Pt(5)
    p1.paragraph_format.line_spacing = 1.18
    p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p1.add_run("El objetivo del proyecto es actualizar la plataforma educativa Moodle desde la versión heredada ")
    r = p1.add_run("2.8.2")
    r.font.bold = True
    p1.add_run(" hasta la versión de soporte extendido más reciente (")
    r = p1.add_run("Moodle 4.x LTS")
    r.font.bold = True
    p1.add_run("), modernizando simultáneamente el motor de base de datos desde ")
    r = p1.add_run("MySQL 5.5 a MySQL 8.0+")
    r.font.bold = True
    p1.add_run(" y el entorno de ejecución a ")
    r = p1.add_run("PHP 8.2")
    r.font.bold = True
    p1.add_run(".")

    p2 = doc.add_paragraph()
    p2.paragraph_format.space_before = Pt(0)
    p2.paragraph_format.space_after = Pt(6)
    p2.paragraph_format.line_spacing = 1.18
    p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p2.add_run("Dado que existen más de 9 años de evolución técnica entre ambas versiones, ")
    r = p2.add_run("no es posible técnicamente realizar un salto directo")
    r.font.bold = True
    p2.add_run(". Para garantizar la absoluta integridad de cursos, usuarios, historiales académicos y archivos, el proyecto se ejecutará mediante una ")
    r = p2.add_run("estrategia de migración escalonada (stepping stones)")
    r.font.bold = True
    p2.add_run(" utilizando contenedores ")
    r = p2.add_run("Docker")
    r.font.bold = True
    p2.add_run(" en entorno local de prueba/staging, asegurando cero riesgos de indisponibilidad o corrupción en la plataforma actual.")

    # 4. Sección 2: Ruta de Migración Obligatoria ("Stepping Stones")
    add_h2(doc, "2. Ruta de Migración Obligatoria (\"Stepping Stones\")")
    
    p_step_intro = doc.add_paragraph()
    p_step_intro.paragraph_format.space_before = Pt(0)
    p_step_intro.paragraph_format.space_after = Pt(6)
    p_step_intro.paragraph_format.line_spacing = 1.18
    p_step_intro.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_step_intro.add_run("El núcleo de Moodle restringe las actualizaciones a versiones intermedias mínimas obligatorias y depende estrechamente de versiones específicas de PHP y MySQL. A continuación se presenta la secuencia técnica requerida:")

    # Diagram Flow: 9-column table
    flow_tbl = doc.add_table(rows=1, cols=9)
    flow_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    flow_tbl.autofit = False
    
    nodes_info = [
        ("Origen: v2.8.2", "PHP 5.6\nMySQL 5.5", False, True, False),
        ("→", "", True, False, False),
        ("Hito 1: v3.2.9", "PHP 7.0 / 7.1\nMySQL 5.6", False, False, False),
        ("→", "", True, False, False),
        ("Hito 2: v3.9 LTS", "PHP 7.4\nMySQL 5.7", False, False, False),
        ("→", "", True, False, False),
        ("Hito 3: v4.1 LTS", "PHP 8.0 / 8.1\nMySQL 8.0", False, False, False),
        ("→", "", True, False, False),
        ("Meta: v4.x LTS", "PHP 8.2\nMySQL 8.0+", False, False, True),
    ]
    
    widths_flow = [Inches(1.28), Inches(0.20), Inches(1.28), Inches(0.20), Inches(1.28), Inches(0.20), Inches(1.28), Inches(0.20), Inches(1.28)]
    
    for i, (title, sub, is_arrow, is_init, is_tgt) in enumerate(nodes_info):
        cell = flow_tbl.cell(0, i)
        cell.width = widths_flow[i]
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        
        if is_arrow:
            set_cell_margins(cell, top=60, bottom=60, left=20, right=20)
            set_cell_borders(cell)
            r = p.add_run(title)
            r.font.name = 'Segoe UI'
            r.font.size = Pt(11)
            r.font.bold = True
            r.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)
        else:
            set_cell_margins(cell, top=70, bottom=70, left=40, right=40)
            if is_init:
                set_cell_background(cell, "FEF2F2")
                set_cell_borders(cell,
                    top=('single', '8', '0', 'EF4444'),
                    bottom=('single', '8', '0', 'EF4444'),
                    left=('single', '8', '0', 'EF4444'),
                    right=('single', '8', '0', 'EF4444'))
            elif is_tgt:
                set_cell_background(cell, "F0FDF4")
                set_cell_borders(cell,
                    top=('single', '8', '0', '10B981'),
                    bottom=('single', '8', '0', '10B981'),
                    left=('single', '8', '0', '10B981'),
                    right=('single', '8', '0', '10B981'))
            else:
                set_cell_background(cell, "FFFFFF")
                set_cell_borders(cell,
                    top=('single', '8', '0', 'CBD5E1'),
                    bottom=('single', '8', '0', 'CBD5E1'),
                    left=('single', '8', '0', 'CBD5E1'),
                    right=('single', '8', '0', 'CBD5E1'))
            
            r_t = p.add_run(title + "\n")
            r_t.font.name = 'Segoe UI'
            r_t.font.size = Pt(8.5)
            r_t.font.bold = True
            r_t.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
            
            r_s = p.add_run(sub)
            r_s.font.name = 'Segoe UI'
            r_s.font.size = Pt(7.5)
            r_s.font.color.rgb = RGBColor(0x47, 0x55, 0x69)
            
    prevent_row_split(flow_tbl.rows[0])
    
    # Spacing between diagram and table
    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.space_after = Pt(6)

    # Stepping Stones Table
    step_rows = [
        ("Línea Base", "2.8.2+", "PHP 5.6", "MySQL 5.5", "Levantamiento de réplica fiel y validación de datos originales."),
        ("Hito 1", "3.2.9 (Bridge)", "PHP 7.0 / 7.1", "MySQL 5.6 / 5.7", "Transición inicial de motor; migración de tablas del núcleo."),
        ("Hito 2", "3.9.x LTS", "PHP 7.4", "MySQL 5.7", "Conversión crítica utf8mb4 (Unicode completo) y Barracuda InnoDB."),
        ("Hito 3", "4.1.x LTS", "PHP 8.1", "MySQL 8.0", "Adopción de la nueva arquitectura Moodle 4 y tema Boost."),
        ("Hito 4 (Meta)", "4.5 LTS (o 4.4)", "PHP 8.2", "MySQL 8.0+", "Versión final con soporte a largo plazo, segura y optimizada.")
    ]
    
    step_tbl = doc.add_table(rows=len(step_rows)+1, cols=5)
    step_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    step_tbl.autofit = False
    
    step_widths = [Inches(1.00), Inches(1.30), Inches(1.20), Inches(1.30), Inches(2.36)]
    headers_step = ["Etapa", "Versión Moodle", "Versión PHP", "Versión MySQL", "Objetivo Principal"]
    
    # Header row
    hdr_row = step_tbl.rows[0]
    set_repeat_header(hdr_row)
    prevent_row_split(hdr_row)
    for col_idx, h_text in enumerate(headers_step):
        cell = hdr_row.cells[col_idx]
        cell.width = step_widths[col_idx]
        set_cell_background(cell, HEX_TABLE_HEAD_BG)
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        set_cell_borders(cell,
            top=('single', '6', '0', HEX_TABLE_BORDER),
            bottom=('single', '10', '0', HEX_TABLE_BORDER),
            left=('single', '6', '0', HEX_TABLE_BORDER),
            right=('single', '6', '0', HEX_TABLE_BORDER)
        )
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(h_text)
        run.font.bold = True
        run.font.size = Pt(8.5)
        run.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
        
    for r_idx, row_vals in enumerate(step_rows):
        row = step_tbl.rows[r_idx + 1]
        prevent_row_split(row)
        bg = HEX_TABLE_ALT_BG if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row_vals):
            cell = row.cells[c_idx]
            cell.width = step_widths[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=70, bottom=70, left=100, right=100)
            set_cell_borders(cell,
                top=('single', '4', '0', HEX_TABLE_BORDER),
                bottom=('single', '4', '0', HEX_TABLE_BORDER),
                left=('single', '4', '0', HEX_TABLE_BORDER),
                right=('single', '4', '0', HEX_TABLE_BORDER)
            )
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.15
            
            if "Conversión crítica utf8mb4" in val:
                r1 = p.add_run("Conversión crítica utf8mb4")
                r1.font.bold = True
                r1.font.size = Pt(8.5)
                r2 = p.add_run(" (Unicode completo) y Barracuda InnoDB.")
                r2.font.size = Pt(8.5)
            else:
                run = p.add_run(val)
                run.font.size = Pt(8.5)
                if c_idx == 0:
                    run.font.bold = True

    # ==========================================
    # PÁGINA 2: Factores Críticos y Metodología por Fases
    # ==========================================
    doc.add_page_break()
    
    add_h2(doc, "3. Factores Críticos y Mitigación de Riesgos")
    
    add_warning_card_rich(doc, 
        "1. Codificación de Base de Datos (utf8 vs utf8mb4):",
        [
            {'text': "Moodle 2.8 utilizaba el juego "},
            {'text': "utf8", 'font': 'Consolas', 'bold': True},
            {'text': " antiguo de MySQL (3 bytes). Moodle moderno exige obligatoriamente "},
            {'text': "utf8mb4", 'font': 'Consolas', 'bold': True},
            {'text': " (soporte completo Unicode y emojis). Entre el Hito 1 y 2 se ejecutará el script de sistema "},
            {'text': "mysql_collation.php", 'font': 'Consolas', 'bold': True},
            {'text': " para convertir todas las tablas sin pérdida de caracteres."}
        ]
    )
    
    add_warning_card_rich(doc,
        "2. Plugins de Terceros y Temas Antiguos:",
        [
            {'text': "Los temas de Moodle 2.8 (como Clean o Canvas) quedaron obsoletos y fueron eliminados en Moodle 4. Los temas y plugins incompatibles serán auditados previamente. Se migrará al tema estándar "},
            {'text': "Boost", 'italic': True, 'bold': True},
            {'text': " para asegurar estabilidad y modernidad visual responsiva."}
        ]
    )
    
    add_warning_card_rich(doc,
        "3. Ejecución por Consola CLI (Cero Timeouts):",
        [
            {'text': "Las actualizaciones masivas de base de datos nunca se ejecutarán a través del navegador web para evitar interrupciones por límite de tiempo (HTTP 504 / Max Execution Time). Se realizarán mediante el comando nativo "},
            {'text': "php admin/cli/upgrade.php", 'font': 'Consolas', 'bold': True},
            {'text': "."}
        ]
    )
    
    add_h2(doc, "4. Metodología de Ejecución por Fases")
    
    add_h3(doc, "Fase 1: Preparación del Entorno Local y Réplica en Docker")
    add_rich_bullet(doc, [
        {'text': "Configuración de un entorno reproducible con "},
        {'text': "docker-compose", 'font': 'Consolas', 'bold': True},
        {'text': " simulando el servidor original (PHP 5.6 + Apache + MySQL 5.5)."}
    ])
    add_rich_bullet(doc, [
        {'text': "Restauración de la copia de seguridad de la base de datos ("},
        {'text': ".sql", 'font': 'Consolas', 'bold': True},
        {'text': ") y de la carpeta de archivos del sistema ("},
        {'text': "moodledata/filedir", 'font': 'Consolas', 'bold': True},
        {'text': ")."}
    ])
    add_rich_bullet(doc, [
        {'text': "Validación funcional de la réplica: verificación de acceso administrador, catálogo de cursos, usuarios y recursos adjuntos."}
    ])
    
    add_h3(doc, "Fase 2: Auditoría y Saneamiento Previo")
    add_rich_bullet(doc, [
        {'text': "Inventario de módulos, actividades y bloques de terceros instalados en 2.8.2."}
    ])
    add_rich_bullet(doc, [
        {'text': "Desinstalación o desactivación controlada de extensiones huérfanas que no cuenten con soporte para Moodle 4."}
    ])
    add_rich_bullet(doc, [
        {'text': "Configuración del tema predeterminado del sistema y generación del "},
        {'text': "Snapshot 0", 'italic': True, 'bold': True},
        {'text': " limpio."}
    ])
    
    add_h3(doc, "Fase 3: Proceso de Migración Escalonada (Stepping Stones)")
    add_rich_bullet(doc, [
        {'text': "Paso 3.1: ", 'bold': True},
        {'text': "Actualización controlada a "},
        {'text': "Moodle 3.2.9", 'bold': True},
        {'text': " con PHP 7.1."}
    ])
    add_rich_bullet(doc, [
        {'text': "Paso 3.2: ", 'bold': True},
        {'text': "Ajuste de parámetros de motor MySQL ("},
        {'text': "innodb_large_prefix", 'font': 'Consolas'},
        {'text': ", "},
        {'text': "innodb_file_format=Barracuda", 'font': 'Consolas'},
        {'text': ") y conversión a "},
        {'text': "utf8mb4_unicode_ci", 'font': 'Consolas', 'bold': True},
        {'text': "."}
    ])
    add_rich_bullet(doc, [
        {'text': "Paso 3.3: ", 'bold': True},
        {'text': "Salto a "},
        {'text': "Moodle 3.9 LTS", 'bold': True},
        {'text': " (PHP 7.4) y generación de respaldo intermedio verificado."}
    ])
    add_rich_bullet(doc, [
        {'text': "Paso 3.4: ", 'bold': True},
        {'text': "Salto a "},
        {'text': "Moodle 4.1 LTS", 'bold': True},
        {'text': " sobre MySQL 8.0 y PHP 8.1."}
    ])
    add_rich_bullet(doc, [
        {'text': "Paso 3.5: ", 'bold': True},
        {'text': "Salto final a la versión objetivo "},
        {'text': "Moodle 4.x LTS", 'bold': True},
        {'text': " (PHP 8.2)."}
    ])
    
    add_h3(doc, "Fase 4: Verificación de Calidad y Pruebas de Integridad (QA)")
    add_rich_bullet(doc, [
        {'text': "Comprobación de integridad de cursos, matrículas de estudiantes y calificaciones históricas."}
    ])
    add_rich_bullet(doc, [
        {'text': "Verificación del repositorio de archivos (descarga correcta de documentos y materiales didácticos)."}
    ])
    add_rich_bullet(doc, [
        {'text': "Validación del funcionamiento de tareas cron y optimización de índices de base de datos."}
    ])
    
    add_h3(doc, "Fase 5: Despliegue en el Nuevo Servidor y Puesta en Marcha")
    add_rich_bullet(doc, [
        {'text': "Coordinación técnica sobre el nuevo servidor destino suministrado y configurado por el cliente (con sistema operativo y certificado SSL ya habilitados)."}
    ])
    add_rich_bullet(doc, [
        {'text': "Instalación y despliegue integral de la aplicación Moodle modernizada en el entorno final."}
    ])
    add_rich_bullet(doc, [
        {'text': "Configuración y optimización de parámetros del motor de Base de Datos (MySQL 8.0) para producción."}
    ])
    add_rich_bullet(doc, [
        {'text': "Sincronización final de datos (delta), migración de repositorio de archivos y verificaciones funcionales de salida."}
    ])

    # ==========================================
    # PÁGINA 3: Beneficios y Cuadro de Inversión
    # ==========================================
    doc.add_page_break()
    
    add_h2(doc, "5. Beneficios para la Organización")
    
    add_benefit_card(doc, "Seguridad y Cumplimiento", "Eliminación de vulnerabilidades críticas asociadas a versiones sin soporte oficial.")
    add_benefit_card(doc, "Compatibilidad Multiplataforma", "Interfaz gráfica moderna, accesible y 100% adaptable a dispositivos móviles.")
    add_benefit_card(doc, "Rendimiento Significativo", "Mejoras drásticas en tiempos de respuesta gracias a PHP 8.2 y optimizaciones MySQL 8.0.")
    add_benefit_card(doc, "Cero Riesgo de Pérdida de Datos", "Procedimiento con puntos de restauración garantizados mediante Docker antes de producción.")
    
    add_h2(doc, "6. Cuadro General de Actividades, Tiempos e Inversión Estimada")
    
    p_bud_intro = doc.add_paragraph()
    p_bud_intro.paragraph_format.space_before = Pt(0)
    p_bud_intro.paragraph_format.space_after = Pt(6)
    p_bud_intro.paragraph_format.line_spacing = 1.18
    p_bud_intro.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_bud_intro.add_run("A continuación se presenta el resumen global de las actividades requeridas para la ejecución integral del proyecto, la dedicación técnica estimada en horas y la inversión económica correspondiente calculada sobre una tarifa de ")
    r_rate = p_bud_intro.add_run("US $25 / hora")
    r_rate.font.bold = True
    p_bud_intro.add_run(":")

    # Budget Table
    budget_items = [
        ("01", "Fase 1: Preparación Staging y Réplica Base", "Levantamiento de infraestructura aislada Docker (PHP 5.6 + MySQL 5.5), restauración fiel de BD (179 MB) y moodledata (9.2 GB). Validación de accesos y estado inicial.", "15 Horas", "US $375"),
        ("02", "Fase 2: Auditoría y Saneamiento Previo", "Inventario de módulos y temas obsoletos, desinstalación de plugins no soportados para Moodle 4.x y generación de Snapshot 0 seguro de restauración.", "20 Horas", "US $500"),
        ("03", "Fase 3: Migración Escalonada (Stepping Stones)", "Actualizaciones progresivas por hitos vía CLI (2.8 → 3.2 → 3.9 → 4.1 → 4.x), conversión de esquemas a utf8mb4_unicode_ci y transición a MySQL 8.0.", "40 Horas", "US $1,000"),
        ("04", "Fase 4: Control de Calidad y Pruebas (QA)", "Verificación exhaustiva de 25 cursos, matrícula de 1.609 usuarios, historial académico de calificaciones, repositorios de archivos y validación del cron.", "20 Horas", "US $500"),
        ("05", "Fase 5: Despliegue en Servidor y Puesta en Marcha", "Instalación de la aplicación modernizada en servidor suministrado y preparado por el cliente, configuración de BD MySQL 8.0, migración final y verificaciones de salida.", "20 Horas", "US $500")
    ]
    
    bud_tbl = doc.add_table(rows=len(budget_items) + 2, cols=5)
    bud_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    bud_tbl.autofit = False
    
    bud_widths = [Inches(0.48), Inches(1.80), Inches(2.95), Inches(0.95), Inches(0.98)]
    headers_bud = ["Ítem", "Fase / Actividad Global", "Alcance Global y Entregables Principales", "Tiempo Est.", "Inversión Est."]
    
    # Header row
    hdr_row = bud_tbl.rows[0]
    set_repeat_header(hdr_row)
    prevent_row_split(hdr_row)
    for c_idx, h_text in enumerate(headers_bud):
        cell = hdr_row.cells[c_idx]
        cell.width = bud_widths[c_idx]
        set_cell_background(cell, HEX_NAVY)
        set_cell_margins(cell, top=100, bottom=100, left=100, right=100)
        set_cell_borders(cell,
            top=('single', '6', '0', HEX_NAVY),
            bottom=('single', '12', '0', HEX_NAVY),
            left=('single', '4', '0', '3B82F6'),
            right=('single', '4', '0', '3B82F6')
        )
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        if c_idx == 0 or c_idx == 3:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif c_idx == 4:
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        else:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            
        run = p.add_run(h_text)
        run.font.bold = True
        run.font.size = Pt(8.5)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        
    for r_idx, (item_num, phase_title, scope_desc, time_est, price_est) in enumerate(budget_items):
        row = bud_tbl.rows[r_idx + 1]
        prevent_row_split(row)
        bg = HEX_TABLE_ALT_BG if r_idx % 2 == 1 else "FFFFFF"
        
        # Cell 0: Item
        c0 = row.cells[0]
        c0.width = bud_widths[0]
        set_cell_background(c0, bg)
        set_cell_margins(c0, top=80, bottom=80, left=60, right=60)
        set_cell_borders(c0,
            top=('single', '4', '0', HEX_TABLE_BORDER),
            bottom=('single', '4', '0', HEX_TABLE_BORDER),
            left=('single', '4', '0', HEX_TABLE_BORDER),
            right=('single', '4', '0', HEX_TABLE_BORDER)
        )
        p0 = c0.paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p0.paragraph_format.space_before = Pt(0)
        p0.paragraph_format.space_after = Pt(0)
        r0 = p0.add_run(item_num)
        r0.font.bold = True
        r0.font.size = Pt(8.5)
        
        # Cell 1: Phase Title
        c1 = row.cells[1]
        c1.width = bud_widths[1]
        set_cell_background(c1, bg)
        set_cell_margins(c1, top=80, bottom=80, left=80, right=80)
        set_cell_borders(c1,
            top=('single', '4', '0', HEX_TABLE_BORDER),
            bottom=('single', '4', '0', HEX_TABLE_BORDER),
            left=('single', '4', '0', HEX_TABLE_BORDER),
            right=('single', '4', '0', HEX_TABLE_BORDER)
        )
        p1 = c1.paragraphs[0]
        p1.paragraph_format.space_before = Pt(0)
        p1.paragraph_format.space_after = Pt(0)
        p1.paragraph_format.line_spacing = 1.15
        r1 = p1.add_run(phase_title)
        r1.font.bold = True
        r1.font.size = Pt(8.5)
        r1.font.color.rgb = COLOR_DARK
        
        # Cell 2: Scope
        c2 = row.cells[2]
        c2.width = bud_widths[2]
        set_cell_background(c2, bg)
        set_cell_margins(c2, top=80, bottom=80, left=80, right=80)
        set_cell_borders(c2,
            top=('single', '4', '0', HEX_TABLE_BORDER),
            bottom=('single', '4', '0', HEX_TABLE_BORDER),
            left=('single', '4', '0', HEX_TABLE_BORDER),
            right=('single', '4', '0', HEX_TABLE_BORDER)
        )
        p2 = c2.paragraphs[0]
        p2.paragraph_format.space_before = Pt(0)
        p2.paragraph_format.space_after = Pt(0)
        p2.paragraph_format.line_spacing = 1.15
        p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        
        # Format scope with code styles if applicable
        if "utf8mb4_unicode_ci" in scope_desc:
            r2_1 = p2.add_run("Actualizaciones progresivas por hitos vía CLI (2.8 → 3.2 → 3.9 → 4.1 → 4.x), conversión de esquemas a ")
            r2_1.font.size = Pt(8.5)
            r2_2 = p2.add_run("utf8mb4_unicode_ci")
            r2_2.font.name = 'Consolas'
            r2_2.font.bold = True
            r2_2.font.size = Pt(8.5)
            r2_3 = p2.add_run(" y transición a MySQL 8.0.")
            r2_3.font.size = Pt(8.5)
        else:
            r2 = p2.add_run(scope_desc)
            r2.font.size = Pt(8.5)
            r2.font.color.rgb = COLOR_DARK
        
        # Cell 3: Time
        c3 = row.cells[3]
        c3.width = bud_widths[3]
        set_cell_background(c3, bg)
        set_cell_margins(c3, top=80, bottom=80, left=60, right=60)
        set_cell_borders(c3,
            top=('single', '4', '0', HEX_TABLE_BORDER),
            bottom=('single', '4', '0', HEX_TABLE_BORDER),
            left=('single', '4', '0', HEX_TABLE_BORDER),
            right=('single', '4', '0', HEX_TABLE_BORDER)
        )
        p3 = c3.paragraphs[0]
        p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p3.paragraph_format.space_before = Pt(0)
        p3.paragraph_format.space_after = Pt(0)
        r3 = p3.add_run(time_est)
        r3.font.bold = True
        r3.font.size = Pt(8.5)
        r3.font.color.rgb = COLOR_BLUE_HOURS
        
        # Cell 4: Price
        c4 = row.cells[4]
        c4.width = bud_widths[4]
        set_cell_background(c4, bg)
        set_cell_margins(c4, top=80, bottom=80, left=80, right=80)
        set_cell_borders(c4,
            top=('single', '4', '0', HEX_TABLE_BORDER),
            bottom=('single', '4', '0', HEX_TABLE_BORDER),
            left=('single', '4', '0', HEX_TABLE_BORDER),
            right=('single', '4', '0', HEX_TABLE_BORDER)
        )
        p4 = c4.paragraphs[0]
        p4.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p4.paragraph_format.space_before = Pt(0)
        p4.paragraph_format.space_after = Pt(0)
        r4 = p4.add_run(price_est)
        r4.font.name = 'Consolas'
        r4.font.bold = True
        r4.font.size = Pt(9)
        r4.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    # Total Row
    tot_row = bud_tbl.rows[len(budget_items) + 1]
    prevent_row_split(tot_row)
    
    # Merge cells 0, 1, 2
    cell_tot_label = tot_row.cells[0]
    cell_tot_label.merge(tot_row.cells[1])
    cell_tot_label.merge(tot_row.cells[2])
    
    set_cell_background(cell_tot_label, HEX_TOTAL_BG)
    set_cell_margins(cell_tot_label, top=100, bottom=100, left=100, right=100)
    set_cell_borders(cell_tot_label,
        top=('single', '16', '0', HEX_NAVY),
        bottom=('single', '16', '0', HEX_NAVY),
        left=('single', '6', '0', HEX_NAVY),
        right=('single', '4', '0', HEX_TABLE_BORDER)
    )
    p_tot_lbl = cell_tot_label.paragraphs[0]
    p_tot_lbl.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_tot_lbl.paragraph_format.space_before = Pt(0)
    p_tot_lbl.paragraph_format.space_after = Pt(0)
    r_tl = p_tot_lbl.add_run("TOTAL GENERAL ESTIMADO DEL PROYECTO:")
    r_tl.font.bold = True
    r_tl.font.size = Pt(9.5)
    r_tl.font.color.rgb = COLOR_NAVY

    # Total Hours Cell
    c_tot_hrs = tot_row.cells[3]
    c_tot_hrs.width = bud_widths[3]
    set_cell_background(c_tot_hrs, HEX_TOTAL_BG)
    set_cell_margins(c_tot_hrs, top=100, bottom=100, left=60, right=60)
    set_cell_borders(c_tot_hrs,
        top=('single', '16', '0', HEX_NAVY),
        bottom=('single', '16', '0', HEX_NAVY),
        left=('single', '4', '0', HEX_TABLE_BORDER),
        right=('single', '4', '0', HEX_TABLE_BORDER)
    )
    p_th = c_tot_hrs.paragraphs[0]
    p_th.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_th.paragraph_format.space_before = Pt(0)
    p_th.paragraph_format.space_after = Pt(0)
    r_th = p_th.add_run("115 Horas")
    r_th.font.bold = True
    r_th.font.size = Pt(9.5)
    r_th.font.color.rgb = COLOR_NAVY

    # Total Price Cell
    c_tot_price = tot_row.cells[4]
    c_tot_price.width = bud_widths[4]
    set_cell_background(c_tot_price, HEX_TOTAL_BG)
    set_cell_margins(c_tot_price, top=100, bottom=100, left=80, right=80)
    set_cell_borders(c_tot_price,
        top=('single', '16', '0', HEX_NAVY),
        bottom=('single', '16', '0', HEX_NAVY),
        left=('single', '4', '0', HEX_TABLE_BORDER),
        right=('single', '6', '0', HEX_NAVY)
    )
    p_tp = c_tot_price.paragraphs[0]
    p_tp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_tp.paragraph_format.space_before = Pt(0)
    p_tp.paragraph_format.space_after = Pt(0)
    r_tp = p_tp.add_run("US $2,875")
    r_tp.font.name = 'Consolas'
    r_tp.font.bold = True
    r_tp.font.size = Pt(10)
    r_tp.font.color.rgb = COLOR_NAVY

    # Note
    p_note = doc.add_paragraph()
    p_note.paragraph_format.space_before = Pt(6)
    p_note.paragraph_format.space_after = Pt(14)
    p_note.paragraph_format.line_spacing = 1.15
    r_n1 = p_note.add_run("* ")
    r_n1.font.size = Pt(8)
    r_n1.font.color.rgb = COLOR_GRAY_LIGHT
    r_n2 = p_note.add_run("Nota: ")
    r_n2.font.bold = True
    r_n2.font.size = Pt(8)
    r_n2.font.color.rgb = COLOR_GRAY_LIGHT
    r_n3 = p_note.add_run("Los tiempos estimados se calculan sobre la volumetría confirmada en la réplica (25 cursos, 1.609 usuarios registrados y 9.2 GB en archivos). La tarifa profesional aplicada es de ")
    r_n3.font.size = Pt(8)
    r_n3.font.italic = True
    r_n3.font.color.rgb = COLOR_GRAY_LIGHT
    r_n4 = p_note.add_run("US $25 / hora")
    r_n4.font.bold = True
    r_n4.font.italic = True
    r_n4.font.size = Pt(8)
    r_n4.font.color.rgb = COLOR_GRAY_LIGHT
    r_n5 = p_note.add_run(". El cliente suministra el servidor destino con sistema operativo y certificado SSL debidamente configurados.")
    r_n5.font.size = Pt(8)
    r_n5.font.italic = True
    r_n5.font.color.rgb = COLOR_GRAY_LIGHT

    # Footer
    p_foot = doc.add_paragraph()
    p_foot.paragraph_format.space_before = Pt(12)
    p_foot.paragraph_format.space_after = Pt(0)
    p_foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Border on footer
    pPr_f = p_foot._p.get_or_add_pPr()
    pBdr_f = parse_xml(f'<w:pBdr {nsdecls("w")}><w:top w:val="single" w:sz="6" w:space="6" w:color="{HEX_BORDER_GRAY}"/></w:pBdr>')
    pPr_f.append(pBdr_f)
    
    r_f = p_foot.add_run("Propuesta Técnica y Comercial • Migración Moodle 2.8.2 a Moodle 4.x LTS • Preparado por Teleint para revisión técnica y ejecutiva")
    r_f.font.name = 'Segoe UI'
    r_f.font.size = Pt(8)
    r_f.font.color.rgb = COLOR_FOOTER

    # Save
    doc.save(docx_output)
    print(f"Generated DOCX successfully: {docx_output}")
    print(f"File size: {os.path.getsize(docx_output)} bytes")
    
    if os.path.exists(os.path.dirname(varios_docx)):
        shutil.copy2(docx_output, varios_docx)
        print(f"Copied to: {varios_docx}")

if __name__ == '__main__':
    build_docx()
