import os
import re
import shutil
import subprocess
from datetime import date

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
            return " ".join(palabras[:28]) + "..."
    return "Análisis técnico de los principales fundamentos normativos, económicos y alcance regulatorio del caso."

def main():
    print("Iniciando Motor Editorial Eficiencia & Norma...")

    borradores_dir = "_borradores"
    posts_dir = "_posts"
    img_base_dir = "assets/img"
    video_base_dir = "assets/video"
    audio_base_dir = "assets/audio"

    os.makedirs(posts_dir, exist_ok=True)
    os.makedirs(img_base_dir, exist_ok=True)
    os.makedirs(video_base_dir, exist_ok=True)
    os.makedirs(audio_base_dir, exist_ok=True)

    today_str = date.today().strftime("%Y-%m-%d")

    if not os.path.exists(borradores_dir):
        return

    todos_los_archivos = [
        f for f in os.listdir(borradores_dir)
        if os.path.isfile(os.path.join(borradores_dir, f))
        and not f.startswith('.')
        and not f.endswith('.gitkeep')
    ]

    archivos_texto = [f for f in todos_los_archivos if os.path.splitext(f).lower() in (EXT_DOCS | EXT_PDF)]
    archivos_video = [f for f in todos_los_archivos if os.path.splitext(f).lower() in EXT_VIDEOS]
    archivos_audio = [f for f in todos_los_archivos if os.path.splitext(f).lower() in EXT_AUDIOS]
    archivos_imagenes_sueltas = [f for f in todos_los_archivos if os.path.splitext(f).lower() in EXT_IMAGENES]

    if not archivos_texto:
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
        article_video_dir = os.path.join(video_base_dir, clean_slug)
        article_audio_dir = os.path.join(audio_base_dir, clean_slug)

        os.makedirs(article_img_dir, exist_ok=True)
        os.makedirs(article_video_dir, exist_ok=True)
        os.makedirs(article_audio_dir, exist_ok=True)

        multimedia_bloques = []
        imagenes_extraidas = []

        # 1. Videos
        for vid in archivos_video:
            origen = os.path.join(borradores_dir, vid)
            if os.path.exists(origen):
                shutil.move(origen, os.path.join(article_video_dir, vid))
                vid_url = f"/Diario/assets/video/{clean_slug}/{vid}"
                multimedia_bloques.append(f'''
<div class="editorial-video-container">
  <video controls preload="metadata"><source src="{vid_url}"></video>
  <div class="media-caption"><span class="caption-label">Cápsula Audiovisual</span></div>
</div>''')

        # 2. Audios
        for aud in archivos_audio:
            origen = os.path.join(borradores_dir, aud)
            if os.path.exists(origen):
                shutil.move(origen, os.path.join(article_audio_dir, aud))
                aud_url = f"/Diario/assets/audio/{clean_slug}/{aud}"
                multimedia_bloques.append(f'''
<div class="editorial-audio-container">
  <audio controls style="width: 100%;"><source src="{aud_url}"></audio>
</div>''')

        # 3. Imágenes sueltas
        for img in archivos_imagenes_sueltas:
            origen = os.path.join(borradores_dir, img)
            if os.path.exists(origen):
                shutil.move(origen, os.path.join(article_img_dir, img))
                imagenes_extraidas.append(img)
                multimedia_bloques.append(f'''
<figure class="editorial-media">
  <img src="/Diario/assets/img/{clean_slug}/{img}" alt="Registro documental" loading="lazy">
  <figcaption>Registro Documental</figcaption>
</figure>''')

        # 4. Procesamiento de Texto y Conversión
        raw_markdown = ""

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
                    imagenes_extraidas.append(img_file)

            # Reemplazar tanto etiquetas HTML <img src="..."> como Markdown ![alt](url)
            def normalizar_img(m):
                img_name = os.path.basename(m.group(1).replace('\\', '/').strip())
                return f'''
<figure class="editorial-media">
  <img src="/Diario/assets/img/{clean_slug}/{img_name}" alt="Gráfico / Esquema técnico" loading="lazy">
  <figcaption>Figura / Gráfico anexo al análisis</figcaption>
</figure>
'''
            # Capturar <img src="...">
            raw_markdown = re.sub(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', normalizar_img, raw_markdown)
            # Capturar ![alt](url)
            raw_markdown = re.sub(r'!\\[.*?\\]\\((.*?)\\)', normalizar_img, raw_markdown)

        elif ext == '.pdf':
            subprocess.run(["pdfimages", "-png", filepath, os.path.join(article_img_dir, "figura")], capture_output=True)
            txt_res = subprocess.run(["pdftotext", "-layout", filepath, "-"], capture_output=True, text=True)
            raw_lines = [l.strip() for l in txt_res.stdout.splitlines() if not re.match(r'^(Página\s+\d+|\d+)$', l.strip())]
            raw_markdown = "\n\n".join([p for p in "\n".join(raw_lines).split("\n\n") if p.strip()])

            pdf_imgs = sorted([f for f in os.listdir(article_img_dir) if f.startswith("figura")])
            if pdf_imgs:
                imagenes_extraidas.extend(pdf_imgs)
                figuras_html = "\n\n".join([
                    f'<figure class="editorial-media"><img src="/Diario/assets/img/{clean_slug}/{img}" alt="Registro documental" loading="lazy"><figcaption>Evidencia extraída del expediente</figcaption></figure>'
                    for img in pdf_imgs
                ])
                raw_markdown = figuras_html + "\n\n" + raw_markdown

        else:
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    raw_markdown = f.read()

        if multimedia_bloques:
            raw_markdown = "\n\n".join(multimedia_bloques) + "\n\n" + raw_markdown

        # Higiene de caracteres
        raw_markdown = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', raw_markdown)

        categoria = clasificar_disciplina(raw_markdown)
        autor = identificar_firma(raw_markdown)
        resumen = generar_extracto(raw_markdown)
        total_palabras = len(re.findall(r'\b\w+\b', raw_markdown))
        tiempo_lectura = max(1, round(total_palabras / 200))

        imagen_portada = ""
        if imagenes_extraidas:
            imagen_portada = f"/Diario/assets/img/{clean_slug}/{imagenes_extraidas[0]}"

        # Diagramación editorial
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
                p = f'<figure class="pull-quote"><blockquote>"{cita}"</blockquote><figcaption>— Referencia del Pronunciamiento</figcaption></figure>'

            cuerpo_final.append(p)

        contenido_maquetado = "\n\n".join(cuerpo_final)

        # Sanitización de Front Matter YAML
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
"""
        if imagen_portada:
            front_matter += f'image: "{imagen_portada}"\n'
        front_matter += "---\n\n"

        with open(post_path, "w", encoding="utf-8") as f:
            f.write(front_matter + contenido_maquetado + "\n")

        if os.path.exists(filepath):
            os.remove(filepath)

        print(f"✔ Publicación completada con éxito: {post_filename}")

if __name__ == "__main__":
    main()
Guarda los cambios con Commit changes....
Paso 2: Asegurar el Diseño en _layouts/post.html
Abre _layouts/post.html y asegúrate de que dentro de su etiqueta <style> estén presentes las siguientes directivas para formatear de inmediato tablas y figuras:
/* TABLAS DE PRENSA */
.article-content table {
  width: 100%;
  border-collapse: collapse;
  margin: 32px 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 0.9rem;
  border: 1px solid var(--line);
}

.article-content th {
  background-color: var(--burgundy);
  color: #ffffff;
  padding: 10px 14px;
  text-align: left;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.article-content td {
  padding: 10px 14px;
  border-bottom: 1px solid var(--line-subtle);
  color: var(--ink-subtle);
}

.article-content tr:nth-child(even) td {
  background-color: var(--bg-tint);
}

/* FIGURAS E IMÁGENES CENTRADAS */
.article-content figure,
.article-content .editorial-media {
  margin: 36px auto;
  text-align: center;
  max-width: 100%;
}

.article-content img {
  display: block;
  margin: 0 auto;
  max-width: 100%;
  height: auto;
  border: 1px solid var(--line);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
}

.article-content figcaption {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 0.82rem;
  color: var(--ink-muted);
  margin-top: 8px;
  font-style: italic;
}
