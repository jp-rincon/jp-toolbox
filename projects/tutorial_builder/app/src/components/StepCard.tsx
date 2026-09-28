import React, { useRef, useState } from 'react';
import type { Step } from '../types';
import { ChapterRecorder } from './ChapterRecorder';
import {
  Trash2,
  ChevronUp,
  ChevronDown,
  Copy,
  Image as ImageIcon,
  Video,
  X,
  Target,
  Sparkles,
} from 'lucide-react';

interface StepCardProps {
  step: Step;
  index: number;
  totalSteps: number;
  onUpdate: (updated: Step) => void;
  onDelete: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  onDuplicate: () => void;
}

export const StepCard: React.FC<StepCardProps> = ({
  step,
  index,
  totalSteps,
  onUpdate,
  onDelete,
  onMoveUp,
  onMoveDown,
  onDuplicate,
}) => {
  const [activeMediaTab, setActiveMediaTab] = useState<'video' | 'image'>(
    step.video ? 'video' : step.image ? 'image' : 'video'
  );
  const fileInputRef = useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    if (step.video) {
      setActiveMediaTab('video');
    }
  }, [step.video]);

  // Handle Ctrl+V inside the card for screenshot fallback
  const handlePaste = (e: React.ClipboardEvent) => {
    const items = e.clipboardData?.items;
    if (!items) return;

    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf('image') !== -1) {
        const file = items[i].getAsFile();
        if (file) {
          const reader = new FileReader();
          reader.onloadend = () => {
            onUpdate({ ...step, image: reader.result as string });
            setActiveMediaTab('image');
          };
          reader.readAsDataURL(file);
          e.preventDefault();
          break;
        }
      }
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        onUpdate({ ...step, image: reader.result as string });
        setActiveMediaTab('image');
      };
      reader.readAsDataURL(file);
    }
  };

  const handleImageClick = (e: React.MouseEvent<HTMLImageElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    onUpdate({
      ...step,
      clickX: Math.round(x * 10) / 10,
      clickY: Math.round(y * 10) / 10,
    });
  };

  return (
    <div
      onPaste={handlePaste}
      tabIndex={0}
      className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-5 shadow-xl transition-all hover:border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
    >
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 mb-4 border-b border-slate-700/60">
        <div className="flex items-center gap-3 flex-1 min-w-[260px]">
          <span className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-600/90 text-white font-bold text-sm shadow-md">
            {index + 1 < 10 ? `0${index + 1}` : index + 1}
          </span>
          <input
            type="text"
            value={step.title}
            onChange={(e) => onUpdate({ ...step, title: e.target.value })}
            placeholder={`Capítulo ${index + 1}: ej. Acceso al Módulo de Clientes`}
            className="flex-1 bg-slate-900/60 border border-slate-700 rounded-lg px-3 py-1.5 text-slate-100 font-semibold text-base focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Media mode selector & Action Buttons */}
        <div className="flex items-center gap-2">
          <div className="flex items-center bg-slate-900/80 p-0.5 rounded-lg border border-slate-700 text-xs">
            <button
              type="button"
              onClick={() => setActiveMediaTab('video')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md transition font-medium ${
                activeMediaTab === 'video'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Video className="w-3 h-3" /> Clip de Video
            </button>
            <button
              type="button"
              onClick={() => setActiveMediaTab('image')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md transition font-medium ${
                activeMediaTab === 'image'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <ImageIcon className="w-3 h-3" /> Captura Fija
            </button>
          </div>

          <div className="flex items-center gap-1 border-l border-slate-700/80 pl-2">
            <button
              type="button"
              onClick={onMoveUp}
              disabled={index === 0}
              className="p-1.5 text-slate-400 hover:text-slate-100 hover:bg-slate-700/60 rounded-lg disabled:opacity-30 transition"
              title="Mover arriba"
            >
              <ChevronUp className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={onMoveDown}
              disabled={index === totalSteps - 1}
              className="p-1.5 text-slate-400 hover:text-slate-100 hover:bg-slate-700/60 rounded-lg disabled:opacity-30 transition"
              title="Mover abajo"
            >
              <ChevronDown className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={onDuplicate}
              className="p-1.5 text-slate-400 hover:text-slate-100 hover:bg-slate-700/60 rounded-lg transition"
              title="Duplicar paso"
            >
              <Copy className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={onDelete}
              className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-950/40 rounded-lg transition"
              title="Eliminar paso"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Grid: Left Media, Right Transcript & Notes */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Media Column (7 cols) */}
        <div className="lg:col-span-7 flex flex-col gap-2">
          {activeMediaTab === 'video' ? (
            <ChapterRecorder
              videoUrl={step.video}
              duration={step.duration}
              onStartRecording={() => {
                // Clear previous transcript so new recording starts fresh
                onUpdate({ ...step, description: '' });
              }}
              onRecordingComplete={(res) => {
                // Update step with native video blob, extracted thumbnail, and new transcribed speech
                onUpdate({
                  ...step,
                  video: res.videoBlob,
                  image: res.thumbnailDataUrl || step.image,
                  duration: res.durationSeconds,
                  description: res.transcript || '',
                });
                setActiveMediaTab('video');
              }}
              onClearVideo={() => onUpdate({ ...step, video: undefined, duration: undefined })}
            />
          ) : (
            <div>
              {step.image ? (
                <div className="relative group rounded-xl overflow-hidden border border-slate-700 bg-slate-950 flex items-center justify-center min-h-[240px]">
                  <img
                    src={step.image}
                    alt={`Captura ${index + 1}`}
                    onClick={handleImageClick}
                    className="max-h-[360px] w-full object-contain cursor-crosshair select-none"
                    title="Haz clic para colocar el punto rojo"
                  />
                  {step.clickX !== undefined && step.clickY !== undefined && (
                    <div
                      className="absolute pointer-events-none transform -translate-x-1/2 -translate-y-1/2"
                      style={{ left: `${step.clickX}%`, top: `${step.clickY}%` }}
                    >
                      <div className="w-7 h-7 rounded-full bg-rose-500/90 border-2 border-white shadow-[0_0_12px_rgba(244,63,94,0.9)] animate-pulse" />
                    </div>
                  )}

                  <div className="absolute top-2 right-2 flex items-center gap-1.5 bg-slate-900/80 backdrop-blur-sm p-1.5 rounded-lg border border-slate-700 opacity-90 group-hover:opacity-100 transition">
                    {step.clickX !== undefined && (
                      <button
                        type="button"
                        onClick={() => onUpdate({ ...step, clickX: undefined, clickY: undefined })}
                        className="flex items-center gap-1 text-[11px] px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded"
                      >
                        <Target className="w-3 h-3 text-rose-400" /> Quitar punto
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => onUpdate({ ...step, image: undefined, clickX: undefined, clickY: undefined })}
                      className="p-1 hover:bg-rose-950/60 text-slate-400 hover:text-rose-400 rounded"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ) : (
                <div className="border-2 border-dashed border-slate-700 hover:border-blue-500/80 rounded-xl p-6 bg-slate-900/40 flex flex-col items-center justify-center min-h-[220px] text-center transition">
                  <div className="w-10 h-10 rounded-full bg-blue-600/10 flex items-center justify-center text-blue-400 mb-2">
                    <ImageIcon className="w-5 h-5" />
                  </div>
                  <p className="text-xs text-slate-300 mb-2">
                    Pega una captura con <kbd className="px-1.5 py-0.5 bg-slate-800 border border-slate-700 rounded text-blue-400">Ctrl + V</kbd> o sube una imagen:
                  </p>
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium border border-slate-700 transition"
                  >
                    Subir imagen
                  </button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                </div>
              )}
            </div>
          )}
        </div>

        {/* Text & Transcript Column (5 cols) */}
        <div className="lg:col-span-5 flex flex-col justify-between gap-4">
          <div className="space-y-3">
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-blue-400" />
                  Texto explicativo / Transcripción
                </label>
                <span className="text-[11px] text-slate-500">Editable libremente</span>
              </div>
              <textarea
                rows={6}
                value={step.description}
                onChange={(e) => onUpdate({ ...step, description: e.target.value })}
                placeholder="El texto de lo que dijiste en el video aparecerá aquí automáticamente transcrito. Puedes editar cualquier palabra o agregar más detalles."
                className="w-full bg-slate-900/70 border border-slate-700 rounded-xl p-3 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-blue-500 transition resize-none leading-relaxed"
              />
            </div>

            {/* Note Selector */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Nota / Advertencia (Opcional)
                </label>
                <div className="flex items-center gap-1">
                  {(['none', 'tip', 'warning', 'info'] as const).map((type) => (
                    <button
                      key={type}
                      type="button"
                      onClick={() => onUpdate({ ...step, noteType: type })}
                      className={`text-xs px-2 py-0.5 rounded transition ${
                        step.noteType === type
                          ? type === 'tip'
                            ? 'bg-emerald-950 text-emerald-400 border border-emerald-700'
                            : type === 'warning'
                            ? 'bg-amber-950 text-amber-400 border border-amber-700'
                            : type === 'info'
                            ? 'bg-sky-950 text-sky-400 border border-sky-700'
                            : 'bg-slate-700 text-slate-200'
                          : 'text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {type === 'none' ? 'Ninguna' : type === 'tip' ? '💡 Tip' : type === 'warning' ? '⚠️ Alerta' : 'ℹ️ Info'}
                    </button>
                  ))}
                </div>
              </div>

              {step.noteType !== 'none' && (
                <input
                  type="text"
                  value={step.noteText}
                  onChange={(e) => onUpdate({ ...step, noteText: e.target.value })}
                  placeholder="Escribe la nota importante para este paso..."
                  className="w-full bg-slate-900/80 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                />
              )}
            </div>
          </div>

          <div className="bg-slate-900/50 p-2.5 rounded-xl border border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
            <span>
              {step.video ? '✅ Video y transcripción vinculados' : 'ℹ️ Listo para grabar pestaña'}
            </span>
            {step.duration && <span>Duración: {step.duration}s</span>}
          </div>
        </div>
      </div>
    </div>
  );
};
