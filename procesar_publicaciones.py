import os
import re
import shutil
import subprocess
from datetime import date

def clasificar_disciplina(texto):
    """Asigna la sección editorial según análisis de términos jurídicos y económicos."""
    t = texto.lower()
    if any(k in t for k in ['tdlc', 'tribunal de defensa', 'sentencia tdlc', 'requerimiento fne']):
        return "Jurisprudencia TDLC"
    elif any(k in t for k in ['colusión', 'colusion', 'cártel', 'cartel', 'fne', 'libre competencia', 'concentración']):
        return "Libre Competencia"
    elif any(k in t for k in ['cmf', 'superintendencia', 'mercado financiero', 'tarifas', 'banca', 'servicios básicos']):
        return "Mercados Regulados"
    elif any(k in t for k in ['medio ambiente', 'sea', 'constitucional', 'política pública', 'proyecto de ley']):
        return "Políticas Públicas"
    return "Análisis Económico & Mercados"

def identificar_firma(texto):
    """Detecta la firma del redactor o columnista en el encabezado o pie."""
    patron = re.search(r'(?:por|autor|análisis de|redacción de)[:\s]+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})', texto, re.IGNORECASE)
    if patron:
        return patron.group(1).strip()
    return "Redacción Eficiencia & Norma"

def generar_extracto(texto):
    """Obtiene una síntesis limpia para la tarjeta de portada."""
    parrafos = [p.strip() for p in texto.split("\n\n") if p.strip() and not p.startswith(('#', '!', '<', '>'))]
    if parrafos:
        primer_bloque = re.sub(r'[*_`]', '', parrafos[0])
        palabras = primer_bloque.split()
        if len(palabras) > 30:
            return " ".join(palabras[:30]) + "..."
        return primer_bloque
    return "Análisis técnico de los principales fundamentos normativos, económicos y alcance regulatorio del caso."

