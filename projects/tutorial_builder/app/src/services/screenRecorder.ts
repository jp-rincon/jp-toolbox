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
  // 1. Capture screen/tab
  const displayStream = await navigator.mediaDevices.getDisplayMedia({
    video: {
      displaySurface: 'browser',
    },
    audio: false, // Llega deshabilitado por defecto para que no tengas que desmarcarlo
  });

  // 2. Capture microphone voice
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

  // 3. Audio Mixing using AudioContext
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

  // 4. Combined Stream (Screen video + Mixed audio tracks if any)
  const audioTracks = audioDest.stream.getAudioTracks();
  const combinedStream = new MediaStream([
    ...displayStream.getVideoTracks(),
    ...(audioTracks.length > 0 ? audioTracks : []),
  ]);

  // 5. Select compatible MediaRecorder mime type
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

  // 6. Speech Recognition Setup (Web Speech API)
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

  // 7. Audible & Visual 3-Second Countdown before recording starts
  const originalTitle = document.title;
  if (options.onCountdownTick) {
    if (audioCtx.state === 'suspended') {
      await audioCtx.resume().catch(() => {});
    }
    for (let c = 3; c > 0; c--) {
      document.title = `🔴 [ ${c} ] Prepárate...`;
      options.onCountdownTick(c);
      playCountdownBeep(audioCtx, 520, 0.16);
      await waitMs(1000);
    }
    document.title = `🔴 ¡GRABANDO TOBO4!`;
    options.onCountdownTick(0);
    playCountdownBeep(audioCtx, 880, 0.25);
  }

  // Helper to cleanup hardware streams AFTER recording finishes
  const cleanupStreams = () => {
    isActivelyRecording = false;
    document.title = originalTitle || 'Tutorial Builder';
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

function playCountdownBeep(ctx: AudioContext, freq = 520, duration = 0.15) {
  try {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(freq, ctx.currentTime);
    gain.gain.setValueAtTime(0.35, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + duration);
  } catch (e) {
    console.warn('Error playing beep:', e);
  }
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
