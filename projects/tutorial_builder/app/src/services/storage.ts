import { get, set, del, keys } from 'idb-keyval';
import type { Tutorial, Step } from '../types';

const TUTORIAL_PREFIX = 'tutorial_';
const ACTIVE_TUTORIAL_KEY = 'active_tutorial_id';

export function createEmptyStep(index: number): Step {
  return {
    id: `step_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
    title: `Paso ${index + 1}`,
    description: '',
    noteType: 'none',
    noteText: '',
  };
}

export function createNewTutorial(title = 'Nuevo Tutorial Tobo4'): Tutorial {
  const now = Date.now();
  const id = `tut_${now}`;
  return {
    id,
    title,
    description: 'Guía paso a paso generada con Tutorial Builder',
    author: 'Equipo Tobo4',
    appName: 'Tobo4',
    createdAt: now,
    updatedAt: now,
    steps: [createEmptyStep(0)],
  };
}

export async function listAllTutorials(): Promise<{ id: string; title: string; updatedAt: number; stepsCount: number }[]> {
  const allKeys = await keys();
  const tutKeys = allKeys.filter((k) => typeof k === 'string' && k.startsWith(TUTORIAL_PREFIX)) as string[];
  
  const results = [];
  for (const k of tutKeys) {
    const tut = (await get(k)) as Tutorial | undefined;
    if (tut) {
      results.push({
        id: tut.id,
        title: tut.title || 'Sin título',
        updatedAt: tut.updatedAt || tut.createdAt,
        stepsCount: tut.steps?.length || 0,
      });
    }
  }
  return results.sort((a, b) => b.updatedAt - a.updatedAt);
}

export async function loadTutorial(id: string): Promise<Tutorial | null> {
  const tut = (await get(`${TUTORIAL_PREFIX}${id}`)) as Tutorial | undefined;
  return tut || null;
}

export async function saveTutorial(tutorial: Tutorial): Promise<void> {
  const toSave = { ...tutorial, updatedAt: Date.now() };
  await set(`${TUTORIAL_PREFIX}${tutorial.id}`, toSave);
  await set(ACTIVE_TUTORIAL_KEY, tutorial.id);
}

export async function deleteTutorial(id: string): Promise<void> {
  await del(`${TUTORIAL_PREFIX}${id}`);
  const activeId = await get(ACTIVE_TUTORIAL_KEY);
  if (activeId === id) {
    await del(ACTIVE_TUTORIAL_KEY);
  }
}

export async function getActiveTutorialId(): Promise<string | null> {
  const activeId = (await get(ACTIVE_TUTORIAL_KEY)) as string | undefined;
  return activeId || null;
}
