import type { Tutorial } from '../types';

function blobToDataUrl(blob: Blob): Promise<string> {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve((reader.result as string) || '');
    reader.onerror = () => resolve('');
    reader.readAsDataURL(blob);
  });
}

export async function generateStandaloneHtml(tutorial: Tutorial): Promise<string> {
  // Convert any Blob video to base64 safely so it can be stored inside the standalone HTML file
  const stepsWithBase64 = await Promise.all(
    tutorial.steps.map(async (st) => {
      let videoStr: string | undefined = undefined;
      if (typeof st.video === 'string') {
        if (st.video.startsWith('blob:')) {
          try {
            const resp = await fetch(st.video);
            const blob = await resp.blob();
            videoStr = await blobToDataUrl(blob);
          } catch (e) {
            console.warn('No se pudo convertir blob URL a base64:', e);
            videoStr = st.video;
          }
        } else {
          videoStr = st.video;
        }
      } else if (st.video && typeof st.video === 'object') {
        try {
          videoStr = await blobToDataUrl(st.video as Blob);
        } catch (err) {
          console.warn('Error al serializar blob de video:', err);
        }
      }
      return {
        ...st,
        video: videoStr,
      };
    })
  );

  const tutToExport = { ...tutorial, steps: stepsWithBase64 };
  const tutorialJson = JSON.stringify(tutToExport).replace(/<\/script>/g, '<\\/script>');

  return `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${escapeHtml(tutorial.title)} - Playbook Interactivo</title>
  <style>
    :root {
      --primary: #2563eb;
      --primary-hover: #1d4ed8;
      --bg: #0f172a;
      --surface: #1e293b;
      --surface-border: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.6;
    }
    header {
      background: rgba(15, 23, 42, 0.95);
      backdrop-filter: blur(8px);
      border-bottom: 1px solid var(--surface-border);
      position: sticky;
      top: 0;
      z-index: 50;
      padding: 0.85rem 1.5rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .badge {
      display: inline-block;
      padding: 0.2rem 0.6rem;
      border-radius: 0.375rem;
      font-size: 0.75rem;
      font-weight: 700;
      background: rgba(37, 99, 235, 0.2);
      color: #60a5fa;
      border: 1px solid rgba(59, 130, 246, 0.3);
      text-transform: uppercase;
    }
    .btn {
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.45rem 0.9rem;
      border-radius: 0.5rem;
      font-weight: 600;
      font-size: 0.85rem;
      border: none;
      transition: all 0.2s;
    }
    .btn-primary { background: var(--primary); color: white; }
    .btn-primary:hover { background: var(--primary-hover); }
    .btn-secondary { background: var(--surface); color: var(--text); border: 1px solid var(--surface-border); }
    .btn-secondary:hover { background: #334155; }

    .tabs { display: flex; gap: 0.4rem; background: #0b1120; padding: 0.25rem; border-radius: 0.5rem; border: 1px solid var(--surface-border); }
    .tab-btn {
      padding: 0.35rem 0.75rem;
      border-radius: 0.375rem;
      font-size: 0.8rem;
      font-weight: 600;
      border: none;
      background: transparent;
      color: var(--text-muted);
      cursor: pointer;
    }
    .tab-btn.active { background: var(--primary); color: white; }

    /* Layout Guidde style */
    .layout-wrapper { display: flex; min-height: calc(100vh - 3.5rem); }
    aside {
      width: 280px;
      flex-shrink: 0;
      border-right: 1px solid var(--surface-border);
      background: rgba(11, 17, 32, 0.6);
      padding: 1.5rem 1rem;
      position: sticky;
      top: 3.5rem;
      height: calc(100vh - 3.5rem);
      overflow-y: auto;
    }
    .toc-title { font-size: 0.75rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 0.75rem; padding-left: 0.5rem; }
    .toc-item {
      display: flex;
      align-items: baseline;
      gap: 0.5rem;
      width: 100%;
      text-align: left;
      padding: 0.5rem 0.6rem;
      border-radius: 0.5rem;
      font-size: 0.8rem;
      color: var(--text-muted);
      background: transparent;
      border: none;
      cursor: pointer;
      transition: all 0.15s;
    }
    .toc-item:hover { color: var(--text); background: var(--surface); }
    .toc-item.active { color: white; background: var(--surface); font-weight: 600; border-left: 3px solid var(--primary); }
    .toc-num { font-family: monospace; font-size: 0.75rem; opacity: 0.7; }

    main { flex: 1; padding: 2rem 3rem; max-width: 950px; }

    .chapter-card { margin-bottom: 3.5rem; scroll-margin-top: 5rem; }
    .chapter-heading { display: flex; align-items: baseline; gap: 0.75rem; margin-bottom: 0.75rem; }
    .chapter-num { font-size: 1.25rem; font-family: monospace; font-weight: 700; color: #60a5fa; }
    .chapter-title { font-size: 1.25rem; font-weight: 700; color: #f8fafc; }
    .chapter-desc { font-size: 0.95rem; color: #cbd5e1; margin-bottom: 1.25rem; white-space: pre-line; }

    .media-box {
      border-radius: 0.75rem;
      overflow: hidden;
      background: #000;
      border: 1px solid var(--surface-border);
      box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5);
      position: relative;
    }
    .media-box video { width: 100%; display: block; max-height: 520px; }
    .media-box img { width: 100%; display: block; max-height: 520px; object-fit: contain; }

    .click-marker {
      position: absolute;
      width: 26px; height: 26px;
      border-radius: 50%;
      background: rgba(239, 68, 68, 0.85);
      border: 3px solid white;
      box-shadow: 0 0 15px rgba(239, 68, 68, 0.9);
      transform: translate(-50%, -50%);
      pointer-events: none;
      animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
      0% { transform: translate(-50%, -50%) scale(0.9); }
      70% { transform: translate(-50%, -50%) scale(1.15); box-shadow: 0 0 0 12px rgba(239, 68, 68, 0); }
      100% { transform: translate(-50%, -50%) scale(0.9); }
    }

    .note-box {
      padding: 0.75rem 1rem;
      border-radius: 0.5rem;
      font-size: 0.85rem;
      margin-bottom: 1rem;
    }
    .note-info { background: rgba(59, 130, 246, 0.15); border-left: 4px solid #3b82f6; color: #93c5fd; }
    .note-tip { background: rgba(16, 185, 129, 0.15); border-left: 4px solid #10b981; color: #a7f3d0; }
    .note-warning { background: rgba(245, 158, 11, 0.15); border-left: 4px solid #f59e0b; color: #fde68a; }

    /* Video Player View */
    #full-video-view { display: none; padding: 2rem; max-width: 1000px; margin: 0 auto; width: 100%; }
    .video-timeline-segments { display: flex; gap: 4px; height: 8px; margin-top: 1rem; margin-bottom: 1rem; }
    .segment-bar { flex: 1; border-radius: 4px; background: var(--surface-border); cursor: pointer; transition: all 0.2s; }
    .segment-bar.active { background: var(--primary); }

    .print-only-media,
    .media-box img.print-only-media,
    .media-box div.print-only-media {
      display: none !important;
    }

    @media (max-width: 768px) {
      aside { display: none; }
      main { padding: 1.5rem; }
    }

    @media print {
      * {
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
      }
      body {
        background: white !important;
        color: #1e293b !important;
      }
      header, aside, .tabs, .btn, .screen-only-video, button {
        display: none !important;
      }
      .layout-wrapper {
        display: block !important;
      }
      main {
        max-width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
      }
      .chapter-card {
        page-break-inside: avoid !important;
        break-inside: avoid !important;
        margin-bottom: 2.5rem !important;
      }
      .chapter-title {
        color: #0f172a !important;
      }
      .chapter-num {
        color: #2563eb !important;
      }
      .chapter-desc {
        color: #334155 !important;
      }
      .media-box {
        border: 1px solid #cbd5e1 !important;
        box-shadow: none !important;
        background: #f8fafc !important;
      }
      .print-only-media,
      .media-box img.print-only-media {
        display: block !important;
        width: 100% !important;
        height: auto !important;
        max-height: 500px !important;
        object-fit: contain !important;
      }
      .media-box div.click-marker.print-only-media {
        display: block !important;
        position: absolute !important;
      }
      .click-marker {
        animation: none !important;
      }
    }
  </style>
</head>
<body>
  <header>
    <div style="display: flex; align-items: center; gap: 0.75rem;">
      <span class="badge">${escapeHtml(tutorial.appName || 'Tobo4')}</span>
      <h1 style="font-size: 1.15rem; font-weight: 700;">${escapeHtml(tutorial.title)}</h1>
    </div>

    <div style="display: flex; align-items: center; gap: 1rem;">
      <div class="tabs">
        <button id="tab-playbook" class="tab-btn active" onclick="switchMode('playbook')">📄 Vista Playbook</button>
        <button id="tab-video" class="tab-btn" onclick="switchMode('video')">▶ Video Tutorial</button>
      </div>
      <button class="btn btn-secondary" onclick="window.print()">🖨️ Imprimir / PDF</button>
    </div>
  </header>

  <div class="layout-wrapper">
    <!-- Left Table of contents -->
    <aside>
      <div class="toc-title">Tabla de Contenido</div>
      <button class="toc-item" onclick="switchMode('video')" style="color: #60a5fa; font-weight: 600; margin-bottom: 0.5rem;">
        ▶ Video Tutorial
      </button>
      ${tutToExport.steps.map((st, i) => {
        const numStr = i + 1 < 10 ? `0${i + 1}` : `${i + 1}`;
        return `
          <button class="toc-item" onclick="handleTocClick('${st.id}', ${i})">
            <span class="toc-num">${numStr}</span>
            <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(st.title || `Capítulo ${i + 1}`)}</span>
          </button>
        `;
      }).join('')}
    </aside>

    <!-- Main Playbook Document -->
    <main id="playbook-view">
      <div style="border-bottom: 1px solid var(--surface-border); padding-bottom: 1.5rem; margin-bottom: 2.5rem;">
        <h1 style="font-size: 2rem; font-weight: 800; margin-bottom: 0.5rem;">${escapeHtml(tutorial.title)}</h1>
        <p style="color: var(--text-muted); font-size: 0.95rem;">${escapeHtml(tutorial.description)}</p>
      </div>

      ${tutToExport.steps.map((st, i) => {
        const numStr = i + 1 < 10 ? `0${i + 1}` : `${i + 1}`;
        return `
          <section class="chapter-card" id="ch-${st.id}">
            <div class="chapter-heading">
              <span class="chapter-num">${numStr}</span>
              <h2 class="chapter-title">${escapeHtml(st.title || `Capítulo ${i + 1}`)}</h2>
            </div>

            ${st.description ? `<p class="chapter-desc">${escapeHtml(st.description)}</p>` : ''}
            ${renderNote(st)}

            ${st.video ? `
              <div class="media-box">
                <video id="step-video-${i}" class="screen-only-video" controls playsinline preload="auto" poster="${st.image || ''}" onplay="ensureStepVideo(${i})" onpointerdown="ensureStepVideo(${i})"></video>
                ${st.image ? `
                  <img src="${st.image}" class="print-only-media" alt="${escapeHtml(st.title)}" />
                  ${st.clickX !== undefined && st.clickY !== undefined ? `
                    <div class="click-marker print-only-media" style="left: ${st.clickX}%; top: ${st.clickY}%;"></div>
                  ` : ''}
                ` : ''}
              </div>
            ` : st.image ? `
              <div class="media-box">
                <img src="${st.image}" alt="${escapeHtml(st.title)}" />
                ${st.clickX !== undefined && st.clickY !== undefined ? `
                  <div class="click-marker" style="left: ${st.clickX}%; top: ${st.clickY}%;"></div>
                ` : ''}
              </div>
            ` : ''}

            <div style="margin-top: 0.75rem;">
              <button onclick="jumpToVideoChapter(${i})" style="background: none; border: none; color: #60a5fa; cursor: pointer; font-size: 0.8rem; font-weight: 600;">
                Ir a este paso en el video ➡
              </button>
            </div>
          </section>
        `;
      }).join('')}
    </main>

    <!-- Full Video Player Container -->
    <div id="full-video-view">
      <div style="margin-bottom: 1rem;">
        <span class="badge" id="video-chapter-badge">Capítulo 01</span>
        <h2 id="video-chapter-title" style="font-size: 1.5rem; font-weight: 700; margin-top: 0.25rem;"></h2>
      </div>

      <div class="media-box" style="aspect-ratio: 16/9; display: flex; align-items: center; justify-content: center; background: #000;">
        <video id="main-player" controls autoplay playsinline style="width: 100%; height: 100%; object-fit: contain;"></video>
      </div>

      <div class="video-timeline-segments" id="video-segments"></div>

      <div style="display: flex; justify-content: space-between; align-items: center;">
        <button class="btn btn-secondary" onclick="prevChapter()">⬅ Anterior</button>
        <span id="video-counter" style="color: var(--text-muted); font-size: 0.85rem;"></span>
        <button class="btn btn-primary" onclick="nextChapter()">Siguiente ➡</button>
      </div>
      <p id="video-chapter-desc" style="color: #cbd5e1; margin-top: 1rem; font-size: 0.95rem; white-space: pre-line;"></p>
    </div>
  </div>

  <script>
    const data = ${tutorialJson};
    let currentChapterIdx = 0;
    const blobUrls = {};

    function base64ToBlob(dataUri) {
      if (!dataUri) return null;
      // Extract clean mime type and clean base64 data regardless of codecs in dataUri
      const b64Idx = dataUri.indexOf(';base64,');
      let b64 = '';
      let mime = 'video/webm';
      if (b64Idx !== -1) {
        b64 = dataUri.substring(b64Idx + 8);
        const mimeMatch = dataUri.substring(0, b64Idx).match(/^data:([^;]+)/);
        if (mimeMatch) mime = mimeMatch[1];
      } else {
        const commaIdx = dataUri.lastIndexOf(',');
        b64 = commaIdx !== -1 ? dataUri.substring(commaIdx + 1) : dataUri;
      }

      const bstr = atob(b64);
      const len = bstr.length;
      const u8arr = new Uint8Array(len);
      for (let i = 0; i < len; i++) {
        u8arr[i] = bstr.charCodeAt(i);
      }
      return new Blob([u8arr], { type: mime });
    }

    function getStreamableUrl(index, dataUrl) {
      if (!dataUrl) return '';
      if (blobUrls[index]) return blobUrls[index];
      try {
        const blob = base64ToBlob(dataUrl);
        if (!blob) return dataUrl;
        const url = URL.createObjectURL(blob);
        blobUrls[index] = url;
        return url;
      } catch (e) {
        console.error('Error al decodificar video blob:', e);
        return dataUrl;
      }
    }

    function ensureStepVideo(idx) {
      const vidEl = document.getElementById('step-video-' + idx);
      if (vidEl && !vidEl.src && data.steps[idx] && data.steps[idx].video) {
        const streamUrl = getStreamableUrl(idx, data.steps[idx].video);
        vidEl.src = streamUrl;
        vidEl.load();
      }
    }

    // Preload all step videos smoothly
    function initAllVideos() {
      for (let i = 0; i < data.steps.length; i++) {
        ensureStepVideo(i);
      }
    }
    initAllVideos();

    function switchMode(mode, targetIdx) {
      document.getElementById('playbook-view').style.display = mode === 'playbook' ? 'block' : 'none';
      document.getElementById('full-video-view').style.display = mode === 'video' ? 'block' : 'none';
      document.getElementById('tab-playbook').classList.toggle('active', mode === 'playbook');
      document.getElementById('tab-video').classList.toggle('active', mode === 'video');

      if (mode === 'video') {
        window.scrollTo({ top: 0, behavior: 'smooth' });
        const idxToPlay = typeof targetIdx === 'number' ? targetIdx : currentChapterIdx;
        renderVideoChapter(idxToPlay);
      }
    }

    function handleTocClick(stepId, idx) {
      if (document.getElementById('full-video-view').style.display === 'block') {
        renderVideoChapter(idx);
      } else {
        const el = document.getElementById('ch-' + stepId);
        if (el) el.scrollIntoView({ behavior: 'smooth' });
      }
    }

    function jumpToVideoChapter(idx) {
      switchMode('video', idx);
    }

    function renderVideoChapter(idx) {
      if (idx < 0 || idx >= data.steps.length) return;
      currentChapterIdx = idx;
      const step = data.steps[idx];

      const numStr = idx + 1 < 10 ? '0' + (idx + 1) : (idx + 1);
      document.getElementById('video-chapter-badge').textContent = 'Capítulo ' + numStr;
      document.getElementById('video-chapter-title').textContent = step.title || ('Capítulo ' + (idx + 1));
      document.getElementById('video-chapter-desc').textContent = step.description || '';
      document.getElementById('video-counter').textContent = (idx + 1) + ' / ' + data.steps.length;

      const player = document.getElementById('main-player');
      if (step.image) {
        player.poster = step.image;
      }

      if (step.video) {
        player.pause();
        const playableUrl = getStreamableUrl(idx, step.video);
        player.src = playableUrl;
        player.load();
        player.play().catch(e => console.log('Autoplay notification:', e));
        player.onended = () => {
          if (currentChapterIdx < data.steps.length - 1) {
            renderVideoChapter(currentChapterIdx + 1);
          }
        };
      } else {
        player.src = '';
      }

      // Render timeline segments
      const segContainer = document.getElementById('video-segments');
      segContainer.innerHTML = '';
      data.steps.forEach((st, i) => {
        const bar = document.createElement('div');
        bar.className = 'segment-bar' + (i === idx ? ' active' : '');
        bar.title = 'Capítulo ' + (i + 1) + ': ' + (st.title || '');
        bar.onclick = () => renderVideoChapter(i);
        segContainer.appendChild(bar);
      });
    }

    function prevChapter() { if (currentChapterIdx > 0) renderVideoChapter(currentChapterIdx - 1); }
    function nextChapter() { if (currentChapterIdx < data.steps.length - 1) renderVideoChapter(currentChapterIdx + 1); }
  </script>
</body>
</html>`;
}

function escapeHtml(str: string): string {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function renderNote(step: any): string {
  if (!step.noteType || step.noteType === 'none' || !step.noteText) return '';
  const prefix = step.noteType === 'tip' ? '💡 Tip:' : step.noteType === 'warning' ? '⚠️ Importante:' : 'ℹ️ Nota:';
  return `<div class="note-box note-${step.noteType}"><strong>${prefix}</strong> ${escapeHtml(step.noteText)}</div>`;
}
