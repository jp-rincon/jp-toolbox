import React, { useState, useEffect } from 'react';
import type { Tutorial } from '../types';
import { compileTutorialToVideo } from '../services/videoCompiler';
import type { CompilationProgress } from '../services/videoCompiler';
import { X, Video, Download, Loader2, CheckCircle2 } from 'lucide-react';

interface VideoExportModalProps {
  tutorial: Tutorial;
  isOpen: boolean;
  onClose: () => void;
}

export const VideoExportModal: React.FC<VideoExportModalProps> = ({
  tutorial,
  isOpen,
  onClose,
}) => {
  const [isCompiling, setIsCompiling] = useState(false);
  const [progress, setProgress] = useState<CompilationProgress>({
    currentStep: 0,
    totalSteps: tutorial.steps.length,
    status: 'Iniciando compilador...',
    percent: 0,
  });
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const startCompilation = async () => {
    setIsCompiling(true);
    setError(null);
    setVideoUrl(null);
    try {
      const blob = await compileTutorialToVideo(tutorial, (p) => {
        setProgress(p);
      });
      const url = URL.createObjectURL(blob);
      setVideoUrl(url);
    } catch (err: any) {
      setError(err?.message || 'Ocurrió un error compilando el video.');
    } finally {
      setIsCompiling(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      startCompilation();
    } else {
      if (videoUrl) {
        URL.revokeObjectURL(videoUrl);
        setVideoUrl(null);
      }
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleDownload = () => {
    if (!videoUrl) return;
    const a = document.createElement('a');
    a.href = videoUrl;
    const safeName = tutorial.title.toLowerCase().replace(/\s+/g, '_');
    a.download = `${safeName}_tutorial.webm`;
    a.click();
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-3xl overflow-hidden shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
          <div className="flex items-center gap-2 text-slate-100 font-bold text-base">
            <Video className="w-5 h-5 text-blue-400" />
            Compilador de Video Automático
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {error ? (
            <div className="p-4 bg-rose-950/50 border border-rose-800 rounded-xl text-rose-300 text-sm">
              <p className="font-semibold mb-1">Error al generar el video:</p>
              <p>{error}</p>
              <button
                onClick={startCompilation}
                className="mt-4 px-4 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-semibold"
              >
                Reintentar
              </button>
            </div>
          ) : isCompiling ? (
            <div className="py-10 text-center space-y-5">
              <div className="w-16 h-16 rounded-full bg-blue-600/10 border border-blue-500/20 flex items-center justify-center mx-auto text-blue-400 animate-spin">
                <Loader2 className="w-8 h-8" />
              </div>

              <div>
                <h3 className="text-lg font-bold text-slate-100 mb-1">
                  Ensamblando capturas y pistas de voz...
                </h3>
                <p className="text-xs text-slate-400">{progress.status}</p>
              </div>

              {/* Progress Bar */}
              <div className="max-w-md mx-auto">
                <div className="flex justify-between text-xs text-slate-400 mb-1.5 font-medium">
                  <span>Progreso</span>
                  <span>{progress.percent}%</span>
                </div>
                <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden border border-slate-700">
                  <div
                    className="bg-gradient-to-r from-blue-600 to-sky-400 h-full transition-all duration-300"
                    style={{ width: `${progress.percent}%` }}
                  />
                </div>
              </div>

              <p className="text-xs text-slate-500">
                Se está procesando directamente en tu navegador en alta definición (1080p).
              </p>
            </div>
          ) : videoUrl ? (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-emerald-400 text-sm font-semibold">
                <CheckCircle2 className="w-4 h-4" />
                ¡Video compilado con éxito!
              </div>

              <div className="rounded-xl overflow-hidden border border-slate-800 bg-black aspect-video flex items-center justify-center">
                <video src={videoUrl} controls autoPlay className="w-full h-full" />
              </div>

              <div className="flex items-center justify-between pt-2">
                <div className="text-xs text-slate-400">
                  Formato WebM HD (Compatible con navegadores, Teams, Slack y YouTube).
                </div>
                <button
                  onClick={handleDownload}
                  className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-sm font-semibold shadow-lg transition"
                >
                  <Download className="w-4 h-4" /> Descargar Video
                </button>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};
