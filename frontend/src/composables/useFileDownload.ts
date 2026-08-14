export function useFileDownload() {
  const downloadUrl = (url: string, filename?: string) => {
    if (!url) return;
    const link = document.createElement('a');
    link.href = url;
    if (filename) link.download = filename;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const downloadBlob = (blob: Blob, filename: string) => {
    const objectUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(objectUrl);
  };

  const openPdf = (url?: string | null) => {
    if (!url) return;
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  return {
    downloadUrl,
    downloadBlob,
    openPdf,
  };
}
