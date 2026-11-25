import os
import re
import shutil
import subprocess
from datetime import date
from PIL import Image, ImageDraw, ImageFont

EXT_DOCS = {'.docx', '.odt', '.rtf', '.doc', '.md', '.markdown', '.txt'}
EXT_PDF = {'.pdf'}
EXT_VIDEOS = {'.mp4', '.webm', '.mov', '.mkv'}
EXT_AUDIOS = {'.mp3', '.wav', '.m4a', '.aac', '.ogg'}
EXT_IMAGENES = {'.png', '.jpg', '.jpeg', '.webp', '.svg'}

def clasificar_disciplina(texto):
    t = texto.lower()
    if any(k in t for k in ['tdlc', 'tribunal de defensa', 'sentencia tdlc', 'requerimiento fne']):
        return "Jurisprudencia TDLC"
    elif any(k in t for k in ['colusión', 'colusion', 'cártel', 'cartel', 'fne', 'libre competencia', 'concentración', 'hhi']):
        return "Libre Competencia"
    elif any(k in t for k in ['cmf', 'superintendencia', 'mercado financiero', 'tarifas', 'banca', 'servicios básicos']):
        return "Mercados Regulados"
    elif any(k in t for k in ['medio ambiente', 'sea', 'constitucional', 'política pública', 'proyecto de ley']):
        return "Políticas Públicas"
    return "Análisis Económico & Mercados"

def identificar_firma(texto):
    patron = re.search(r'(?:por|autor|escrito por|análisis de|redacción de)[:\s]+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})', texto, re.IGNORECASE)
    if patron:
        return patron.group(1).strip()
    return "Redacción Eficiencia & Norma"

def generar_extracto(texto):
    parrafos = [p.strip() for p in texto.split("\n\n") if p.strip() and not p.startswith(('#', '!', '<', '>'))]
    for p in parrafos:
        limpio = re.sub(r'[*_`\\|]', '', p).strip()
        palabras = limpio.split()
        if len(palabras) >= 12:
            return " ".join(palabras[:26]) + "..."
    return "Análisis técnico de los fundamentos económicos, jurisprudencia aplicable y marco regulatorio."

def disenar_portada_editorial(titulo, categoria, autor, ruta_salida):
    """
    Motor Director de Arte (Estilo The Economist / Financial Times):
    Crea una portada 16:9 (1200x675 px) con tipografía serif imponente,
    marcos burdeo institucional y acabados sobrios de alta prensa.
    """
    W, H = 1200, 675
    # Fondo grafito oscuro editorial
    img = Image.new('RGB', (W, H), color='#12151a')
    draw = ImageDraw.Draw(img)

    # 1. Franja superior e inferior en Burdeo Institucional (#8b1517)
    draw.rectangle([(0, 0), (W, 16)], fill='#8b1517')
    draw.rectangle([(0, H - 14), (W, H)], fill='#8b1517')

    # 2. Marco sutil interior
    draw.rectangle([(36, 40), (W - 36, H - 38)], outline='#262c36', width=2)

    # 3. Intentar cargar fuentes tipográficas del sistema (Linux / Ubuntu Runner)
    def cargar_fuente(rutas, tam):
        for r in rutas:
            if os.path.exists(r):
                try:
                    return ImageFont.truetype(r, tam)
                except Exception:
                    pass
        return ImageFont.load_default()

    font_sello = cargar_fuente([
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    ], 15)

    font_cat = cargar_fuente([
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    ], 18)

    font_tit = cargar_fuente([
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
    ], 46)

    font_meta = cargar_fuente([
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    ], 17)

    # 4. Cabecera de la Portada: Sello Editorial
    draw.text((64, 60), "EFICIENCIA & NORMA", font=font_sello, fill='#8b1517')
    draw.text((260, 60), "·   ANÁLISIS ECONÓMICO Y DERECHO REGULATORIO", font=font_sello, fill='#8a95a5')

    # Línea divisoria
    draw.line([(64, 94), (W - 64, 94)], fill='#2a323d', width=1)

    # 5. Categoría (Pill formal)
    cat_texto = f"  {categoria.upper()}  "
    draw.rectangle([(64, 126), (64 + len(cat_texto)*12, 160)], fill='#1a2332')
    draw.rectangle([(64, 126), (68, 160)], fill='#8b1517') # Acento burdeo
    draw.text((76, 133), cat_texto.strip(), font=font_cat, fill='#ffffff')

    # 6. Titular con corte de líneas inteligente
    palabras = titulo.split()
    lineas = []
    linea_actual = []

    for p in palabras:
        linea_actual.append(p)
        texto_linea = " ".join(linea_actual)
        # Aproximación de ancho para máximo 38 caracteres por línea
        if len(texto_linea) > 36:
            lineas.append(" ".join(linea_actual[:-1]))
            linea_actual = [p]
    if linea_actual:
        lineas.append(" ".join(linea_actual))

    # Limitar a máximo 4 líneas para que no choque con el pie
    lineas = lineas[:4]

    y_tit = 210
    for l in lineas:
        draw.text((64, y_tit), l, font=font_tit, fill='#f8fafc')
        y_tit += 62

    # 7. Pleca y Metadatos de Cierre (Autor y Edición)
    draw.line([(64, H - 110), (W - 64, H - 110)], fill='#2a323d', width=1)
    draw.text((64, H - 85), f"POR: {autor.upper()}", font=font_meta, fill='#d53f43')
    draw.text((W - 320, H - 85), "EDICIÓN DIGITAL ESPECIALIZADA", font=font_meta, fill='#64748b')

    # Guardar en assets
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    img.save(ruta_salida, format="JPEG", quality=92)
    print(f"✔ Portada editorial diseñada exitosamente: {ruta_salida}")

