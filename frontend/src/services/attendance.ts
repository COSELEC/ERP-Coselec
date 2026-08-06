import api from './api'

export interface TimeclockRecord {
  id: number
  user_id: number
  date: string
  check_in: string | null
  check_out: string | null
  status: string
  notes?: string | null
}

export interface TimeclockHistoryItem {
  id: number
  user_id: number
  user_name: string
  date: string
  check_in: string | null
  check_out: string | null
  duration_minutes: number | null
}

export const attendanceService = {
  /** Récupère le pointage du jour pour l'utilisateur connecté */
  getToday(): Promise<{ data: TimeclockRecord | null }> {
    return api.get('/hr/timeclock/today')
  },

  /** Enregistre l'arrivée (check_in) */
  clockIn(): Promise<{ data: TimeclockRecord }> {
    return api.post('/hr/timeclock/checkin')
  },

  /** Enregistre la sortie (check_out) */
  clockOut(): Promise<{ data: TimeclockRecord }> {
    return api.post('/hr/timeclock/checkout')
  },

  /** Historique des pointages (Admin/RH) */
  getHistory(days = 30): Promise<{ data: TimeclockHistoryItem[] }> {
    return api.get('/hr/timeclock/history', { params: { days } })
  },

  /** Pointages de tous les employés pour aujourd'hui (Admin/RH) */
  getTodayAll(): Promise<{ data: TimeclockHistoryItem[] }> {
    return api.get('/hr/timeclock/today-all')
  }
}
