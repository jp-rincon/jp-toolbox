import React, { useState, useEffect, useRef } from 'react';
import type { Tutorial } from '../types';
import {
  X,
  ChevronLeft,
  ChevronRight,
  Volume2,
  VolumeX,
  Download,
  CheckCircle2,
} from 'lucide-react';
import { generateStandaloneHtml } from '../services/htmlExporter';

interface InteractiveGuideModalProps {
  tutorial: Tutorial;
  isOpen: boolean;
  onClose: () => void;
}

export const InteractiveGuideModal: React.FC<InteractiveGuideModalProps> = ({
  tutorial,
  isOpen,
  onClose,
}) => {
  const [currentIdx, setCurrentIdx] = useState(0);
  const [autoplayAudio, setAutoplayAudio] = useState(true);
  const [isMuted, setIsMuted] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      setCurrentIdx(0);
    }
  }, [isOpen]);

  const step = tutorial.steps[currentIdx];

  useEffect(() => {
    if (!isOpen || !step) return;

    if (step.audio && audioRef.current && autoplayAudio && !isMuted) {
      audioRef.current.currentTime = 0;
      audioRef.current.play().catch(() => {});
    }
  }, [currentIdx, isOpen, step, autoplayAudio, isMuted]);

  if (!isOpen || !step) return null;

  const totalSteps = tutorial.steps.length;
  const progressPercent = Math.round(((currentIdx + 1) / totalSteps) * 100);

  const handleNext = () => {
    if (currentIdx < totalSteps - 1) {
      setCurrentIdx((prev) => prev + 1);
    }
  };

  const handlePrev = () => {
    if (currentIdx > 0) {
      setCurrentIdx((prev) => prev - 1);
    }
  };

  const handleDownloadHtml = async () => {
    const html = await generateStandaloneHtml(tutorial);
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${tutorial.title.toLowerCase().replace(/\s+/g, '_')}_guia.html`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-5xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/90">
          <div className="flex items-center gap-3">
            <span className="px-2.5 py-0.5 rounded-full bg-blue-600/20 text-blue-400 border border-blue-500/30 text-xs font-semibold">
              {tutorial.appName || 'Tobo4'}
            </span>
            <h2 className="text-base font-bold text-slate-100 truncate max-w-md">
              {tutorial.title}
            </h2>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleDownloadHtml}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold transition shadow"
            >
              <Download className="w-3.5 h-3.5" /> Descargar Guía HTML
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-slate-800 h-1.5">
          <div
            className="bg-blue-600 h-full transition-all duration-300"
            style={{ width: `${progressPercent}%` }}
          />
        </div>

        {/* Step Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 tracking-wider uppercase">
              Paso {currentIdx + 1} de {totalSteps}
            </span>
            <div className="flex items-center gap-4 text-xs text-slate-400">
              <label className="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoplayAudio}
                  onChange={(e) => setAutoplayAudio(e.target.checked)}
                  className="rounded bg-slate-800 border-slate-700 text-blue-600"
                />
                Auto-reproducir voz
              </label>
              <button
                onClick={() => setIsMuted(!isMuted)}
                className="hover:text-slate-200 transition"
              >
                {isMuted ? <VolumeX className="w-4 h-4 text-rose-400" /> : <Volume2 className="w-4 h-4 text-emerald-400" />}
              </button>
            </div>
          </div>

          <h3 className="text-xl font-bold text-slate-100">{step.title}</h3>

          {step.description && (
            <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-line">
              {step.description}
            </p>
          )}

          {/* Note Callout */}
          {step.noteType !== 'none' && step.noteText && (
            <div
              className={`p-3 rounded-xl text-xs font-medium border ${
                step.noteType === 'tip'
                  ? 'bg-emerald-950/40 text-emerald-300 border-emerald-700/50'
                  : step.noteType === 'warning'
                  ? 'bg-amber-950/40 text-amber-300 border-amber-700/50'
                  : 'bg-sky-950/40 text-sky-300 border-sky-700/50'
              }`}
            >
              {step.noteType === 'tip' ? '💡 Tip: ' : step.noteType === 'warning' ? '⚠️ Importante: ' : 'ℹ️ Nota: '}
              {step.noteText}
            </div>
          )}

          {/* Image & Click Marker */}
          {step.image ? (
            <div className="relative rounded-xl overflow-hidden border border-slate-800 bg-slate-950 flex items-center justify-center">
              <img
                src={step.image}
                alt={step.title}
                className="max-h-[500px] w-full object-contain select-none"
              />
              {step.clickX !== undefined && step.clickY !== undefined && (
                <div
                  className="absolute pointer-events-none transform -translate-x-1/2 -translate-y-1/2"
                  style={{ left: `${step.clickX}%`, top: `${step.clickY}%` }}
                >
                  <div className="w-8 h-8 rounded-full bg-rose-500/90 border-2 border-white shadow-[0_0_16px_rgba(244,63,94,0.9)] animate-pulse" />
                </div>
              )}
            </div>
          ) : (
            <div className="p-8 border border-dashed border-slate-800 rounded-xl text-center text-slate-500 text-sm">
              Sin captura de pantalla en este paso.
            </div>
          )}

          {step.audio && (
            <audio
              ref={audioRef}
              src={step.audio}
              muted={isMuted}
              controls
              className="w-full mt-2"
            />
          )}
        </div>

        {/* Footer Nav Controls */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-slate-800 bg-slate-900/90">
          <button
            onClick={handlePrev}
            disabled={currentIdx === 0}
            className="flex items-center gap-1.5 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-sm font-medium border border-slate-700 disabled:opacity-30 disabled:pointer-events-none transition"
          >
            <ChevronLeft className="w-4 h-4" /> Anterior
          </button>

          <span className="text-xs font-medium text-slate-400">
            {currentIdx + 1} de {totalSteps}
          </span>

          {currentIdx === totalSteps - 1 ? (
            <button
              onClick={onClose}
              className="flex items-center gap-1.5 px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-sm font-semibold shadow-md transition"
            >
              <CheckCircle2 className="w-4 h-4" /> Finalizar Vista Previa
            </button>
          ) : (
            <button
              onClick={handleNext}
              className="flex items-center gap-1.5 px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-sm font-semibold shadow-md transition"
            >
              Siguiente <ChevronRight className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
