-- ============================================================================
-- SCRIPT DE CORRECCIÓN DE ENCODING Y CARACTERES ESPECIALES (MOJIBAKE)
-- Archivo: fix_mojibake.sql
-- Objetivo: Corregir caracteres acentuados y especiales corruptos en name y display_name.
-- ============================================================================

SET jit = off;

CREATE OR REPLACE FUNCTION fix_mojibake(txt text)
RETURNS text AS $$
BEGIN
    IF txt IS NULL THEN
        RETURN NULL;
    END IF;
    
    -- Vocales acentuadas minúsculas
    txt := REPLACE(txt, '├®', 'é');
    txt := REPLACE(txt, '├║', 'ú');
    txt := REPLACE(txt, '├í', 'á');
    txt := REPLACE(txt, '├¡', 'í');
    txt := REPLACE(txt, '├│', 'ó');
    txt := REPLACE(txt, '├╝', 'ü');
    txt := REPLACE(txt, '├┤', 'ô');
    txt := REPLACE(txt, '├½', 'ë');
    
    -- Ñ y Mayúsculas
    txt := REPLACE(txt, '├▒', 'ñ');
    txt := REPLACE(txt, '├æ', 'Ñ');
    txt := REPLACE(txt, '├ü', 'Á');
    txt := REPLACE(txt, '├ñ', 'ä');
    txt := REPLACE(txt, '├Â', 'ö');
    txt := REPLACE(txt, '├▓', 'É');
    txt := REPLACE(txt, '├Ä', 'Í');
    
    -- Variaciones adicionales de acentos
    txt := REPLACE(txt, '├¿', 'é');
    txt := REPLACE(txt, '├»', 'í');
    txt := REPLACE(txt, '├á', 'á');
    txt := REPLACE(txt, '├ó', 'á');
    txt := REPLACE(txt, '├º', 'ç');
    txt := REPLACE(txt, '├¬', 'ê');
    txt := REPLACE(txt, '┼ô', 'ñ');
    
    -- Símbolos y puntuación
    txt := REPLACE(txt, '┬¬', 'ª');
    txt := REPLACE(txt, '┬║', 'º');
    txt := REPLACE(txt, '┬¿', '¿');
    txt := REPLACE(txt, '┬░', '°');
    txt := REPLACE(txt, '┬┤', '´');
    txt := REPLACE(txt, 'ÔÇÖ', '''');
    
    RETURN txt;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Aplicar la limpieza a las columnas name y display_name en geo_total
UPDATE geo_total 
SET name = fix_mojibake(name),
    display_name = fix_mojibake(display_name)
WHERE name LIKE '%├%' OR display_name LIKE '%├%' 
   OR name LIKE '%┬%' OR display_name LIKE '%┬%'
   OR name LIKE '%ÔÇÖ%' OR display_name LIKE '%ÔÇÖ%'
   OR name LIKE '%┼ô%' OR display_name LIKE '%┼ô%';

-- Aplicar la limpieza a la tabla gps_total
UPDATE gps_total 
SET name = fix_mojibake(name),
    display_name = fix_mojibake(display_name)
WHERE name LIKE '%├%' OR display_name LIKE '%├%' 
   OR name LIKE '%┬%' OR display_name LIKE '%┬%'
   OR name LIKE '%ÔÇÖ%' OR display_name LIKE '%ÔÇÖ%'
   OR name LIKE '%┼ô%' OR display_name LIKE '%┼ô%';
