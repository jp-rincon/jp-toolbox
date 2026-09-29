import React, { useState } from 'react';
import type { Tutorial } from '../types';
import {
  FileText,
  Video,
  Play,
  Plus,
  FolderOpen,
  Check,
  Layers,
  BookOpen,
  Volume2,
} from 'lucide-react';
import { generateStandaloneHtml } from '../services/htmlExporter';
import { playStandaloneCountdownPreview } from '../services/screenRecorder';

interface NavbarProps {
  tutorial: Tutorial;
  tutorialsList: { id: string; title: string; updatedAt: number; stepsCount: number }[];
  currentView: 'editor' | 'playbook';
  onViewChange: (view: 'editor' | 'playbook') => void;
  onTitleChange: (newTitle: string) => void;
  onAppNameChange: (newApp: string) => void;
  onNewTutorial: () => void;
  onSelectTutorial: (id: string) => void;
  onOpenFullVideo: () => void;
  onOpenVideoExport: () => void;
  isSaving: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  tutorial,
  tutorialsList,
  currentView,
  onViewChange,
  onTitleChange,
  onAppNameChange,
  onNewTutorial,
  onSelectTutorial,
  onOpenFullVideo,
  onOpenVideoExport,
  isSaving,
}) => {
  const [showDropdown, setShowDropdown] = useState(false);
  const [isExportingHtml, setIsExportingHtml] = useState(false);

  const handleDownloadHtml = async () => {
    if (isExportingHtml) return;
    try {
      setIsExportingHtml(true);
      const html = await generateStandaloneHtml(tutorial);
      const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const safeTitle = tutorial.title.toLowerCase().replace(/\s+/g, '_');
      a.download = `${safeTitle}_playbook.html`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error('Error generando HTML:', err);
      alert('Error generando la guía HTML: ' + (err?.message || err));
    } finally {
      setIsExportingHtml(false);
    }
  };

  return (
    <header className="sticky top-0 z-40 bg-slate-900/95 backdrop-blur-md border-b border-slate-800 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex flex-wrap items-center justify-between gap-4">
        {/* Left: App Logo & Tutorial Title */}
        <div className="flex items-center gap-3 flex-1 min-w-[280px]">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-sky-400 flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
            <Layers className="w-5 h-5" />
          </div>

          <div className="flex flex-col flex-1 max-w-lg">
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={tutorial.appName}
                onChange={(e) => onAppNameChange(e.target.value)}
                placeholder="App (ej. Tobo4)"
                className="bg-blue-600/20 border border-blue-500/30 text-blue-400 text-[11px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md w-24 focus:outline-none focus:border-blue-400"
              />
              <span className="text-xs text-slate-500 flex items-center gap-1">
                {isSaving ? (
                  <span className="text-amber-400">Guardando...</span>
                ) : (
                  <span className="text-emerald-400 flex items-center gap-1">
                    <Check className="w-3 h-3" /> Guardado
                  </span>
                )}
              </span>
            </div>

            <input
              type="text"
              value={tutorial.title}
              onChange={(e) => onTitleChange(e.target.value)}
              placeholder="Título del tutorial (ej. Registrar y Gestionar Objetos en Tobo4)"
              className="bg-transparent font-bold text-base text-slate-100 border-b border-transparent hover:border-slate-700 focus:border-blue-500 focus:outline-none transition py-0.5"
            />
          </div>
        </div>

        {/* Center: Main View Switcher (Editor vs Playbook Document) */}
        <div className="flex items-center bg-slate-950/80 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => onViewChange('editor')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              currentView === 'editor'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Modo Editor
          </button>
          <button
            onClick={() => onViewChange('playbook')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              currentView === 'playbook'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" /> Vista Playbook
          </button>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Test Audio Button */}
          <button
            type="button"
            onClick={() => playStandaloneCountdownPreview()}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800/90 hover:bg-slate-700 text-slate-200 hover:text-white rounded-lg text-xs font-semibold border border-slate-700 hover:border-blue-500/50 transition shadow-sm"
            title="Probar sonido de la cuenta regresiva (4, 3, 2, 1...)"
          >
            <Volume2 className="w-3.5 h-3.5 text-blue-400" />
            Probar audio
          </button>

          {/* Tutorials Menu Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium border border-slate-700 transition"
              title="Mis Tutoriales"
            >
              <FolderOpen className="w-3.5 h-3.5" />
              Tutoriales ({tutorialsList.length})
            </button>

            {showDropdown && (
              <div className="absolute right-0 mt-2 w-64 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl p-2 z-50">
                <button
                  onClick={() => {
                    onNewTutorial();
                    setShowDropdown(false);
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 rounded-lg text-xs font-semibold mb-2 transition"
                >
                  <Plus className="w-4 h-4" /> Crear nuevo tutorial
                </button>

                <div className="max-h-56 overflow-y-auto space-y-1">
                  {tutorialsList.map((tut) => (
                    <button
                      key={tut.id}
                      onClick={() => {
                        onSelectTutorial(tut.id);
                        setShowDropdown(false);
                      }}
                      className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs transition flex justify-between items-center ${
                        tut.id === tutorial.id
                          ? 'bg-blue-600 text-white font-semibold'
                          : 'text-slate-300 hover:bg-slate-800'
                      }`}
                    >
                      <span className="truncate flex-1">{tut.title}</span>
                      <span className="text-[10px] opacity-70 ml-2">{tut.stepsCount} pasos</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Video Player Modal Trigger */}
          <button
            onClick={onOpenFullVideo}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium border border-slate-700 transition shadow-sm"
          >
            <Play className="w-3.5 h-3.5 text-blue-400 fill-current" /> Ver Video
          </button>

          {/* Export HTML */}
          <button
            onClick={handleDownloadHtml}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shadow transition"
            title="Descarga la guía completa interactiva con videos y texto"
          >
            <FileText className="w-3.5 h-3.5" /> Descargar Guía HTML
          </button>

          {/* Export Video */}
          <button
            onClick={onOpenVideoExport}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow transition"
            title="Exportar archivo de video unificado"
          >
            <Video className="w-3.5 h-3.5" /> Compilar Video
          </button>
        </div>
      </div>
    </header>
  );
};
