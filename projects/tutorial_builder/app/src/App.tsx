import React, { useState, useEffect, useRef } from 'react';
import type { Tutorial, Step } from './types';
import {
  createNewTutorial,
  createEmptyStep,
  loadTutorial,
  saveTutorial,
  listAllTutorials,
  getActiveTutorialId,
  deleteTutorial,
} from './services/storage';
import { Navbar } from './components/Navbar';
import { StepCard } from './components/StepCard';
import { PlaybookView } from './components/PlaybookView';
import { FullVideoPlayerModal } from './components/FullVideoPlayerModal';
import { VideoExportModal } from './components/VideoExportModal';
import { Plus, Info, Trash2 } from 'lucide-react';

export const App: React.FC = () => {
  const [tutorial, setTutorial] = useState<Tutorial | null>(null);
  const [tutorialsList, setTutorialsList] = useState<
    { id: string; title: string; updatedAt: number; stepsCount: number }[]
  >([]);
  const [isSaving, setIsSaving] = useState(false);
  const [currentView, setCurrentView] = useState<'editor' | 'playbook'>('editor');
  const [isFullVideoOpen, setIsFullVideoOpen] = useState(false);
  const [videoStartStep, setVideoStartStep] = useState(0);
  const [isVideoExportOpen, setIsVideoExportOpen] = useState(false);
  const saveTimeoutRef = useRef<number | null>(null);

  // Initial load
  useEffect(() => {
    async function init() {
      const list = await listAllTutorials();
      setTutorialsList(list);

      const activeId = await getActiveTutorialId();
      if (activeId) {
        const loaded = await loadTutorial(activeId);
        if (loaded) {
          setTutorial(loaded);
          return;
        }
      }

      if (list.length > 0) {
        const loaded = await loadTutorial(list[0].id);
        if (loaded) {
          setTutorial(loaded);
          return;
        }
      }

      // Default first tutorial matching Tobo4
      const fresh = createNewTutorial(
        'Registrar y Gestionar Objetos y Dispositivos en Plataforma'
      );
      fresh.description =
        'Este video muestra cómo registrar y administrar objetos en la plataforma para su seguimiento efectivo. Se explica el proceso de asignación de clientes, estados y dispositivos vinculados para garantizar un monitoreo seguro y fiable.';
      await saveTutorial(fresh);
      setTutorial(fresh);
      const updatedList = await listAllTutorials();
      setTutorialsList(updatedList);
    }
    init();
  }, []);

  // Autosave with debounce
  const handleTutorialChange = (updated: Tutorial) => {
    setTutorial(updated);
    setIsSaving(true);
    if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
    saveTimeoutRef.current = window.setTimeout(async () => {
      await saveTutorial(updated);
      setIsSaving(false);
      const list = await listAllTutorials();
      setTutorialsList(list);
    }, 400);
  };

  const handleStepUpdate = (index: number, updatedStep: Step) => {
    if (!tutorial) return;
    const newSteps = [...tutorial.steps];
    newSteps[index] = updatedStep;
    handleTutorialChange({ ...tutorial, steps: newSteps });
  };

  const handleAddStep = () => {
    if (!tutorial) return;
    const newStep = createEmptyStep(tutorial.steps.length);
    handleTutorialChange({ ...tutorial, steps: [...tutorial.steps, newStep] });
  };

  const handleDeleteStep = (index: number) => {
    if (!tutorial) return;
    if (tutorial.steps.length === 1) {
      alert('El tutorial debe tener al menos un capítulo.');
      return;
    }
    const newSteps = tutorial.steps.filter((_, i) => i !== index);
    handleTutorialChange({ ...tutorial, steps: newSteps });
  };

  const handleMoveStep = (fromIndex: number, toIndex: number) => {
    if (!tutorial) return;
    if (toIndex < 0 || toIndex >= tutorial.steps.length) return;
    const newSteps = [...tutorial.steps];
    const [moved] = newSteps.splice(fromIndex, 1);
    newSteps.splice(toIndex, 0, moved);
    handleTutorialChange({ ...tutorial, steps: newSteps });
  };

  const handleDuplicateStep = (index: number) => {
    if (!tutorial) return;
    const original = tutorial.steps[index];
    const duplicated: Step = {
      ...original,
      id: `step_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      title: `${original.title} (Copia)`,
    };
    const newSteps = [...tutorial.steps];
    newSteps.splice(index + 1, 0, duplicated);
    handleTutorialChange({ ...tutorial, steps: newSteps });
  };

  const handleNewTutorial = async () => {
    const title = prompt('Nombre del nuevo tutorial:', 'Nuevo Tutorial Tobo4');
    if (!title) return;
    const fresh = createNewTutorial(title);
    await saveTutorial(fresh);
    setTutorial(fresh);
    const list = await listAllTutorials();
    setTutorialsList(list);
    setCurrentView('editor');
  };

  const handleSelectTutorial = async (id: string) => {
    const loaded = await loadTutorial(id);
    if (loaded) setTutorial(loaded);
  };

  const handleDeleteCurrentTutorial = async () => {
    if (!tutorial) return;
    if (confirm(`¿Estás seguro de eliminar el tutorial "${tutorial.title}"?`)) {
      await deleteTutorial(tutorial.id);
      const list = await listAllTutorials();
      setTutorialsList(list);
      if (list.length > 0) {
        const next = await loadTutorial(list[0].id);
        setTutorial(next);
      } else {
        const fresh = createNewTutorial();
        await saveTutorial(fresh);
        setTutorial(fresh);
      }
    }
  };

  if (!tutorial) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">
        Cargando Tutorial Builder...
      </div>
    );
  }

  // If user selected Playbook view (Matching Guidde image 2)
  if (currentView === 'playbook') {
    return (
      <>
        <PlaybookView
          tutorial={tutorial}
          onBackToEditor={() => setCurrentView('editor')}
          onOpenFullVideo={(stepIdx = 0) => {
            setVideoStartStep(stepIdx);
            setIsFullVideoOpen(true);
          }}
        />

        <FullVideoPlayerModal
          tutorial={tutorial}
          isOpen={isFullVideoOpen}
          initialStepIndex={videoStartStep}
          onClose={() => setIsFullVideoOpen(false)}
          onSwitchToPlaybook={() => setIsFullVideoOpen(false)}
        />
      </>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar
        tutorial={tutorial}
        tutorialsList={tutorialsList}
        currentView={currentView}
        onViewChange={setCurrentView}
        isSaving={isSaving}
        onTitleChange={(title) => handleTutorialChange({ ...tutorial, title })}
        onAppNameChange={(appName) => handleTutorialChange({ ...tutorial, appName })}
        onNewTutorial={handleNewTutorial}
        onSelectTutorial={handleSelectTutorial}
        onOpenFullVideo={() => {
          setVideoStartStep(0);
          setIsFullVideoOpen(true);
        }}
        onOpenVideoExport={() => setIsVideoExportOpen(true)}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Banner with Tutorial Details */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="space-y-1 flex-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Descripción general del tutorial / Playbook
              </span>
            </div>
            <input
              type="text"
              value={tutorial.description}
              onChange={(e) =>
                handleTutorialChange({ ...tutorial, description: e.target.value })
              }
              placeholder="Describe de qué trata este tutorial..."
              className="w-full bg-slate-950/60 border border-slate-800 hover:border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-blue-500 transition"
            />
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <div className="text-xs text-slate-400">Total de Capítulos</div>
              <div className="text-lg font-bold text-blue-400">{tutorial.steps.length}</div>
            </div>

            <button
              onClick={handleDeleteCurrentTutorial}
              className="p-2 text-slate-500 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition"
              title="Eliminar este tutorial"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Tip Banner */}
        <div className="bg-blue-950/30 border border-blue-900/50 rounded-xl p-3.5 flex items-center gap-3 text-xs text-blue-300">
          <Info className="w-5 h-5 flex-shrink-0 text-blue-400" />
          <div>
            <strong>Flujo de trabajo:</strong> En cada capítulo puedes presionar{' '}
            <strong className="text-white">"Grabar Pestaña y Voz"</strong> para capturar Tobo4 y hablar por el micrófono. El texto se transcribirá automáticamente en la caja de la derecha. Si te equivocas en un capítulo, das clic en{' '}
            <strong className="text-sky-300">"Regrabar clip"</strong> y solo repites esos segundos.
          </div>
        </div>

        {/* Chapters List */}
        <div className="space-y-5">
          {tutorial.steps.map((step, idx) => (
            <StepCard
              key={step.id}
              step={step}
              index={idx}
              totalSteps={tutorial.steps.length}
              onUpdate={(updated) => handleStepUpdate(idx, updated)}
              onDelete={() => handleDeleteStep(idx)}
              onMoveUp={() => handleMoveStep(idx, idx - 1)}
              onMoveDown={() => handleMoveStep(idx, idx + 1)}
              onDuplicate={() => handleDuplicateStep(idx)}
            />
          ))}
        </div>

        {/* Add Step Button */}
        <div className="pt-2 pb-12 flex justify-center">
          <button
            onClick={handleAddStep}
            className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-semibold text-sm shadow-xl shadow-blue-600/20 hover:scale-105 transition active:scale-95"
          >
            <Plus className="w-5 h-5" /> Agregar Siguiente Capítulo
          </button>
        </div>
      </main>

      {/* Modals */}
      <FullVideoPlayerModal
        tutorial={tutorial}
        isOpen={isFullVideoOpen}
        initialStepIndex={videoStartStep}
        onClose={() => setIsFullVideoOpen(false)}
        onSwitchToPlaybook={() => {
          setIsFullVideoOpen(false);
          setCurrentView('playbook');
        }}
      />

      <VideoExportModal
        tutorial={tutorial}
        isOpen={isVideoExportOpen}
        onClose={() => setIsVideoExportOpen(false)}
      />
    </div>
  );
};

export default App;
