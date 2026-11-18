import os
import re
import shutil
import subprocess
from datetime import date

# Extensiones reconocidas por el motor editorial
EXT_DOCS = {'.docx', '.odt', '.rtf', '.doc', '.md', '.markdown', '.txt'}
EXT_PDF = {'.pdf'}
EXT_VIDEOS = {'.mp4', '.webm', '.mov', '.mkv'}
EXT_AUDIOS = {'.mp3', '.wav', '.m4a', '.aac', '.ogg'}
EXT_IMAGENES = {'.png', '.jpg', '.jpeg', '.webp', '.svg'}

def clasificar_disciplina(texto):
    """Asigna la sección editorial según análisis temático profundo."""
    t = texto.lower()
    if any(k in t for k in ['tdlc', 'tribunal de defensa', 'sentencia tdlc', 'requerimiento fne']):
        return "Jurisprudencia TDLC"
    elif any(k in t for k in ['colusión', 'colusion', 'cártel', 'cartel', 'fne', 'libre competencia', 'concentración', 'hhi']):
        return "Libre Competencia"
    elif any(k in t for k in ['cmf', 'superintendencia', 'mercado financiero', 'tarifas', 'banca', 'servicios básicos', 'monopolio natural']):
        return "Mercados Regulados"
    elif any(k in t for k in ['medio ambiente', 'sea', 'constitucional', 'política pública', 'proyecto de ley', 'legislativo']):
        return "Políticas Públicas"
    return "Análisis Económico & Mercados"

def identificar_firma(texto):
    """Detecta la firma del autor o asigna la redacción institucional."""
    patron = re.search(r'(?:por|autor|escrito por|análisis de|redacción de)[:\s]+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})', texto, re.IGNORECASE)
    if patron:
        return patron.group(1).strip()
    return "Redacción Eficiencia & Norma"

def generar_extracto(texto):
    """Genera un copete formal para la portada principal."""
    parrafos = [p.strip() for p in texto.split("\n\n") if p.strip() and not p.startswith(('#', '!', '<', '>'))]
    if parrafos:
        primer_bloque = re.sub(r'[*_`]', '', parrafos[0])
        palabras = primer_bloque.split()
        if len(palabras) > 30:
            return " ".join(palabras[:30]) + "..."
        return primer_bloque
    return "Análisis técnico de los principales antecedentes regulatorios, fundamentos económicos y alcance jurídico del caso analizado."

