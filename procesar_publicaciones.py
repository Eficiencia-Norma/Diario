import os
import re
import shutil
import subprocess
from datetime import date

def main():
    print("Iniciando procesamiento editorial blindado...")

    borradores_dir = "_borradores"
    posts_dir = "_posts"
    img_base_dir = "assets/img"
    docs_base_dir = "assets/docs"

    os.makedirs(posts_dir, exist_ok=True)
    os.makedirs(img_base_dir, exist_ok=True)
    os.makedirs(docs_base_dir, exist_ok=True)

    today_str = date.today().strftime("%Y-%m-%d")

    if not os.path.exists(borradores_dir):
        print("No existe carpeta _borradores. Finalizando.")
        return

    archivos = [
        f for f in os.listdir(borradores_dir)
        if os.path.isfile(os.path.join(borradores_dir, f))
        and not f.startswith('.')
        and not f.endswith(('.txt', '.gitkeep', 'LEEME'))
    ]

    if not archivos:
        print("No hay borradores pendientes para procesar.")
        return

    for filename in archivos:
        print(f"Procesando: {filename}")
        filepath = os.path.join(borradores_dir, filename)
        base_name, ext = os.path.splitext(filename)
        ext = ext.lower().replace('.', '')

        clean_slug = re.sub(r'[^a-zA-Z0-9]+', '-', base_name.lower()).strip('-')
        if not clean_slug:
            clean_slug = "articulo-editorial"
        clean_title = base_name.replace('-', ' ').replace('_', ' ').strip().title()

        post_filename = f"{today_str}-{clean_slug}.md"
        post_path = os.path.join(posts_dir, post_filename)
        article_img_dir = os.path.join(img_base_dir, clean_slug)
        os.makedirs(article_img_dir, exist_ok=True)

        raw_markdown = ""

        # CASO 1: DOCX
        if ext == "docx":
            media_temp = os.path.join("/tmp", f"media_{clean_slug}")
            os.makedirs(media_temp, exist_ok=True)
            cmd = [
                "pandoc", filepath,
                "-f", "docx",
                "-t", "gfm-raw_html",
                f"--extract-media={media_temp}",
                "--wrap=none"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            raw_markdown = res.stdout

            extracted_folder = os.path.join(media_temp, "media")
            if os.path.exists(extracted_folder):
                for img_file in os.listdir(extracted_folder):
                    shutil.copy2(
                        os.path.join(extracted_folder, img_file),
                        os.path.join(article_img_dir, img_file)
                    )

            # Reemplazar ruta de imagenes de forma segura sin romper Liquid
            prefix_tag = "{{ site.baseurl }}"
            replacement = rf'![\1]({prefix_tag}/assets/img/{clean_slug}/\2)'
            raw_markdown = re.sub(r'!\\[(.*?)\\]\\([^)]*media/([^)]+)\\)', replacement, raw_markdown)

        # CASO 2: PDF
        elif ext == "pdf":
            pdf_target = os.path.join(docs_base_dir, f"{today_str}-{clean_slug}.pdf")
            shutil.copy2(filepath, pdf_target)

            subprocess.run(["pdfimages", "-png", filepath, os.path.join(article_img_dir, "img")], capture_output=True)
            txt_res = subprocess.run(["pdftotext", "-layout", filepath, "-"], capture_output=True, text=True)
            raw_lines = [l.strip() for l in txt_res.stdout.splitlines() if not re.match(r'^(Página\s+\d+|\d+)$', l.strip())]
            raw_markdown = "\n\n".join([p for p in "\n".join(raw_lines).split("\n\n") if p.strip()])

            prefix_tag = "{{ site.baseurl }}"
            raw_markdown += f"\n\n---\n\n<div class=\"download-box\">Documento Oficial: <a href=\"{prefix_tag}/assets/docs/{today_str}-{clean_slug}.pdf\" target=\"_blank\">Descargar archivo original en PDF</a></div>\n"

        # CASO 3: ARCHIVO DE TEXTO O MARKDOWN DIRECTO
        else:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                raw_markdown = f.read()

        # Higiene de caracteres invisibles y etiquetas sueltas
        raw_markdown = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', raw_markdown)
        raw_markdown = re.sub(r'<\/?(span|font|o:p)[^>]*>', '', raw_markdown)

        # Calculo de tiempo de lectura
        palabras = re.findall(r'\b\w+\b', raw_markdown)
        total_palabras = len(palabras)
        minutos = max(1, round(total_palabras / 200))

        # Maquetacion sobria (The Economist / El Dinamo)
        parrafos = [p.strip() for p in raw_markdown.split("\n\n") if p.strip()]
        cuerpo_final = []
        dropcap_listo = False

        for idx, p in enumerate(parrafos):
            # Standfirst en el primer parrafo largo
            if idx == 0 and len(p.split()) > 15 and not p.startswith(('#', '!', '<')):
                cuerpo_final.append(f'<p class="editorial-standfirst">{p}</p>')
                continue

            # Drop Cap
            if not dropcap_listo and not p.startswith(('#', '!', '<', '>', '|', '-')):
                m = re.match(r'^([^a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]*)([a-zA-ZáéíóúüñÁÉÍÓÚÜÑ])(.*)$', p, re.DOTALL)
                if m:
                    pref, letra, resto = m.groups()
                    p = f'{pref}<span class="drop-cap">{letra}</span>{resto}'
                    dropcap_listo = True

            # Pull Quotes
            if p.startswith('>'):
                cita = re.sub(r'^>\s*', '', p, flags=re.MULTILINE)
                p = f'<figure class="pull-quote"><blockquote>"{cita}"</blockquote><figcaption>— Referencia del Dictamen</figcaption></figure>'

            cuerpo_final.append(p)

        contenido_maquetado = "\n\n".join(cuerpo_final)

        # Front Matter
        front_matter = f"""---
layout: post
title: "{clean_title}"
author: "Redacción Eficiencia & Norma"
date: {today_str}
category: "Mercados & Regulación"
reading_time: "{minutos} min de lectura"
---

"""
        with open(post_path, "w", encoding="utf-8") as f:
            f.write(front_matter + contenido_maquetado + "\n")

        os.remove(filepath)
        print(f"Completado exitosamente: {post_filename}")

if __name__ == "__main__":
    main()
