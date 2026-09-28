import type { Tutorial, Step } from '../types';
import { toPlayableVideoUrl } from '../utils/media';

export interface CompilationProgress {
  currentStep: number;
  totalSteps: number;
  status: string;
  percent: number;
}

export async function compileTutorialToVideo(
  tutorial: Tutorial,
  onProgress?: (p: CompilationProgress) => void
): Promise<Blob> {
  const steps = tutorial.steps;
  if (!steps.length) throw new Error('El tutorial no tiene capítulos para compilar.');

  const width = 1920;
  const height = 1080;

  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('No se pudo inicializar el contexto 2D del canvas');

  // Setup AudioContext for clean mixed sound
  const AudioCtxClass = window.AudioContext || (window as any).webkitAudioContext;
  const audioCtx = new AudioCtxClass();
  const audioDest = audioCtx.createMediaStreamDestination();

  // Canvas Stream at 30fps
  const canvasStream = canvas.captureStream(30);
  const audioTracks = audioDest.stream.getAudioTracks();

  const combinedStream = new MediaStream([
    ...canvasStream.getVideoTracks(),
    ...(audioTracks.length > 0 ? audioTracks : []),
  ]);

  // Pick compatible mimeType
  const mimeTypes = [
    'video/webm;codecs=vp9,opus',
    'video/webm;codecs=vp8,opus',
    'video/webm',
    'video/mp4',
  ];
  let selectedMime = 'video/webm';
  for (const m of mimeTypes) {
    if (MediaRecorder.isTypeSupported(m)) {
      selectedMime = m;
      break;
    }
  }

  const mediaRecorder = new MediaRecorder(combinedStream, {
    mimeType: selectedMime,
    videoBitsPerSecond: 3500000,
  });

  const chunks: Blob[] = [];
  mediaRecorder.ondataavailable = (e) => {
    if (e.data && e.data.size > 0) chunks.push(e.data);
  };

  const recordingPromise = new Promise<Blob>((resolve) => {
    mediaRecorder.onstop = () => {
      const finalBlob = new Blob(chunks, { type: selectedMime });
      audioCtx.close().catch(() => {});
      resolve(finalBlob);
    };
  });

  mediaRecorder.start(250);

  // Initial black frame to kickstart the stream
  ctx.fillStyle = '#0f172a';
  ctx.fillRect(0, 0, width, height);

  // Render loop across all steps
  for (let i = 0; i < steps.length; i++) {
    const step = steps[i];
    const stepNum = i + 1;

    onProgress?.({
      currentStep: stepNum,
      totalSteps: steps.length,
      status: `Unificando Capítulo ${stepNum} de ${steps.length}: ${step.title || 'Clip'}...`,
      percent: Math.round(((i) / steps.length) * 100),
    });

    if (step.video) {
      // Play actual video clip frame-by-frame onto canvas and stream its audio
      await renderVideoStep(ctx, width, height, step, stepNum, steps.length, audioCtx, audioDest);
    } else {
      // Render static image slide
      await renderStaticStep(ctx, width, height, step, stepNum, steps.length, audioCtx, audioDest);
    }
  }

  onProgress?.({
    currentStep: steps.length,
    totalSteps: steps.length,
    status: 'Finalizando archivo de video...',
    percent: 100,
  });

  // Short buffer at end
  await waitMs(300);

  if (mediaRecorder.state !== 'inactive') {
    mediaRecorder.requestData();
    mediaRecorder.stop();
  }

  return await recordingPromise;
}

