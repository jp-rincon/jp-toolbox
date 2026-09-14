import subprocess
import os
import shutil

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
docs_dir = os.path.join(base_dir, "docs")

edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
html_path = os.path.join(docs_dir, "Propuesta_Tecnica_Migracion_Moodle.html")
pdf_path = os.path.join(docs_dir, "Propuesta_Tecnica_Migracion_Moodle.pdf")

cmd = [
    edge_path,
    "--headless",
    "--disable-gpu",
    "--no-pdf-header-footer",
    f"--print-to-pdf={pdf_path}",
    html_path
]

print("Running command:", " ".join(cmd))
res = subprocess.run(cmd, capture_output=True, text=True)
print("Return code:", res.returncode)
print("File size:", os.path.getsize(pdf_path))

# Also sync to user's Documentos\Varios
varios_pdf = r"c:\Users\rinco\Documentos\Varios\Propuesta_Tecnica_Migracion_Moodle.pdf"
if os.path.exists(os.path.dirname(varios_pdf)):
    shutil.copy2(pdf_path, varios_pdf)
    print(f"Synced to: {varios_pdf}")

