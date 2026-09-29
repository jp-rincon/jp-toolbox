export interface ScreenRecordingResult {
  videoBlob: Blob;
  videoUrl: string;
  thumbnailDataUrl: string;
  transcript: string;
  durationSeconds: number;
}

export interface ActiveRecordingSession {
  stop: () => Promise<ScreenRecordingResult>;
  cancel: () => void;
  onTranscriptUpdate?: (liveText: string) => void;
}

export async function startTabAndVoiceRecording(options: {
  onTranscriptUpdate?: (liveText: string) => void;
  onStreamEnded?: () => void;
  onCountdownTick?: (secondsLeft: number) => void;
}): Promise<ActiveRecordingSession> {
  // 1. Capture screen/tab (Edge switches focus to Tobo4 here)
  const displayStream = await navigator.mediaDevices.getDisplayMedia({
    video: {
      displaySurface: 'browser',
    },
    audio: false, // Llega deshabilitado por defecto
  });

  // Listen if user clicks browser's native "Dejar de compartir" button
  displayStream.getVideoTracks()[0].onended = () => {
    options.onStreamEnded?.();
  };

  // 2. Audible & Visual 3-Second Countdown before recording starts
  // CRITICAL: Runs BEFORE opening the microphone session, preventing OS/Chromium audio session interruption
  const originalTitle = document.title;
  let countdownAudioHandle: { stop: () => void } | null = null;
  if (options.onCountdownTick) {
    countdownAudioHandle = playContinuousCountdownAudio();

    for (let c = 3; c > 0; c--) {
      document.title = `🔴 [ ${c} ] Prepárate...`;
      options.onCountdownTick(c);
      await waitMs(1000);
    }
    document.title = `🔴 ¡GRABANDO TOBO4!`;
    options.onCountdownTick(0);
    countdownAudioHandle = null;
  }

  // 3. Capture microphone voice now (at tick 0 when recording begins)
  let micStream: MediaStream | null = null;
  try {
    micStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });
  } catch (e) {
    console.warn('No se pudo acceder al micrófono para la voz:', e);
  }

  // 4. Audio Mixing using AudioContext
  const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
  const audioDest = audioCtx.createMediaStreamDestination();

  // Route tab audio if present
  if (displayStream.getAudioTracks().length > 0) {
    const tabSource = audioCtx.createMediaStreamSource(
      new MediaStream([displayStream.getAudioTracks()[0]])
    );
    tabSource.connect(audioDest);
  }

  // Route mic audio if present
  if (micStream && micStream.getAudioTracks().length > 0) {
    const micSource = audioCtx.createMediaStreamSource(micStream);
    micSource.connect(audioDest);
  }

  // 5. Combined Stream (Screen video + Mixed audio tracks if any)
  const audioTracks = audioDest.stream.getAudioTracks();
  const combinedStream = new MediaStream([
    ...displayStream.getVideoTracks(),
    ...(audioTracks.length > 0 ? audioTracks : []),
  ]);

  // 6. Select compatible MediaRecorder mime type
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
    videoBitsPerSecond: 3000000,
  });

  const chunks: Blob[] = [];
  mediaRecorder.ondataavailable = (e) => {
    if (e.data && e.data.size > 0) {
      chunks.push(e.data);
    }
  };

  // 7. Speech Recognition Setup (Web Speech API)
  let accumulatedTranscript = '';
  let currentInterim = '';
  let recognitionInstance: any = null;
  let isActivelyRecording = true;
  let isRecognitionRunning = false;
  const SpeechRecognition =
    (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

  if (SpeechRecognition) {
    try {
      recognitionInstance = new SpeechRecognition();
      recognitionInstance.lang = 'es-CO'; // Español
      recognitionInstance.continuous = true;
      recognitionInstance.interimResults = true;

      recognitionInstance.onstart = () => {
        isRecognitionRunning = true;
      };

      recognitionInstance.onresult = (event: any) => {
        let interim = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const trans = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            accumulatedTranscript += (accumulatedTranscript ? ' ' : '') + trans.trim();
          } else {
            interim += trans;
          }
        }
        currentInterim = interim.trim();
        const fullCurrent = (accumulatedTranscript + (currentInterim ? ' ' + currentInterim : '')).trim();
        options.onTranscriptUpdate?.(fullCurrent);
      };

      recognitionInstance.onerror = (err: any) => {
        const errType = err?.error || err;
        console.warn('SpeechRecognition notification/error:', errType);
      };

      // Chrome/Edge naturally ends speech recognition sessions after ~60s or pauses in speech ('no-speech').
      // Auto-restart keeps recognition running uninterrupted for long recordings (3m, 5m, 10m+)!
      recognitionInstance.onend = () => {
        isRecognitionRunning = false;
        if (isActivelyRecording) {
          try {
            recognitionInstance.start();
          } catch (e) {
            setTimeout(() => {
              if (isActivelyRecording && !isRecognitionRunning) {
                try {
                  recognitionInstance.start();
                } catch (err) {}
              }
            }, 150);
          }
        }
      };
    } catch (err) {
      console.warn('No se pudo inicializar SpeechRecognition:', err);
    }
  }

  // Helper to cleanup hardware streams AFTER recording finishes
  const cleanupStreams = () => {
    if (countdownAudioHandle) {
      countdownAudioHandle.stop();
      countdownAudioHandle = null;
    }
    document.title = originalTitle || 'Tutorial Builder';
    isActivelyRecording = false;
    if (recognitionInstance) {
      try {
        recognitionInstance.stop();
      } catch (e) {}
    }
    displayStream.getTracks().forEach((t) => t.stop());
    if (micStream) micStream.getTracks().forEach((t) => t.stop());
    combinedStream.getTracks().forEach((t) => t.stop());
    audioCtx.close().catch(() => {});
  };

  // Listen if user clicks browser's native "Dejar de compartir" button
  displayStream.getVideoTracks()[0].onended = () => {
    options.onStreamEnded?.();
  };

  // START RECORDING NOW
  const startTime = Date.now();
  mediaRecorder.start(250);
  if (recognitionInstance) {
    try {
      recognitionInstance.start();
    } catch (e) {}
  }

  return {
    cancel: () => {
      if (countdownAudioHandle) {
        countdownAudioHandle.stop();
        countdownAudioHandle = null;
      }
      document.title = originalTitle || 'Tutorial Builder';
      if (mediaRecorder.state !== 'inactive') {
        try {
          mediaRecorder.stop();
        } catch (e) {}
      }
      cleanupStreams();
    },
    stop: async () => {
      const durationSeconds = Math.max(1, Math.round((Date.now() - startTime) / 1000));

      const recordingPromise = new Promise<Blob>((resolve) => {
        mediaRecorder.onstop = () => {
          cleanupStreams();
          const finalBlob = new Blob(chunks, { type: selectedMime });
          resolve(finalBlob);
        };
      });

      if (mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
      } else {
        cleanupStreams();
      }

      const videoBlob = await recordingPromise;
      const videoUrl = URL.createObjectURL(videoBlob);

      // Extract a thumbnail frame from the video with robust fallback
      const thumbnailDataUrl = await extractThumbnailFromVideo(videoBlob);

      const finalFullTranscript = (accumulatedTranscript + (currentInterim ? ' ' + currentInterim : '')).trim();

      return {
        videoBlob,
        videoUrl,
        thumbnailDataUrl,
        transcript: finalFullTranscript,
        durationSeconds,
      };
    },
  };
}

