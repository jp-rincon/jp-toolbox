import React, { useState } from 'react';
import type { Tutorial } from '../types';
import {
  Play,
  Video,
  Printer,
  ChevronRight,
  ArrowLeft,
} from 'lucide-react';
import { toPlayableVideoUrl } from '../utils/media';

interface PlaybookViewProps {
  tutorial: Tutorial;
  onBackToEditor: () => void;
  onOpenFullVideo: (startStepIndex?: number) => void;
}

export const PlaybookView: React.FC<PlaybookViewProps> = ({
  tutorial,
  onBackToEditor,
  onOpenFullVideo,
}) => {
  const [activeStepId, setActiveStepId] = useState<string>(
    tutorial.steps[0]?.id || ''
  );

  const scrollToStep = (stepId: string) => {
    setActiveStepId(stepId);
    const element = document.getElementById(`playbook-step-${stepId}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans print:bg-white print:text-slate-900 print:min-h-0">
      {/* Top Bar */}
      <header className="sticky top-0 z-30 bg-slate-950/90 backdrop-blur-md border-b border-slate-800 px-6 py-3.5 flex items-center justify-between print:hidden">
        <div className="flex items-center gap-4">
          <button
            onClick={onBackToEditor}
            className="flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-slate-100 px-2.5 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Volver al Editor
          </button>
          <div className="h-4 w-[1px] bg-slate-700" />
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-blue-600/20 text-blue-400 border border-blue-500/30 text-xs font-bold uppercase">
              {tutorial.appName || 'Tobo4'}
            </span>
            <h1 className="text-base font-bold text-slate-100 truncate max-w-xl">
              {tutorial.title}
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => onOpenFullVideo(0)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow transition"
          >
            <Video className="w-3.5 h-3.5" /> Ver Video Completo
          </button>
          <button
            onClick={() => window.print()}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium border border-slate-700 transition"
          >
            <Printer className="w-3.5 h-3.5" /> Imprimir / PDF
          </button>
        </div>
      </header>

      {/* Main 2-Column Guidde-style Layout */}
      <div className="flex-1 max-w-7xl w-full mx-auto flex print:block print:max-w-full print:m-0">
        {/* Left Sidebar: Table of contents */}
        <aside className="w-72 hidden md:block sticky top-14 h-[calc(100vh-3.5rem)] overflow-y-auto border-r border-slate-800 p-4 bg-slate-950/40 print:hidden">
          <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 px-2">
            Table of contents
          </div>

          <nav className="space-y-1">
            <button
              onClick={() => onOpenFullVideo(0)}
              className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold text-blue-400 hover:bg-blue-950/40 transition text-left"
            >
              <Play className="w-3.5 h-3.5 fill-current" /> Video Tutorial
            </button>

            {tutorial.steps.map((step, idx) => {
              const numStr = idx + 1 < 10 ? `0${idx + 1}` : `${idx + 1}`;
              const isActive = activeStepId === step.id;
              return (
                <button
                  key={step.id}
                  onClick={() => scrollToStep(step.id)}
                  className={`w-full flex items-start gap-2 px-3 py-2 rounded-lg text-xs transition text-left ${
                    isActive
                      ? 'bg-slate-800 text-slate-100 font-semibold border-l-2 border-blue-500'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                  }`}
                >
                  <span className="font-mono text-[11px] opacity-70 flex-shrink-0 mt-0.5">
                    {numStr}
                  </span>
                  <span className="truncate flex-1">
                    {step.title || `Capítulo ${idx + 1}`}
                  </span>
                </button>
              );
            })}
          </nav>
        </aside>

        {/* Right Content: Guidde-style Playbook Chapters */}
        <main className="flex-1 p-6 md:p-10 space-y-12 overflow-y-auto max-w-4xl print:p-0 print:max-w-full print:space-y-8">
          <div className="border-b border-slate-800 pb-6 print:border-slate-200 print:pb-4">
            <h1 className="text-3xl font-extrabold text-slate-100 mb-2 print:text-slate-900">
              {tutorial.title}
            </h1>
            <p className="text-sm text-slate-400 leading-relaxed print:text-slate-600">
              {tutorial.description}
            </p>
          </div>

          {tutorial.steps.map((step, idx) => {
            const numStr = idx + 1 < 10 ? `0${idx + 1}` : `${idx + 1}`;
            return (
              <section
                key={step.id}
                id={`playbook-step-${step.id}`}
                className="scroll-mt-20 space-y-4 print:break-inside-avoid print:mb-8"
              >
                <div className="flex items-baseline gap-2">
                  <span className="text-xl font-mono font-bold text-blue-400 print:text-blue-600">
                    {numStr}
                  </span>
                  <h2 className="text-xl font-bold text-slate-100 print:text-slate-900">
                    {step.title || `Capítulo ${idx + 1}`}
                  </h2>
                </div>

                {step.description && (
                  <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-line print:text-slate-700">
                    {step.description}
                  </p>
                )}

                {/* Callout Note if any */}
                {step.noteType !== 'none' && step.noteText && (
                  <div
                    className={`p-3 rounded-xl text-xs font-medium border ${
                      step.noteType === 'tip'
                        ? 'bg-emerald-950/40 text-emerald-300 border-emerald-700/50 print:bg-emerald-50 print:text-emerald-800 print:border-emerald-300'
                        : step.noteType === 'warning'
                        ? 'bg-amber-950/40 text-amber-300 border-amber-700/50 print:bg-amber-50 print:text-amber-800 print:border-amber-300'
                        : 'bg-sky-950/40 text-sky-300 border-sky-700/50 print:bg-sky-50 print:text-sky-800 print:border-sky-300'
                    }`}
                  >
                    {step.noteType === 'tip'
                      ? '💡 Tip: '
                      : step.noteType === 'warning'
                      ? '⚠️ Importante: '
                      : 'ℹ️ Nota: '}
                    {step.noteText}
                  </div>
                )}

                {/* Video or Image with "Video content" badge */}
                {step.video ? (
                  <div className="relative rounded-2xl overflow-hidden border border-slate-800 bg-black aspect-video shadow-2xl print:border-slate-300 print:bg-slate-50 print:aspect-auto print:shadow-none">
                    <video
                      src={toPlayableVideoUrl(step.video)}
                      controls
                      playsInline
                      className="w-full h-full object-contain print:hidden"
                    />
                    {step.image && (
                      <div className="hidden print:block relative w-full">
                        <img
                          src={step.image}
                          alt={step.title}
                          className="w-full h-auto max-h-[500px] object-contain"
                        />
                        {step.clickX !== undefined && step.clickY !== undefined && (
                          <div
                            className="absolute pointer-events-none transform -translate-x-1/2 -translate-y-1/2"
                            style={{ left: `${step.clickX}%`, top: `${step.clickY}%` }}
                          >
                            <div className="w-8 h-8 rounded-full bg-rose-500 border-2 border-white" />
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ) : step.image ? (
                  <div className="relative rounded-2xl overflow-hidden border border-slate-800 bg-slate-950 shadow-2xl print:border-slate-300 print:bg-slate-50 print:shadow-none">
                    <img
                      src={step.image}
                      alt={step.title}
                      className="w-full h-auto max-h-[500px] object-contain"
                    />
                    {step.clickX !== undefined && step.clickY !== undefined && (
                      <div
                        className="absolute pointer-events-none transform -translate-x-1/2 -translate-y-1/2"
                        style={{ left: `${step.clickX}%`, top: `${step.clickY}%` }}
                      >
                        <div className="w-8 h-8 rounded-full bg-rose-500/90 border-2 border-white shadow-[0_0_16px_rgba(244,63,94,0.9)] animate-pulse print:animate-none" />
                      </div>
                    )}
                  </div>
                ) : null}

                {/* Jump to this step in video link (like Guidde!) */}
                <div className="pt-1 print:hidden">
                  <button
                    onClick={() => onOpenFullVideo(idx)}
                    className="inline-flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 font-semibold hover:underline"
                  >
                    <span>Jump to this step in video</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </section>
            );
          })}
        </main>
      </div>
    </div>
  );
};
