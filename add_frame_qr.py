from PIL import Image, ImageDraw, ImageFont
import os

def crear_qr_enmarcado():
    print("====================================================")
    print("      CREANDO MARCO PARA EL CÓDIGO QR...            ")
    print("====================================================")
    
    # 1. Cargar el QR original
    qr_path = "menu_qr.png"
    if not os.path.exists(qr_path):
        print(f"Error: No se encontró el archivo '{qr_path}'. Genera primero el QR.")
        return
        
    qr_img = Image.open(qr_path).convert("RGBA")
    qr_w, qr_h = qr_img.size  # Tamaño del QR (normalmente ~410x410 px)
    
    # 2. Configurar el tamaño del nuevo lienzo (tarjeta con marco)
    # Dejamos espacio para márgenes y texto abajo
    canvas_w = qr_w + 120  # Margen lateral de 60px a cada lado
    canvas_h = qr_h + 240  # Margen superior e inferior para el texto
    
    # Crear lienzo nuevo con color de fondo blanco limpio
    canvas = Image.new("RGBA", (canvas_w, canvas_h), "white")
    draw = ImageDraw.Draw(canvas)
    
    # 3. Dibujar borde exterior redondeado estilo tarjeta premium
    # Usaremos el color corporativo morado/índigo de la app (#1e1b4b)
    borde_color = "#1e1b4b"
    borde_ancho = 6
    draw.rounded_rectangle(
        [15, 15, canvas_w - 15, canvas_h - 15],
        radius=24,
        outline=borde_color,
        width=borde_ancho
    )
    
    # 4. Pegar el código QR centrado
    pos_x = (canvas_w - qr_w) // 2
    pos_y = 60  # Separación desde arriba
    canvas.paste(qr_img, (pos_x, pos_y), qr_img)
    
    # 5. Escribir los textos usando tipografía de Windows
    font_path = "C:\\Windows\\Fonts\\segoeui.ttf"  # Fuente limpia y moderna de Windows
    if not os.path.exists(font_path):
        font_path = "C:\\Windows\\Fonts\\arial.ttf"  # Fallback estándar
        
    try:
        # Cargar fuentes a diferentes tamaños
        font_titulo = ImageFont.truetype(font_path, 36)
        font_subtitulo = ImageFont.truetype(font_path, 20)
        
        # Texto Principal: ¡RESERVA AHORA!
        texto_titulo = "¡RESERVA AHORA!"
        # Obtener caja de texto para centrarlo
        bbox = draw.textbbox((0, 0), texto_titulo, font=font_titulo)
        txt_w = bbox[2] - bbox[0]
        x_tit = (canvas_w - txt_w) // 2
        y_tit = pos_y + qr_h + 30
        draw.text((x_tit, y_tit), texto_titulo, font=font_titulo, fill="#1e1b4b")
        
        # Subtexto: Escanea este código con tu móvil
        texto_sub = "Escanea este código con tu móvil"
        bbox_sub = draw.textbbox((0, 0), texto_sub, font=font_subtitulo)
        sub_w = bbox_sub[2] - bbox_sub[0]
        x_sub = (canvas_w - sub_w) // 2
        y_sub = y_tit + 50
        draw.text((x_sub, y_sub), texto_sub, font=font_subtitulo, fill="#6b7280")
        
    except Exception as e:
        print(f"Nota: No se pudo cargar la fuente del sistema ({e}). Escribiendo texto estándar.")
        draw.text(((canvas_w - 150)//2, pos_y + qr_h + 30), "¡RESERVA AHORA!", fill="#1e1b4b")
        draw.text(((canvas_w - 200)//2, pos_y + qr_h + 60), "Escanea con tu movil", fill="#6b7280")

    # 6. Guardar la imagen final
    output_path = "menu_qr_enmarcado.png"
    canvas.convert("RGB").save(output_path, "PNG")
    
    path_absoluto = os.path.abspath(output_path)
    print(f"\n¡Marco añadido con éxito!")
    print(f"Guardado en: {path_absoluto}")
    print("====================================================")

if __name__ == "__main__":
    crear_qr_enmarcado()
