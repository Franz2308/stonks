import os
import shutil
import time

src = r"C:\Users\Frank\Documents\antigravity\happy-carson\stonks\Finanzas Trabajo Parcial_Completo.docx"
dst = r"C:\Users\Frank\Documents\antigravity\happy-carson\stonks\Finanzas Trabajo Parcial.docx"

for i in range(10):
    try:
        shutil.copy2(src, dst)
        print(f"Exito: {dst} actualizado correctamente con la version completa.")
        break
    except Exception as e:
        time.sleep(1)
else:
    print(f"Aviso: El archivo principal sigue en uso por Microsoft Word. El archivo actualizado esta listo en: {src}")