function waitMs(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

let cachedCleanWavUrl: string | null = null;

function getCleanCountdownWavUrl(): string {
  if (cachedCleanWavUrl) return cachedCleanWavUrl;

  const sampleRate = 22050;
  const totalDuration = 3.6;
  const numSamples = Math.floor(sampleRate * totalDuration);
  const buffer = new ArrayBuffer(44 + numSamples * 2);
  const view = new DataView(buffer);

  // RIFF identifier
  view.setUint32(0, 0x52494646, false); // "RIFF"
  view.setUint32(4, 36 + numSamples * 2, true);
  view.setUint32(8, 0x57415645, false); // "WAVE"
  // fmt chunk
  view.setUint32(12, 0x666d7420, false); // "fmt "
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, 1, true); // 1 channel (mono)
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  // data chunk
  view.setUint32(36, 0x64617461, false); // "data"
  view.setUint32(40, numSamples * 2, true);

  // Micro-dither (+-1 / 32767) keeps Edge/Chromium media subsystem continuously streaming
  for (let i = 0; i < numSamples; i++) {
    view.setInt16(44 + i * 2, i % 2 === 0 ? 1 : -1, true);
  }

  // Classic 3-second countdown: 3, 2, 1 y ¡Arranque!
  const beeps = [
    { start: 0.0, freq: 520, dur: 0.16 }, // Tick 3
    { start: 1.0, freq: 520, dur: 0.16 }, // Tick 2
    { start: 2.0, freq: 520, dur: 0.16 }, // Tick 1
    { start: 3.0, freq: 880, dur: 0.28 }, // Tick 0 (¡Arranque!)
  ];

  for (const beep of beeps) {
    const startIndex = Math.floor(beep.start * sampleRate);
    const beepSamples = Math.floor(beep.dur * sampleRate);

    for (let i = 0; i < beepSamples; i++) {
      const idx = startIndex + i;
      if (idx >= numSamples) break;

      const t = i / sampleRate;
      const attack = Math.min(1, i / (sampleRate * 0.012));
      const release = Math.min(1, (beepSamples - i) / (sampleRate * 0.04));
      const envelope = attack * release;
      const sample = Math.sin(2 * Math.PI * beep.freq * t) * envelope * 0.85;

      view.setInt16(44 + idx * 2, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
    }
  }

  const blob = new Blob([buffer], { type: 'audio/wav' });
  cachedCleanWavUrl = URL.createObjectURL(blob);
  return cachedCleanWavUrl;
}

function playContinuousCountdownAudio(): { stop: () => void } {
  let audio = document.getElementById('tb-countdown-audio') as HTMLAudioElement;
  if (!audio) {
    audio = document.createElement('audio');
    audio.id = 'tb-countdown-audio';
    audio.style.display = 'none';
    document.body.appendChild(audio);
  }
  audio.src = getCleanCountdownWavUrl();
  audio.volume = 1.0;
  audio.currentTime = 0;
  audio.play().catch((err) => {
    console.warn('Error al reproducir audio de cuenta regresiva:', err);
  });

  return {
    stop: () => {
      try {
        audio.pause();
        audio.currentTime = 0;
      } catch (e) {}
    },
  };
}

export function playStandaloneCountdownPreview(): { stop: () => void } {
  return playContinuousCountdownAudio();
}

export function extractThumbnailFromVideo(videoBlob: Blob): Promise<string> {
  return new Promise((resolve) => {
    const video = document.createElement('video');
    const blobUrl = URL.createObjectURL(videoBlob);
    video.src = blobUrl;
    video.muted = true;
    video.playsInline = true;

    // Safety timeout: Never hang longer than 1.2s if video seeking fails
    const timeoutId = setTimeout(() => {
      URL.revokeObjectURL(blobUrl);
      resolve('');
    }, 1200);

    const captureFrame = () => {
      try {
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth || 1280;
        canvas.height = video.videoHeight || 720;
        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
          clearTimeout(timeoutId);
          URL.revokeObjectURL(blobUrl);
          resolve(dataUrl);
          return;
        }
      } catch (err) {
        console.warn('Error capturando thumbnail del video:', err);
      }
      clearTimeout(timeoutId);
      URL.revokeObjectURL(blobUrl);
      resolve('');
    };

    video.onloadeddata = () => {
      video.currentTime = 0.2;
    };

    video.onseeked = () => {
      captureFrame();
    };

    video.onerror = () => {
      clearTimeout(timeoutId);
      URL.revokeObjectURL(blobUrl);
      resolve('');
    };
  });
}
