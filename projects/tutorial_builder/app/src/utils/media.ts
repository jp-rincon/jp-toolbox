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
      const b64Idx = video.indexOf(';base64,');
      let b64 = '';
      let mime = 'video/webm';
      if (b64Idx !== -1) {
        b64 = video.substring(b64Idx + 8);
        const mimeMatch = video.substring(0, b64Idx).match(/^data:([^;]+)/);
        if (mimeMatch) mime = mimeMatch[1];
      } else {
        const commaIdx = video.lastIndexOf(',');
        b64 = commaIdx !== -1 ? video.substring(commaIdx + 1) : video;
      }

      const bstr = atob(b64);
      const len = bstr.length;
      const u8arr = new Uint8Array(len);
      for (let i = 0; i < len; i++) {
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