def main():
    print("Iniciando Motor Editorial con Director de Arte...")

    borradores_dir = "_borradores"
    posts_dir = "_posts"
    img_base_dir = "assets/img"

    os.makedirs(posts_dir, exist_ok=True)
    os.makedirs(img_base_dir, exist_ok=True)

    today_str = date.today().strftime("%Y-%m-%d")

    if not os.path.exists(borradores_dir):
        return

    todos = [
        f for f in os.listdir(borradores_dir)
        if os.path.isfile(os.path.join(borradores_dir, f))
        and not f.startswith('.')
        and not f.endswith('.gitkeep')
    ]

archivos_texto = [f for f in todos if os.path.splitext(f)[1].lower() in (EXT_DOCS | EXT_PDF)]
    if not archivos_texto:
        print("No hay borradores para procesar.")
        return

    for filename in archivos_texto:
        filepath = os.path.join(borradores_dir, filename)
        base_name, ext = os.path.splitext(filename)
        ext = ext.lower()

        clean_slug = re.sub(r'[^a-zA-Z0-9]+', '-', base_name.lower()).strip('-')
        if not clean_slug:
            clean_slug = "analisis-editorial"
        clean_title = base_name.replace('-', ' ').replace('_', ' ').strip().title()

        post_filename = f"{today_str}-{clean_slug}.md"
        post_path = os.path.join(posts_dir, post_filename)
        article_img_dir = os.path.join(img_base_dir, clean_slug)
        os.makedirs(article_img_dir, exist_ok=True)

        raw_markdown = ""

        # Conversión de Word / LibreOffice
        if ext in {'.docx', '.odt', '.rtf'}:
            media_temp = os.path.join("/tmp", f"media_{clean_slug}")
            os.makedirs(media_temp, exist_ok=True)

            cmd = ["pandoc", filepath, "-f", "docx", "-t", "gfm", f"--extract-media={media_temp}", "--wrap=none"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            raw_markdown = res.stdout

            extracted_folder = os.path.join(media_temp, "media")
            if os.path.exists(extracted_folder):
                for img_file in sorted(os.listdir(extracted_folder)):
                    shutil.copy2(os.path.join(extracted_folder, img_file), os.path.join(article_img_dir, img_file))

            def normalizar_img(m):
                img_name = os.path.basename(m.group(1).replace('\\', '/').strip())
                return f'''
<figure class="editorial-media">
  <img src="/Diario/assets/img/{clean_slug}/{img_name}" alt="Gráfico del análisis" loading="lazy">
  <figcaption>Figura / Gráfico anexo al análisis</figcaption>
</figure>'''

            raw_markdown = re.sub(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', normalizar_img, raw_markdown)
            raw_markdown = re.sub(r'!\\[.*?\\]\\((.*?)\\)', normalizar_img, raw_markdown)

        # Conversión de PDF
        elif ext == '.pdf':
            subprocess.run(["pdfimages", "-png", filepath, os.path.join(article_img_dir, "figura")], capture_output=True)
            txt_res = subprocess.run(["pdftotext", "-layout", filepath, "-"], capture_output=True, text=True)
            raw_lines = [l.strip() for l in txt_res.stdout.splitlines() if not re.match(r'^(Página\s+\d+|\d+)$', l.strip())]
            raw_markdown = "\n\n".join([p for p in "\n".join(raw_lines).split("\n\n") if p.strip()])

        else:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                raw_markdown = f.read()

        raw_markdown = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', raw_markdown)

        categoria = clasificar_disciplina(raw_markdown)
        autor = identificar_firma(raw_markdown)
        resumen = generar_extracto(raw_markdown)
        total_palabras = len(re.findall(r'\b\w+\b', raw_markdown))
        tiempo_lectura = max(1, round(total_palabras / 200))

        # DISEÑAR PORTADA AUTOMÁTICA EN 16:9
        portada_nombre = "portada.jpg"
        portada_ruta_fisica = os.path.join(article_img_dir, portada_nombre)
        portada_url_web = f"/Diario/assets/img/{clean_slug}/{portada_nombre}"

        disenar_portada_editorial(clean_title, categoria, autor, portada_ruta_fisica)

        # Maquetación de párrafos y citas
        parrafos = [p.strip() for p in raw_markdown.split("\n\n") if p.strip()]
        cuerpo_final = []
        dropcap_listo = False

        for idx, p in enumerate(parrafos):
            if idx == 0 and len(p.split()) > 15 and not p.startswith(('#', '!', '<')):
                cuerpo_final.append(f'<p class="editorial-standfirst">{p}</p>')
                continue

            if not dropcap_listo and not p.startswith(('#', '!', '<', '>', '|', '-')):
                m = re.match(r'^([^a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]*)([a-zA-ZáéíóúüñÁÉÍÓÚÜÑ])(.*)$', p, re.DOTALL)
                if m:
                    pref, letra, resto = m.groups()
                    p = f'{pref}<span class="drop-cap">{letra}</span>{resto}'
                    dropcap_listo = True

            if p.startswith('>'):
                cita = re.sub(r'^>\s*', '', p, flags=re.MULTILINE).replace('>', '').strip()
                p = f'<figure class="pull-quote"><blockquote>"{cita}"</blockquote><figcaption>— Criterio Jurisprudencial</figcaption></figure>'

            cuerpo_final.append(p)

        contenido_maquetado = "\n\n".join(cuerpo_final)

        def sanitizar(val):
            return re.sub(r'[\"\n\r\\]', ' ', str(val)).strip()

        front_matter = f"""---
layout: post
title: "{sanitizar(clean_title)}"
author: "{sanitizar(autor)}"
date: {today_str}
category: "{sanitizar(categoria)}"
reading_time: "{tiempo_lectura} min de lectura"
excerpt: "{sanitizar(resumen)}"
image: "{portada_url_web}"
---

"""
        with open(post_path, "w", encoding="utf-8") as f:
            f.write(front_matter + contenido_maquetado + "\n")

        if os.path.exists(filepath):
            os.remove(filepath)

        print(f"✔ Publicación completada con éxito: {post_filename}")

if __name__ == "__main__":
    main()
