import qrcode
import os

def generar_codigo_qr():
    # URL de ejemplo. Cambiar por la URL real una vez desplegado en Streamlit Cloud
    url_por_defecto = "https://comedor-uni.streamlit.app"
    
    print("====================================================")
    print("   GENERADOR DE CÓDIGO QR - COMEDOR UNIVERSITARIO   ")
    print("====================================================")
    
    url = input(f"Introduce la URL definitiva de tu app\n(Presiona ENTER para usar '{url_por_defecto}'): ").strip()
    if not url:
        url = url_por_defecto
        
    print(f"\nGenerando código QR para: {url} ...")
    
    # Configuración de diseño del código QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H, # Alta tolerancia a fallos/daños (ideal para imprimir)
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    # Generar la imagen (negro sobre blanco)
    img = qr.make_image(fill_color="#1e1b4b", back_color="white") # Azul oscuro corporativo matching con la app
    
    nombre_archivo = "menu_qr.png"
    img.save(nombre_archivo)
    
    path_absoluto = os.path.abspath(nombre_archivo)
    print(f"\n¡Éxito! Imagen generada correctamente.")
    print(f"Guardada en: {path_absoluto}")
    print("====================================================")

if __name__ == "__main__":
    generar_codigo_qr()
