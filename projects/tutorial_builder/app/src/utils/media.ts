const urlCache = new WeakMap<Blob, string>();
const stringUrlCache = new Map<string, string>();

export function toPlayableVideoUrl(video?: Blob | string): string {
  if (!video) return '';
  if (video instanceof Blob) {
    if (urlCache.has(video)) return urlCache.get(video)!;
    const url = URL.createObjectURL(video);
    urlCache.set(video, url);
    return url;
  }
  if (typeof video === 'string' && video.startsWith('data:video/')) {
    if (stringUrlCache.has(video)) return stringUrlCache.get(video)!;
    try {
      const parts = video.split(',');
      const mime = parts[0].match(/:(.*?);/)?.[1] || 'video/webm';
      const bstr = atob(parts[1]);
      const n = bstr.length;
      const u8arr = new Uint8Array(n);
      for (let i = 0; i < n; i++) {
        u8arr[i] = bstr.charCodeAt(i);
      }
      const blob = new Blob([u8arr], { type: mime });
      const url = URL.createObjectURL(blob);
      stringUrlCache.set(video, url);
      return url;
    } catch (e) {
      console.warn('Error convirtiendo data:video a blob URL:', e);
      return video;
    }
  }
  return video;
}