def main():
    print("Iniciando Sistema de Publicación Editorial Senior...")

    borradores_dir = "_borradores"
    posts_dir = "_posts"
    img_base_dir = "assets/img"

    os.makedirs(posts_dir, exist_ok=True)
    os.makedirs(img_base_dir, exist_ok=True)

    today_str = date.today().strftime("%Y-%m-%d")

    if not os.path.exists(borradores_dir):
        return

    archivos = [
        f for f in os.listdir(borradores_dir)
        if os.path.isfile(os.path.join(borradores_dir, f))
        and not f.startswith('.')
        and not f.endswith(('.txt', '.gitkeep', 'LEEME'))
    ]

    if not archivos:
        print("Bandeja de entrada vacía. Sin borradores pendientes.")
        return

    for filename in archivos:
        print(f"\n==========================================")
        print(f"PROCESANDO CONTENIDO: {filename}")
        print(f"==========================================")

        filepath = os.path.join(borradores_dir, filename)
        base_name, ext = os.path.splitext(filename)
        ext = ext.lower().replace('.', '')

        clean_slug = re.sub(r'[^a-zA-Z0-9]+', '-', base_name.lower()).strip('-')
        if not clean_slug:
            clean_slug = "analisis-regulatorio"
        clean_title = base_name.replace('-', ' ').replace('_', ' ').strip().title()

        post_filename = f"{today_str}-{clean_slug}.md"
        post_path = os.path.join(posts_dir, post_filename)
        article_img_dir = os.path.join(img_base_dir, clean_slug)
        os.makedirs(article_img_dir, exist_ok=True)

        raw_markdown = ""
        imagenes_extraidas = []

        # 1. EXTRACCIÓN DE CONTENIDO Y MULTIMEDIA
        if ext == "docx":
            media_temp = os.path.join("/tmp", f"media_{clean_slug}")
            os.makedirs(media_temp, exist_ok=True)

            cmd = ["pandoc", filepath, "-f", "docx", "-t", "gfm-raw_html", f"--extract-media={media_temp}", "--wrap=none"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            raw_markdown = res.stdout

            extracted_folder = os.path.join(media_temp, "media")
            if os.path.exists(extracted_folder):
                for img_file in sorted(os.listdir(extracted_folder)):
                    shutil.copy2(os.path.join(extracted_folder, img_file), os.path.join(article_img_dir, img_file))
                    imagenes_extraidas.append(img_file)

            # Reemplazar rutas de imágenes en el texto con formato absoluto para GitHub Pages
            raw_markdown = re.sub(
                r'!\\[(.*?)\\]\\((?:.*?media/)?([^)]+)\\)',
                rf'\n\n<figure class="editorial-media"><img src="/Diario/assets/img/{clean_slug}/\2" alt="\1" loading="lazy"><figcaption>\1</figcaption></figure>\n\n',
                raw_markdown
            )

        elif ext == "pdf":
            subprocess.run(["pdfimages", "-png", filepath, os.path.join(article_img_dir, "figura")], capture_output=True)
            txt_res = subprocess.run(["pdftotext", "-layout", filepath, "-"], capture_output=True, text=True)
            raw_lines = [l.strip() for l in txt_res.stdout.splitlines() if not re.match(r'^(Página\s+\d+|\d+)$', l.strip())]
            raw_markdown = "\n\n".join([p for p in "\n".join(raw_lines).split("\n\n") if p.strip()])

            pdf_imgs = sorted([f for f in os.listdir(article_img_dir) if f.startswith("figura")])
            if pdf_imgs:
                imagenes_extraidas = pdf_imgs
                figuras_html = "\n\n".join([
                    f'<figure class="editorial-media"><img src="/Diario/assets/img/{clean_slug}/{img}" alt="Figura de análisis" loading="lazy"><figcaption>Gráfico incorporado en el expediente / informe</figcaption></figure>'
                    for img in pdf_imgs
                ])
                raw_markdown = figuras_html + "\n\n" + raw_markdown

        else:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                raw_markdown = f.read()

        # 2. HIGIENE Y SANITIZACIÓN DEL TEXTO
        raw_markdown = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', raw_markdown)
        raw_markdown = re.sub(r'<\/?(span|font|o:p)[^>]*>', '', raw_markdown)

        # 3. METADATOS Y CLASIFICACIÓN
        categoria = clasificar_disciplina(raw_markdown)
        autor = identificar_firma(raw_markdown)
        resumen_portada = generar_extracto(raw_markdown)

        total_palabras = len(re.findall(r'\b\w+\b', raw_markdown))
        tiempo_lectura = max(1, round(total_palabras / 200))

        # Asignar imagen destacada para la portada si existe alguna figura
        imagen_destacada = ""
        if imagenes_extraidas:
            imagen_destacada = f"/Diario/assets/img/{clean_slug}/{imagenes_extraidas[0]}"

        # 4. MAQUETACIÓN EDITORIAL SOBRIA (ESTILO THE ECONOMIST)
        parrafos = [p.strip() for p in raw_markdown.split("\n\n") if p.strip()]
        cuerpo_final = []
        dropcap_listo = False

        for idx, p in enumerate(parrafos):
            # Standfirst / Copete en el primer párrafo sustantivo
            if idx == 0 and len(p.split()) > 15 and not p.startswith(('#', '!', '<')):
                cuerpo_final.append(f'<p class="editorial-standfirst">{p}</p>')
                continue

            # Letra Capital Clásica (Drop Cap)
            if not dropcap_listo and not p.startswith(('#', '!', '<', '>', '|', '-')):
                m = re.match(r'^([^a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]*)([a-zA-ZáéíóúüñÁÉÍÓÚÜÑ])(.*)$', p, re.DOTALL)
                if m:
                    pref, letra, resto = m.groups()
                    p = f'{pref}<span class="drop-cap">{letra}</span>{resto}'
                    dropcap_listo = True

            # Pull Quotes (Citas de fallos o dictámenes)
            if p.startswith('>'):
                cita = re.sub(r'^>\s*', '', p, flags=re.MULTILINE)
                p = f'<figure class="pull-quote"><blockquote>"{cita}"</blockquote><figcaption>— Referencia del Pronunciamiento</figcaption></figure>'

            cuerpo_final.append(p)

        contenido_maquetado = "\n\n".join(cuerpo_final)

        # 5. GENERACIÓN DEL FRONT MATTER FINAL
        front_matter = f"""---
layout: post
title: "{clean_title}"
author: "{autor}"
date: {today_str}
category: "{categoria}"
reading_time: "{tiempo_lectura} min de lectura"
excerpt: "{resumen_portada}"
"""
        if imagen_destacada:
            front_matter += f'image: "{imagen_destacada}"\n'

        front_matter += "---\n\n"

        with open(post_path, "w", encoding="utf-8") as f:
            f.write(front_matter + contenido_maquetado + "\n")

        # 6. ELIMINACIÓN DEL ARCHIVO FUENTE (Cero redundancias en servidor)
        os.remove(filepath)
        print(f"✔ Publicación completada con éxito: {post_filename}")
        print(f"  Categoría: {categoria} | Autor: {autor} | Lectura: {tiempo_lectura} min")

if __name__ == "__main__":
    main()
