import React, { useState, useRef, useEffect } from 'react';
import type { Tutorial } from '../types';
import {
  X,
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Volume2,
  VolumeX,
  ArrowLeft,
} from 'lucide-react';
import { toPlayableVideoUrl } from '../utils/media';

interface FullVideoPlayerModalProps {
  tutorial: Tutorial;
  isOpen: boolean;
  initialStepIndex?: number;
  onClose: () => void;
  onSwitchToPlaybook: () => void;
}

export const FullVideoPlayerModal: React.FC<FullVideoPlayerModalProps> = ({
  tutorial,
  isOpen,
  initialStepIndex = 0,
  onClose,
  onSwitchToPlaybook,
}) => {
  const [currentStepIdx, setCurrentStepIdx] = useState(initialStepIndex);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      setCurrentStepIdx(initialStepIndex);
      setIsPlaying(true);
    }
  }, [isOpen, initialStepIndex]);

  const currentStep = tutorial.steps[currentStepIdx];

  useEffect(() => {
    if (videoRef.current && currentStep?.video) {
      videoRef.current.currentTime = 0;
      if (isPlaying) {
        videoRef.current.play().catch(() => {});
      }
    }
  }, [currentStepIdx]);

  if (!isOpen || !currentStep) return null;

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
      setDuration(videoRef.current.duration || 0);
    }
  };

  const handleVideoEnded = () => {
    // Automatically transition to next chapter!
    if (currentStepIdx < tutorial.steps.length - 1) {
      setCurrentStepIdx((prev) => prev + 1);
    } else {
      setIsPlaying(false);
    }
  };

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
    } else {
      videoRef.current.play().catch(() => {});
      setIsPlaying(true);
    }
  };

  const jumpToStep = (index: number) => {
    setCurrentStepIdx(index);
    setIsPlaying(true);
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950 flex flex-col font-sans text-slate-100">
      {/* Top Header bar matching Guidde */}
      <header className="h-14 border-b border-slate-800 bg-slate-900/90 px-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={onClose}
            className="flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-slate-100 px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Volver al Editor
          </button>
          <div className="h-4 w-[1px] bg-slate-700" />
          <span className="px-2 py-0.5 rounded bg-blue-600/20 text-blue-400 border border-blue-500/30 text-xs font-bold uppercase">
            {tutorial.appName || 'Tobo4'}
          </span>
          <h2 className="text-sm font-bold truncate max-w-xl">
            {tutorial.title}
          </h2>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onSwitchToPlaybook}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition"
          >
            Ver Playbook / Texto
          </button>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded-lg transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </header>

      {/* Main Area: Sidebar Table of Contents + Video Player */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar Table of contents */}
        <aside className="w-72 border-r border-slate-800 bg-slate-950/60 flex flex-col">
          <div className="p-4 border-b border-slate-800/80">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Tabla de Contenido
            </span>
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-1">
            <div className="px-3 py-2 text-xs font-semibold text-blue-400 flex items-center gap-2 bg-blue-950/40 rounded-lg border border-blue-800/40 mb-2">
              <Play className="w-3 h-3 fill-current" /> Reproductor de Video
            </div>

            {tutorial.steps.map((step, idx) => {
              const numStr = idx + 1 < 10 ? `0${idx + 1}` : `${idx + 1}`;
              const isCurrent = currentStepIdx === idx;
              return (
                <button
                  key={step.id}
                  onClick={() => jumpToStep(idx)}
                  className={`w-full flex items-start gap-2.5 px-3 py-2 rounded-lg text-xs transition text-left ${
                    isCurrent
                      ? 'bg-slate-800 text-white font-semibold border-l-2 border-blue-500 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                  }`}
                >
                  <span className="font-mono text-[11px] opacity-70 mt-0.5">
                    {numStr}
                  </span>
                  <span className="truncate flex-1">
                    {step.title || `Capítulo ${idx + 1}`}
                  </span>
                  {step.video && (
                    <span className="text-[10px] text-emerald-400 font-mono">
                      {step.duration ? `${step.duration}s` : 'clip'}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </aside>

        {/* Center Main Video Stage */}
        <main className="flex-1 flex flex-col bg-black justify-between p-6 overflow-y-auto">
          <div className="flex-1 flex items-center justify-center relative max-w-5xl mx-auto w-full">
            {currentStep.video ? (
              <div className="w-full relative aspect-video bg-black rounded-2xl overflow-hidden shadow-2xl border border-slate-800 flex items-center justify-center">
                <video
                  ref={videoRef}
                  src={toPlayableVideoUrl(currentStep.video)}
                  muted={isMuted}
                  onTimeUpdate={handleTimeUpdate}
                  onEnded={handleVideoEnded}
                  playsInline
                  autoPlay
                  className="w-full h-full object-contain"
                />

                {/* Center Play Overlay when paused */}
                {!isPlaying && (
                  <button
                    onClick={togglePlay}
                    className="absolute w-20 h-20 rounded-full bg-blue-600/90 text-white flex items-center justify-center shadow-2xl hover:scale-110 transition"
                  >
                    <Play className="w-8 h-8 fill-current ml-1" />
                  </button>
                )}
              </div>
            ) : currentStep.image ? (
              <div className="w-full relative aspect-video bg-slate-950 rounded-2xl overflow-hidden shadow-2xl border border-slate-800 flex items-center justify-center">
                <img
                  src={currentStep.image}
                  alt={currentStep.title}
                  className="max-h-full max-w-full object-contain"
                />
                {currentStep.clickX !== undefined && currentStep.clickY !== undefined && (
                  <div
                    className="absolute pointer-events-none transform -translate-x-1/2 -translate-y-1/2"
                    style={{ left: `${currentStep.clickX}%`, top: `${currentStep.clickY}%` }}
                  >
                    <div className="w-8 h-8 rounded-full bg-rose-500/90 border-2 border-white shadow-[0_0_16px_rgba(244,63,94,0.9)] animate-pulse" />
                  </div>
                )}
              </div>
            ) : (
              <div className="text-slate-500 text-sm">
                No hay video ni captura grabada en este capítulo.
              </div>
            )}
          </div>

          {/* Video Control Bar & Segmented Chapter Bar */}
          <div className="max-w-5xl mx-auto w-full pt-4 space-y-3">
            {/* Segmented Timeline across all chapters */}
            <div className="flex gap-1.5 h-2 w-full">
              {tutorial.steps.map((st, i) => (
                <div
                  key={st.id}
                  onClick={() => jumpToStep(i)}
                  className={`flex-1 h-full rounded-full cursor-pointer transition-all ${
                    i === currentStepIdx
                      ? 'bg-blue-500 shadow-md'
                      : i < currentStepIdx
                      ? 'bg-blue-800/80 hover:bg-blue-600'
                      : 'bg-slate-800 hover:bg-slate-700'
                  }`}
                  title={`Capítulo ${i + 1}: ${st.title}`}
                />
              ))}
            </div>

            {/* Controls */}
            <div className="flex items-center justify-between px-2">
              <div className="flex items-center gap-4">
                <button
                  onClick={() => {
                    if (currentStepIdx > 0) jumpToStep(currentStepIdx - 1);
                  }}
                  disabled={currentStepIdx === 0}
                  className="p-1.5 text-slate-400 hover:text-slate-100 disabled:opacity-30 transition"
                  title="Capítulo anterior"
                >
                  <SkipBack className="w-4 h-4" />
                </button>

                <button
                  onClick={togglePlay}
                  className="w-10 h-10 rounded-full bg-blue-600 hover:bg-blue-500 text-white flex items-center justify-center transition shadow"
                >
                  {isPlaying ? (
                    <Pause className="w-4 h-4 fill-current" />
                  ) : (
                    <Play className="w-4 h-4 fill-current ml-0.5" />
                  )}
                </button>

                <button
                  onClick={() => {
                    if (currentStepIdx < tutorial.steps.length - 1) {
                      jumpToStep(currentStepIdx + 1);
                    }
                  }}
                  disabled={currentStepIdx === tutorial.steps.length - 1}
                  className="p-1.5 text-slate-400 hover:text-slate-100 disabled:opacity-30 transition"
                  title="Siguiente capítulo"
                >
                  <SkipForward className="w-4 h-4" />
                </button>

                <button
                  onClick={() => setIsMuted(!isMuted)}
                  className="text-slate-400 hover:text-slate-100 transition ml-2"
                >
                  {isMuted ? (
                    <VolumeX className="w-4 h-4 text-rose-400" />
                  ) : (
                    <Volume2 className="w-4 h-4" />
                  )}
                </button>

                <span className="text-xs text-slate-400 font-mono">
                  {formatTime(currentTime)} / {formatTime(duration)}
                </span>
              </div>

              <div className="flex items-center gap-3">
                <span className="text-xs font-semibold text-slate-300">
                  Capítulo {currentStepIdx + 1} de {tutorial.steps.length}:{' '}
                  <span className="text-blue-400">{currentStep.title}</span>
                </span>
              </div>
            </div>

            {/* Bottom Chapter Info (Matching Guidde image 1) */}
            <div className="border-t border-slate-900 pt-3 text-left">
              <div className="text-xs text-slate-400 flex items-center gap-2 mb-1">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                <span>{tutorial.author || 'Equipo Tobo4'}</span>
              </div>
              <p className="text-sm text-slate-300 leading-relaxed">
                {currentStep.description || tutorial.description}
              </p>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};
