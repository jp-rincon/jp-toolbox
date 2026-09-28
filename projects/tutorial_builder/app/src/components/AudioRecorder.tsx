import React, { useState, useRef, useEffect } from 'react';
import { Mic, Square, Play, RotateCcw, Volume2, Sparkles } from 'lucide-react';

interface AudioRecorderProps {
  audioBase64?: string;
  onAudioChange: (base64?: string, duration?: number) => void;
  textToSpeak?: string;
}

export const AudioRecorder: React.FC<AudioRecorderProps> = ({
  audioBase64,
  onAudioChange,
  textToSpeak,
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const mr = new MediaRecorder(stream);
      mediaRecorderRef.current = mr;

      mr.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mr.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const reader = new FileReader();
        reader.onloadend = () => {
          onAudioChange(reader.result as string, recordingSeconds);
        };
        reader.readAsDataURL(audioBlob);
        stream.getTracks().forEach((track) => track.stop());
      };

      mr.start();
      setIsRecording(true);
      setRecordingSeconds(0);
      timerRef.current = window.setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      alert('No se pudo acceder al micrófono. Por favor permite el acceso en el navegador.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  const handlePlay = () => {
    if (!audioPlayerRef.current) return;
    if (isPlaying) {
      audioPlayerRef.current.pause();
      setIsPlaying(false);
    } else {
      audioPlayerRef.current.currentTime = 0;
      audioPlayerRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleSynthesizeTTS = () => {
    if (!textToSpeak || !textToSpeak.trim()) {
      alert('Escribe una descripción primero para sintetizar la voz.');
      return;
    }
    if (!window.speechSynthesis) {
      alert('Tu navegador no soporta síntesis de voz.');
      return;
    }

    const utter = new SpeechSynthesisUtterance(textToSpeak);
    utter.lang = 'es-ES';
    utter.rate = 1.0;

    // Optional audio playback preview
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utter);
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="flex flex-wrap items-center gap-3 bg-slate-900/80 p-3 rounded-xl border border-slate-700/60">
      {audioBase64 ? (
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <audio
            ref={audioPlayerRef}
            src={audioBase64}
            onEnded={() => setIsPlaying(false)}
            className="hidden"
          />
          <button
            type="button"
            onClick={handlePlay}
            className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow transition"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            {isPlaying ? 'Pausar Audio' : 'Escuchar Voz'}
          </button>

          <button
            type="button"
            onClick={() => onAudioChange(undefined, undefined)}
            className="flex items-center gap-1.5 px-2.5 py-1.5 bg-slate-800 hover:bg-rose-950/60 hover:text-rose-400 text-slate-300 rounded-lg text-xs font-medium border border-slate-700 transition"
            title="Borrar audio y volver a grabar"
          >
            <RotateCcw className="w-3 h-3" />
            Regrabar
          </button>
          <span className="text-xs text-emerald-400 font-medium flex items-center gap-1">
            <Volume2 className="w-3 h-3" /> Audio listo
          </span>
        </div>
      ) : isRecording ? (
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-rose-500 font-mono text-sm animate-pulse">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
            Grabando: {formatTime(recordingSeconds)}
          </div>
          <button
            type="button"
            onClick={stopRecording}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-semibold shadow transition"
          >
            <Square className="w-3 h-3 fill-current" />
            Detener
          </button>
        </div>
      ) : (
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={startRecording}
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white rounded-lg text-xs font-medium border border-slate-700 transition shadow-sm"
          >
            <Mic className="w-3.5 h-3.5 text-rose-400" />
            Grabar voz para este paso
          </button>
          {textToSpeak && (
            <button
              type="button"
              onClick={handleSynthesizeTTS}
              className="flex items-center gap-1.5 px-2.5 py-1.5 bg-slate-800/60 hover:bg-slate-700 text-slate-400 hover:text-sky-300 rounded-lg text-xs transition"
              title="Escuchar texto narrado con la voz del navegador"
            >
              <Sparkles className="w-3 h-3 text-sky-400" />
              Probar narración IA
            </button>
          )}
        </div>
      )}
    </div>
  );
};
