export function useStatusBadges() {
  const getStatusBadgeClass = (statusInput?: string | null): string => {
    if (!statusInput) return 'bg-gray-100 text-gray-700 border-gray-200';
    const s = String(statusInput).toUpperCase().trim();

    // Validated / Approved / Done / Active / CDI
    if (['APPROVED', 'VALIDÉ', 'VALIDE', 'DONE', 'TERMINÉ', 'TERMINE', 'ACTIF', 'ACTIVE', 'CDI', 'RESOLVED', 'COMPLETED', 'PUBLISHED', 'CHANTIER'].includes(s)) {
      return 'bg-emerald-50 text-emerald-700 border border-emerald-200';
    }

    // Pending / Review / CDD / In Progress / Site
    if (['PENDING', 'EN ATTENTE', 'REVIEW', 'IN_REVIEW', 'REVUE', 'CDD', 'SITE', 'IN_PROGRESS', 'ISSUED'].includes(s)) {
      return 'bg-amber-50 text-amber-700 border border-amber-200';
    }

    // Rejected / Inactive / Cancelled / Urgent / Congé
    if (['REJECTED', 'REFUSÉ', 'REFUSE', 'INACTIF', 'INACTIVE', 'CANCELLED', 'ANNULÉ', 'ANNULE', 'URGENT', 'URGENTE', 'CONGE', 'CONGÉ'].includes(s)) {
      return 'bg-rose-50 text-rose-700 border border-rose-200';
    }

    // Intern / Stage / Prestataire
    if (['STAGIAIRE', 'STAGE', 'PRESTATAIRE', 'ON_HOLD'].includes(s)) {
      return 'bg-purple-50 text-purple-700 border border-purple-200';
    }

    // Draft / Archived / Default
    return 'bg-gray-50 text-gray-700 border border-gray-200';
  };

  const getStatusLabel = (statusInput?: string | null): string => {
    if (!statusInput) return '-';
    const s = String(statusInput).toUpperCase().trim();

    const labels: Record<string, string> = {
      APPROVED: 'Approuvé',
      PENDING: 'En attente',
      PENDING_MANAGER_APPROVAL: 'Attente Manager',
      PENDING_FINANCE_APPROVAL: 'Attente Finance',
      COMPROMISE_PENDING: 'Compromis en attente',
      IN_PROGRESS: 'En cours',
      COMPLETED: 'Terminé',
      REJECTED: 'Refusé',
      ON_HOLD: 'Suspendu',
      DRAFT: 'Brouillon',
      ISSUED: 'Émis',
      CANCELLED: 'Annulé',
      CDI: 'CDI',
      CDD: 'CDD',
      STAGIAIRE: 'Stagiaire',
      PRESTATAIRE: 'Prestataire',
      INACTIF: 'Inactif',
      CHANTIER: 'Sur Chantier',
      SITE: 'Au Siège',
      CONGE: 'En Congé',
      NONE: 'Non renseigné',
    };

    return labels[s] || statusInput;
  };

  const getPriorityBadgeClass = (priorityInput?: string | null): string => {
    if (!priorityInput) return 'bg-gray-100 text-gray-700';
    const p = String(priorityInput).toUpperCase().trim();

    if (['URGENT', 'URGENTE'].includes(p)) {
      return 'bg-rose-100 text-rose-800 font-bold';
    }
    if (['HIGH', 'HAUTE'].includes(p)) {
      return 'bg-orange-100 text-orange-800 font-semibold';
    }
    if (['MEDIUM', 'MOYENNE', 'NORMAL', 'NORMALE'].includes(p)) {
      return 'bg-blue-100 text-blue-800';
    }
    return 'bg-slate-100 text-slate-700';
  };

  return {
    getStatusBadgeClass,
    getStatusLabel,
    getPriorityBadgeClass,
  };
}
