import pandas as pd
import os
import openpyxl

def exportar_a_excel(ruta_salida, datos_dict, imagenes=None):
    """
    Guarda múltiples DataFrames o textos en distintas hojas de un Excel.

    datos_dict: dict con {"nombre_hoja": DataFrame o str}
    imagenes: lista opcional de rutas de imágenes a insertar
    """
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    with pd.ExcelWriter(ruta_salida, engine="openpyxl") as writer:
        for hoja, contenido in datos_dict.items():
            if isinstance(contenido, pd.DataFrame):
                contenido.to_excel(writer, sheet_name=hoja[:31], index=False)
            else:
                df = pd.DataFrame({"Contenido": [contenido]})
                df.to_excel(writer, sheet_name=hoja[:31], index=False)

        if imagenes:
            from openpyxl import load_workbook
            from openpyxl.drawing.image import Image as XLImage
            wb = load_workbook(ruta_salida)
            for i, img_path in enumerate(imagenes):
                if os.path.exists(img_path):
                    ws = wb.create_sheet(title=f"Grafico_{i+1}")
                    img = XLImage(img_path)
                    ws.add_image(img, "A1")
            wb.save(ruta_salida)