def main():
    print("Iniciando Motor Editorial Universal (Eficiencia & Norma)...")

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
        print("Carpeta _borradores/ no existe.")
        return

    todos_los_archivos = [
        f for f in os.listdir(borradores_dir)
        if os.path.isfile(os.path.join(borradores_dir, f))
        and not f.startswith('.')
        and not f.endswith(('.gitkeep', 'LEEME'))
    ]

    if not todos_los_archivos:
        print("Bandeja de borradores vacía.")
        return

    # Separar por categorías de archivos
    archivos_texto = [f for f in todos_los_archivos if os.path.splitext(f)[1].lower() in (EXT_DOCS | EXT_PDF)]
    archivos_video = [f for f in todos_los_archivos if os.path.splitext(f)[1].lower() in EXT_VIDEOS]
    archivos_audio = [f for f in todos_los_archivos if os.path.splitext(f)[1].lower() in EXT_AUDIOS]
    archivos_imagenes_sueltas = [f for f in todos_los_archivos if os.path.splitext(f)[1].lower() in EXT_IMAGENES]

    # Si solo subieron multimedia sin texto, generamos una nota de cobertura audiovisual automática
    if not archivos_texto and (archivos_video or archivos_audio or archivos_imagenes_sueltas):
        base_name = os.path.splitext(todos_los_archivos[0])[0]
        archivos_texto = [f"{base_name}.txt"]
        with open(os.path.join(borradores_dir, archivos_texto[0]), "w", encoding="utf-8") as f:
            f.write(f"Registro y Cobertura Audiovisual: {base_name.replace('-', ' ').title()}.\n\nDocumentación anexa para análisis de la causa.")

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

        # 1. PROCESAR VIDEOS (.mp4, .webm, .mov)
        for vid in archivos_video:
            origen = os.path.join(borradores_dir, vid)
            if os.path.exists(origen):
                shutil.move(origen, os.path.join(article_video_dir, vid))
                vid_url = f"/Diario/assets/video/{clean_slug}/{vid}"
                multimedia_bloques.append(f'''
<div class="editorial-video-container">
  <video controls preload="metadata">
    <source src="{vid_url}">
    Tu navegador no soporta reproducción de video.
  </video>
  <div class="media-caption">
    <span class="caption-label">Cápsula / Entrevista Audiovisual</span>
    <span class="caption-credit">Registro de Sesión</span>
  </div>
</div>
''')

        # 2. PROCESAR AUDIOS / PODCASTS (.mp3, .wav, .m4a)
        for aud in archivos_audio:
            origen = os.path.join(borradores_dir, aud)
            if os.path.exists(origen):
                shutil.move(origen, os.path.join(article_audio_dir, aud))
                aud_url = f"/Diario/assets/audio/{clean_slug}/{aud}"
                multimedia_bloques.append(f'''
<div class="editorial-video-container" style="background: var(--bg-tint); padding: 18px; border: 1px solid var(--line);">
  <div style="font-weight: 800; font-size: 0.85rem; color: var(--burgundy); margin-bottom: 8px; text-transform: uppercase;">
    Entrevista / Declaración en Audio
  </div>
  <audio controls style="width: 100%;">
    <source src="{aud_url}">
    Tu navegador no soporta reproducción de audio.
  </audio>
</div>
''')

        # 3. MOVER IMÁGENES SUELTAS SUBIDAS A LA CARPETA
        for img in archivos_imagenes_sueltas:
            origen = os.path.join(borradores_dir, img)
            if os.path.exists(origen):
                shutil.move(origen, os.path.join(article_img_dir, img))
                imagenes_extraidas.append(img)
                multimedia_bloques.append(f'''
<figure class="editorial-media">
  <img src="/Diario/assets/img/{clean_slug}/{img}" alt="Fotografía documental" loading="lazy">
  <figcaption><strong>Registro Documental:</strong> Evidencia fotográfica incorporada</figcaption>
</figure>
''')

        # 4. EXTRACCIÓN DEL CONTENIDO ESCRITO
        raw_markdown = ""

        # CASO A: Documentos de procesador (Word .docx, LibreOffice .odt, .rtf)
        if ext in {'.docx', '.odt', '.rtf'}:
            media_temp = os.path.join("/tmp", f"media_{clean_slug}")
            os.makedirs(media_temp, exist_ok=True)

            cmd = ["pandoc", filepath, "-t", "gfm-raw_html", f"--extract-media={media_temp}", "--wrap=none"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            raw_markdown = res.stdout

            extracted_folder = os.path.join(media_temp, "media")
            if os.path.exists(extracted_folder):
                for img_file in sorted(os.listdir(extracted_folder)):
                    shutil.copy2(os.path.join(extracted_folder, img_file), os.path.join(article_img_dir, img_file))
                    imagenes_extraidas.append(img_file)

            def reemplazar_figura(m):
                alt_text = m.group(1).strip()
                img_name = m.group(2).strip()
                caption = alt_text if alt_text else "Gráfico / Esquema incorporado en el análisis"
                return f'''
<figure class="editorial-media">
  <img src="/Diario/assets/img/{clean_slug}/{img_name}" alt="{caption}" loading="lazy">
  <figcaption><strong>Figura / Registro:</strong> {caption}</figcaption>
</figure>
'''
            raw_markdown = re.sub(r'!\\[(.*?)\\]\\((?:.*?media/)?([^)]+)\\)', reemplazar_figura, raw_markdown)

        # CASO B: Documentos PDF (.pdf)
        elif ext == '.pdf':
            subprocess.run(["pdfimages", "-png", filepath, os.path.join(article_img_dir, "figura")], capture_output=True)
            txt_res = subprocess.run(["pdftotext", "-layout", filepath, "-"], capture_output=True, text=True)
            raw_lines = [l.strip() for l in txt_res.stdout.splitlines() if not re.match(r'^(Página\s+\d+|\d+)$', l.strip())]
            raw_markdown = "\n\n".join([p for p in "\n".join(raw_lines).split("\n\n") if p.strip()])

            pdf_imgs = sorted([f for f in os.listdir(article_img_dir) if f.startswith("figura")])
            if pdf_imgs:
                imagenes_extraidas.extend(pdf_imgs)
                figuras_html = "\n\n".join([
                    f'<figure class="editorial-media"><img src="/Diario/assets/img/{clean_slug}/{img}" alt="Figura de expediente" loading="lazy"><figcaption><strong>Anexo:</strong> Gráfico extraído del expediente oficial</figcaption></figure>'
                    for img in pdf_imgs
                ])
                raw_markdown = figuras_html + "\n\n" + raw_markdown

        # CASO C: Texto plano o Markdown (.md, .txt)
        else:
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    raw_markdown = f.read()

        # Insertar elementos audiovisuales en el cuerpo
        if multimedia_bloques:
            raw_markdown = "\n\n".join(multimedia_bloques) + "\n\n" + raw_markdown

        # Conversión de videos de YouTube en reproductores integrados
        raw_markdown = re.sub(
            r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'<div class="editorial-video-container"><iframe src="[suspicious link removed]" allowfullscreen></iframe><div class="media-caption"><span class="caption-label">Cápsula Informativa</span><span class="caption-credit">Cobertura Audiovisual</span></div></div>',
            raw_markdown
        )

        # Higiene editorial profunda
        raw_markdown = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', raw_markdown)
        raw_markdown = re.sub(r'<\/?(span|font|o:p)[^>]*>', '', raw_markdown)

        # Metadatos automáticos
        categoria = clasificar_disciplina(raw_markdown)
        autor = identificar_firma(raw_markdown)
        resumen = generar_extracto(raw_markdown)
        total_palabras = len(re.findall(r'\b\w+\b', raw_markdown))
        tiempo_lectura = max(1, round(total_palabras / 200))

        # Imagen de portada si existe alguna figura
        imagen_portada = ""
        if imagenes_extraidas:
            imagen_portada = f"/Diario/assets/img/{clean_slug}/{imagenes_extraidas[0]}"

        # Maquetación sobria (The Economist / El Dínamo)
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
                cita = re.sub(r'^>\s*', '', p, flags=re.MULTILINE)
                p = f'<figure class="pull-quote"><blockquote>"{cita}"</blockquote><figcaption>— Referencia del Pronunciamiento</figcaption></figure>'

            cuerpo_final.append(p)

        contenido_maquetado = "\n\n".join(cuerpo_final)

        # Generar Front Matter limpio
        front_matter = f"""---
layout: post
title: "{clean_title}"
author: "{autor}"
date: {today_str}
category: "{categoria}"
reading_time: "{tiempo_lectura} min de lectura"
excerpt: "{resumen}"
"""
        if imagen_portada:
            front_matter += f'image: "{imagen_portada}"\n'
        front_matter += "---\n\n"

        with open(post_path, "w", encoding="utf-8") as f:
            f.write(front_matter + contenido_maquetado + "\n")

        # Eliminar archivo original de la bandeja
        if os.path.exists(filepath):
            os.remove(filepath)
            
        print(f"✔ Publicación completada con éxito: {post_filename} ({ext.upper()})")

if __name__ == "__main__":
    main()