function renderVideoStep(
  ctx: CanvasRenderingContext2D,
  w: number,
  h: number,
  step: Step,
  stepNum: number,
  totalSteps: number,
  audioCtx: AudioContext,
  audioDest: MediaStreamAudioDestinationNode
): Promise<void> {
  return new Promise((resolve) => {
    const video = document.createElement('video');
    const srcUrl = toPlayableVideoUrl(step.video);
    video.src = srcUrl;
    video.crossOrigin = 'anonymous';
    video.playsInline = true;
    video.muted = false;

    let animId: number | null = null;
    let sourceNode: MediaElementAudioSourceNode | null = null;
    let isCleanedUp = false;

    const cleanup = () => {
      if (isCleanedUp) return;
      isCleanedUp = true;
      if (animId) cancelAnimationFrame(animId);
      if (sourceNode) {
        try {
          sourceNode.disconnect();
        } catch (e) {}
      }
      video.pause();
      video.removeAttribute('src');
      video.load();
      resolve();
    };

    video.oncanplay = () => {
      try {
        sourceNode = audioCtx.createMediaElementSource(video);
        sourceNode.connect(audioDest);
      } catch (err) {
        console.warn('Audio routing notice:', err);
      }

      video.play().catch(() => cleanup());

      const startTime = Date.now();
      const drawFrame = () => {
        if (isCleanedUp) return;

        // Clear and draw video frame
        ctx.fillStyle = '#000000';
        ctx.fillRect(0, 0, w, h);

        if (video.videoWidth > 0 && video.videoHeight > 0) {
          const scale = Math.min(w / video.videoWidth, h / video.videoHeight);
          const dw = video.videoWidth * scale;
          const dh = video.videoHeight * scale;
          const dx = (w - dw) / 2;
          const dy = (h - dh) / 2;
          ctx.drawImage(video, dx, dy, dw, dh);
        }

        // Draw modern chapter pill for the first 3.5 seconds
        const elapsed = (Date.now() - startTime) / 1000;
        if (elapsed < 3.5) {
          drawChapterOverlay(ctx, w, h, step, stepNum, totalSteps, Math.min(1, 3.5 - elapsed));
        }

        animId = requestAnimationFrame(drawFrame);
      };

      drawFrame();
    };

    video.onended = () => cleanup();
    video.onerror = () => cleanup();

    // Safety timeout in case video fails to end
    const maxDur = Math.max(8, (step.duration || 10) + 4) * 1000;
    setTimeout(() => cleanup(), maxDur);
  });
}

function renderStaticStep(
  ctx: CanvasRenderingContext2D,
  w: number,
  h: number,
  step: Step,
  stepNum: number,
  totalSteps: number,
  _audioCtx: AudioContext,
  _audioDest: MediaStreamAudioDestinationNode
): Promise<void> {
  return new Promise(async (resolve) => {
    let img: HTMLImageElement | null = null;
    if (step.image) {
      img = await loadImage(step.image);
    }

    const durationMs = 3500;
    const startTime = Date.now();
    let animId: number;

    const drawFrame = () => {
      const elapsed = Date.now() - startTime;
      if (elapsed >= durationMs) {
        cancelAnimationFrame(animId);
        resolve();
        return;
      }

      ctx.fillStyle = '#0f172a';
      ctx.fillRect(0, 0, w, h);

      if (img) {
        const scale = Math.min((w - 100) / img.width, (h - 220) / img.height);
        const dw = img.width * scale;
        const dh = img.height * scale;
        const dx = (w - dw) / 2;
        const dy = (h - dh) / 2;
        ctx.drawImage(img, dx, dy, dw, dh);
      }

      drawChapterOverlay(ctx, w, h, step, stepNum, totalSteps, 1);
      animId = requestAnimationFrame(drawFrame);
    };

    drawFrame();
  });
}

function drawChapterOverlay(
  ctx: CanvasRenderingContext2D,
  w: number,
  h: number,
  step: Step,
  stepNum: number,
  totalSteps: number,
  opacity = 1
) {
  ctx.save();
  ctx.globalAlpha = opacity;

  // Bottom modern banner
  const bannerH = 100;
  const bannerY = h - bannerH - 40;
  const bannerX = 50;
  const bannerW = w - 100;

  ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
  roundRect(ctx, bannerX, bannerY, bannerW, bannerH, 16);
  ctx.fill();
  ctx.strokeStyle = '#334155';
  ctx.lineWidth = 2;
  ctx.stroke();

  // Chapter pill
  const numStr = stepNum < 10 ? `0${stepNum}` : `${stepNum}`;
  ctx.fillStyle = '#2563eb';
  roundRect(ctx, bannerX + 20, bannerY + 20, 60, 60, 12);
  ctx.fill();
  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 26px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(numStr, bannerX + 50, bannerY + 58);
  ctx.textAlign = 'left';

  // Title
  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 28px sans-serif';
  ctx.fillText(step.title || `Capítulo ${stepNum}`, bannerX + 100, bannerY + 45);

  // Counter & App
  ctx.fillStyle = '#94a3b8';
  ctx.font = '18px sans-serif';
  ctx.fillText(`Capítulo ${stepNum} de ${totalSteps}`, bannerX + 100, bannerY + 75);

  ctx.restore();
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => resolve(img);
    img.onerror = () => resolve(img);
    img.src = src;
  });
}

function waitMs(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function roundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}
