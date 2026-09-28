export interface Step {
  id: string;
  title: string;
  description: string; // Transcripción o explicación del capítulo
  noteType: 'none' | 'info' | 'tip' | 'warning';
  noteText: string;
  image?: string; // Captura clave / fotograma del video
  video?: Blob | string; // Clip de video grabado (Blob nativo o Data URL / Blob URL)
  audio?: string; // Pista de audio opcional
  duration?: number; // Duración del clip en segundos
  clickX?: number; // Marcador opcional
  clickY?: number;
}

export interface Tutorial {
  id: string;
  title: string;
  description: string;
  author: string;
  appName: string;
  createdAt: number;
  updatedAt: number;
  steps: Step[];
}
