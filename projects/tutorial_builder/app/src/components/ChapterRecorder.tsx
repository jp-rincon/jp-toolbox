import React, { useState, useRef, useEffect, useMemo } from 'react';
import {
  Video,
  Square,
  RotateCcw,
  Sparkles,
  Loader2,
  CheckCircle2,
  Trash2,
} from 'lucide-react';
import {
  startTabAndVoiceRecording,
} from '../services/screenRecorder';
import type { ActiveRecordingSession } from '../services/screenRecorder';
import { toPlayableVideoUrl } from '../utils/media';

interface ChapterRecorderProps {
  videoUrl?: Blob | string;
  duration?: number;
  onStartRecording?: () => void;
  onRecordingComplete: (result: {
    videoBlob: Blob;
    videoUrl: string;
    thumbnailDataUrl: string;
    transcript: string;
    durationSeconds: number;
  }) => void;
  onClearVideo: () => void;
}

export const ChapterRecorder: React.FC<ChapterRecorderProps> = ({
  videoUrl,
  duration,
  onStartRecording,
  onRecordingComplete,
  onClearVideo,
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [countdown, setCountdown] = useState<number | null>(null);
  const [seconds, setSeconds] = useState(0);
  const [liveTranscript, setLiveTranscript] = useState('');
  const sessionRef = useRef<ActiveRecordingSession | null>(null);
  const timerRef = useRef<number | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  // Convert any Blob or base64 into a streamable blob URL for Chromium
  const playableSrc = useMemo(() => {
    return toPlayableVideoUrl(videoUrl);
  }, [videoUrl]);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (sessionRef.current) sessionRef.current.cancel();
    };
  }, []);

  const handleStart = async () => {
    try {
      onStartRecording?.();
      setLiveTranscript('');
      setSeconds(0);

      const session = await startTabAndVoiceRecording({
        onCountdownTick: (c) => {
          setCountdown(c === 0 ? null : c);
        },
        onTranscriptUpdate: (text) => {
          setLiveTranscript(text);
        },
        onStreamEnded: () => {
          handleStop();
        },
      });

      sessionRef.current = session;
      setCountdown(null);
      setIsRecording(true);

      timerRef.current = window.setInterval(() => {
        setSeconds((prev) => prev + 1);
      }, 1000);
    } catch (err: any) {
      console.warn('Grabación cancelada o fallida:', err);
      setCountdown(null);
    }
  };

  const handleStop = async () => {
    if (!sessionRef.current || !isRecording) return;
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setIsRecording(false);
    setIsProcessing(true);

    try {
      const result = await sessionRef.current.stop();
      onRecordingComplete({
        videoBlob: result.videoBlob,
        videoUrl: result.videoUrl,
        thumbnailDataUrl: result.thumbnailDataUrl,
        transcript: result.transcript,
        durationSeconds: result.durationSeconds,
      });
    } catch (err) {
      console.error('Error al procesar el video grabado:', err);
    } finally {
      setIsProcessing(false);
      sessionRef.current = null;
    }
  };

  const formatSeconds = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  if (countdown !== null && countdown > 0) {
    return (
      <>
        {/* Fullscreen Fixed High-Visibility Overlay across entire window */}
        <div className="fixed inset-0 z-[99999] flex flex-col items-center justify-center bg-slate-950/85 backdrop-blur-md select-none">
          <div className="text-sm font-bold text-blue-400 uppercase tracking-widest mb-5">
            Prepárate para hablar en Tobo4...
          </div>
          <div className="w-36 h-36 rounded-full bg-blue-600/30 border-4 border-blue-500 flex items-center justify-center text-7xl font-black text-white shadow-[0_0_60px_rgba(59,130,246,0.9)] animate-pulse">
            {countdown}
          </div>
          <p className="text-sm text-slate-200 mt-6 font-medium">
            Escucha los pitidos en tus audífonos: cuando suene el último pitido agudo, empieza a hablar.
          </p>
        </div>

        {/* Card Placeholder */}
        <div className="flex flex-col items-center justify-center p-8 bg-slate-900/90 rounded-2xl border-2 border-blue-500 shadow-2xl text-center">
          <div className="text-xs font-bold text-blue-400 uppercase tracking-widest mb-2">
            Iniciando grabación...
          </div>
          <div className="w-14 h-14 rounded-full bg-blue-600/20 border-2 border-blue-500 flex items-center justify-center text-2xl font-bold text-white">
            {countdown}
          </div>
        </div>
      </>
    );
  }

  if (isProcessing) {
    return (
      <div className="flex flex-col items-center justify-center p-8 bg-slate-900/80 rounded-xl border border-slate-700 text-center">
        <Loader2 className="w-8 h-8 text-blue-400 animate-spin mb-2" />
        <p className="text-sm font-semibold text-slate-200">
          Procesando video y finalizando transcripción...
        </p>
      </div>
    );
  }

  if (isRecording) {
    return (
      <div className="flex flex-col gap-3 p-4 bg-rose-950/40 rounded-xl border border-rose-700/60 shadow-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-rose-500 animate-ping" />
            <span className="text-rose-400 font-mono font-bold text-sm">
              Grabando pestaña: {formatSeconds(seconds)}
            </span>
          </div>

          <button
            type="button"
            onClick={handleStop}
            className="flex items-center gap-1.5 px-4 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-bold shadow-md transition"
          >
            <Square className="w-3.5 h-3.5 fill-current" /> Detener y Guardar Clip
          </button>
        </div>

        {/* Live speech transcription badge */}
        <div className="bg-slate-900/90 rounded-lg p-2.5 border border-slate-800 text-xs">
          <div className="flex items-center gap-1.5 text-blue-400 font-semibold mb-1">
            <Sparkles className="w-3 h-3 text-sky-400 animate-spin" />
            Transcribiendo tu voz en tiempo real:
          </div>
          <p className="text-slate-300 italic min-h-[1.5rem]">
            {liveTranscript || 'Habla claro en el micrófono mientras realizas la acción en Tobo4...'}
          </p>
        </div>
      </div>
    );
  }

  if (playableSrc) {
    return (
      <div className="flex flex-col gap-2">
        <div className="relative group rounded-xl overflow-hidden border border-slate-700 bg-black aspect-video flex items-center justify-center">
          <video
            ref={videoRef}
            src={playableSrc}
            controls
            playsInline
            className="w-full h-full object-contain"
          />

          <div className="absolute top-2 right-2 flex items-center gap-1.5 bg-slate-900/80 backdrop-blur-sm p-1.5 rounded-lg border border-slate-700 opacity-90 group-hover:opacity-100 transition">
            <button
              type="button"
              onClick={handleStart}
              className="flex items-center gap-1 text-[11px] px-2.5 py-1 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded transition"
              title="Volver a grabar este capítulo sin tocar los demás"
            >
              <RotateCcw className="w-3 h-3" /> Regrabar clip
            </button>
            <button
              type="button"
              onClick={onClearVideo}
              className="p-1 text-slate-400 hover:text-rose-400 rounded transition"
              title="Eliminar este video"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <div className="flex items-center justify-between text-xs text-slate-400 px-1">
          <span className="flex items-center gap-1 text-emerald-400 font-medium">
            <CheckCircle2 className="w-3.5 h-3.5" /> Clip de video guardado
            {duration ? ` (${duration}s)` : ''}
          </span>
          <span className="text-[11px] text-slate-500">
            ¿Te equivocaste? Haz clic en "Regrabar clip" arriba a la derecha.
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="border-2 border-dashed border-slate-700 hover:border-blue-500/80 rounded-xl p-6 bg-slate-900/40 flex flex-col items-center justify-center min-h-[220px] text-center transition group">
      <div className="w-12 h-12 rounded-full bg-blue-600/10 flex items-center justify-center text-blue-400 mb-3 group-hover:scale-110 transition">
        <Video className="w-6 h-6" />
      </div>

      <p className="text-sm font-semibold text-slate-200 mb-1">
        Graba este paso en video con tu voz
      </p>
      <p className="text-xs text-slate-400 mb-4 max-w-sm">
        Selecciona la pestaña de Tobo4, escucha la cuenta regresiva (3.. 2.. 1..) y habla por el micrófono describiendo la acción.
      </p>

      <button
        type="button"
        onClick={handleStart}
        className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-sky-500 hover:from-blue-500 hover:to-sky-400 text-white rounded-xl text-xs font-bold shadow-lg shadow-blue-500/20 transition active:scale-95"
      >
        <Video className="w-4 h-4" /> Grabar Pestaña y Voz (Micrófono)
      </button>
    </div>
  );
};
