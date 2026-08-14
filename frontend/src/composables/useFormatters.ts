export function useFormatters() {
  const formatDate = (
    dateInput?: string | Date | null,
    options: Intl.DateTimeFormatOptions = { day: '2-digit', month: '2-digit', year: 'numeric' }
  ): string => {
    if (!dateInput) return '-';
    try {
      const d = typeof dateInput === 'string' ? new Date(dateInput) : dateInput;
      if (isNaN(d.getTime())) return '-';
      return d.toLocaleDateString('fr-FR', options);
    } catch {
      return '-';
    }
  };

  const formatDateTime = (
    dateInput?: string | Date | null
  ): string => {
    if (!dateInput) return '-';
    try {
      const d = typeof dateInput === 'string' ? new Date(dateInput) : dateInput;
      if (isNaN(d.getTime())) return '-';
      return d.toLocaleDateString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return '-';
    }
  };

  const formatTime = (dateInput?: string | Date | null): string => {
    if (!dateInput) return '-';
    try {
      const d = typeof dateInput === 'string' ? new Date(dateInput) : dateInput;
      if (isNaN(d.getTime())) return '-';
      return d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '-';
    }
  };

  const formatYear = (dateInput?: string | Date | null): string => {
    if (!dateInput) return '-';
    try {
      const d = typeof dateInput === 'string' ? new Date(dateInput) : dateInput;
      if (isNaN(d.getTime())) return '-';
      return String(d.getFullYear());
    } catch {
      return '-';
    }
  };

  const formatMonthDay = (dateInput?: string | Date | null): string => {
    if (!dateInput) return '-';
    try {
      const d = typeof dateInput === 'string' ? new Date(dateInput) : dateInput;
      if (isNaN(d.getTime())) return '-';
      return d.toLocaleDateString('fr-FR', { month: '2-digit', day: '2-digit' });
    } catch {
      return '-';
    }
  };

  const formatPeriod = (dateInput?: string | Date | null): string => {
    if (!dateInput) return '';
    try {
      const d = typeof dateInput === 'string' ? new Date(dateInput) : dateInput;
      if (isNaN(d.getTime())) return '';
      const month = String(d.getMonth() + 1).padStart(2, '0');
      const year = String(d.getFullYear()).slice(2);
      return `${month}${year}`;
    } catch {
      return '';
    }
  };

  const formatCurrency = (
    amount?: number | string | null,
    currency = 'FCFA'
  ): string => {
    if (amount === undefined || amount === null || amount === '') return `0 ${currency}`;
    const num = typeof amount === 'string' ? parseFloat(amount) : amount;
    if (isNaN(num)) return `0 ${currency}`;
    return `${num.toLocaleString('fr-FR')} ${currency}`.trim();
  };

  const formatNumber = (
    value?: number | string | null,
    decimals = 0
  ): string => {
    if (value === undefined || value === null || value === '') return '0';
    const num = typeof value === 'string' ? parseFloat(value) : value;
    if (isNaN(num)) return '0';
    return num.toLocaleString('fr-FR', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    });
  };

  const formatFileSize = (bytes?: number | null): string => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const formatRelativeTime = (dateInput?: string | Date | null): string => {
    if (!dateInput) return '-';
    try {
      const d = typeof dateInput === 'string' ? new Date(dateInput) : dateInput;
      if (isNaN(d.getTime())) return '-';
      const now = new Date();
      const diffMs = now.getTime() - d.getTime();
      const diffSec = Math.floor(diffMs / 1000);
      const diffMin = Math.floor(diffSec / 60);
      const diffHours = Math.floor(diffMin / 60);
      const diffDays = Math.floor(diffHours / 24);

      if (diffSec < 60) return "À l'instant";
      if (diffMin < 60) return `Il y a ${diffMin} min`;
      if (diffHours < 24) return `Il y a ${diffHours} h`;
      if (diffDays === 1) return 'Hier';
      if (diffDays < 7) return `Il y a ${diffDays} jours`;
      return d.toLocaleDateString('fr-FR');
    } catch {
      return '-';
    }
  };

  return {
    formatDate,
    formatDateTime,
    formatTime,
    formatYear,
    formatMonthDay,
    formatPeriod,
    formatCurrency,
    formatNumber,
    formatFileSize,
    formatRelativeTime,
  };
}
