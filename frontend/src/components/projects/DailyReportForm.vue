<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50" v-if="isOpen">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 overflow-hidden">
      <div class="flex justify-between items-center p-6 border-b border-gray-100">
        <h3 class="text-xl font-semibold text-gray-800">Nouveau Rapport Journalier</h3>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 transition-colors">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>

      <div class="p-6">
        <form @submit.prevent="handleSubmit" class="space-y-6">
          <div class="grid grid-cols-2 gap-6">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Projet</label>
              <select v-model="form.project_id" required class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-colors bg-white">
                <option value="">Sélectionner un projet</option>
                <option v-for="p in myProjects" :key="p.id" :value="p.id">
                  {{ p.nom }}
                </option>
              </select>
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Date du rapport</label>
              <input type="date" v-model="form.report_date" required class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-colors bg-white">
            </div>
          </div>

          <div class="grid grid-cols-2 gap-6">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Heures travaillées</label>
              <input type="number" step="0.5" v-model="form.hours_worked" required placeholder="ex: 8" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-colors">
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Avancement estimé (%)</label>
              <input type="number" min="0" max="100" v-model="form.progress_percentage" placeholder="ex: 50" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-colors">
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Tâches terminées aujourd'hui</label>
            <textarea v-model="form.tasks_completed" required rows="3" placeholder="- Tâche 1&#10;- Tâche 2" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-colors"></textarea>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Problèmes rencontrés (Optionnel)</label>
            <textarea v-model="form.issues_encountered" rows="2" placeholder="Décrivez les blocages ou problèmes" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-colors"></textarea>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Plan pour demain (Optionnel)</label>
            <textarea v-model="form.plan_for_tomorrow" rows="2" placeholder="Ce qui est prévu pour le prochain jour travaillé" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-colors"></textarea>
          </div>

          <div class="flex justify-end space-x-4 pt-4 border-t border-gray-100">
            <button type="button" @click="$emit('close')" class="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium">
              Annuler
            </button>
            <button type="submit" :disabled="loading" class="px-6 py-2 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-lg hover:from-red-700 hover:to-red-800 transition-all font-medium flex items-center justify-center min-w-[120px] shadow-md shadow-red-500/30">
              <span v-if="loading" class="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
              <span v-else>Soumettre</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useToast } from '@/composables/useToast';
import { dailyReportsService, type DailyReportCreate } from '@/services/daily_reports';
import { api } from '@/services/api';

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  }
});

const emit = defineEmits(['close', 'report-submitted']);
const toast = useToast();
const loading = ref(false);
const myProjects = ref<any[]>([]);

const form = ref<DailyReportCreate>({
  project_id: '' as any,
  report_date: new Date().toISOString().split('T')[0],
  hours_worked: '' as any,
  progress_percentage: '' as any,
  tasks_completed: '',
  issues_encountered: '',
  plan_for_tomorrow: ''
});

onMounted(async () => {
  try {
    // We fetch assignments for the current user
    // Since we don't have a specific endpoint for "my assignments", 
    // we fetch projects and maybe we just list them. 
    // For simplicity, let's fetch all active projects the user has access to.
    const res = await api.get('/projects');
    myProjects.value = res.data.filter((p: any) => !['Terminé', 'Clôturé', 'Annulé'].includes(p.status));
  } catch (e) {
    console.error("Error fetching projects", e);
  }
});

async function handleSubmit() {
  try {
    loading.value = true;
    
    const payload = { ...form.value };
    if (!payload.progress_percentage) delete payload.progress_percentage;
    
    await dailyReportsService.submitReport(payload as any);
    
    toast.success("Rapport journalier soumis avec succès !");
    
    // Reset form
    form.value = {
      project_id: '' as any,
      report_date: new Date().toISOString().split('T')[0],
      hours_worked: '' as any,
      progress_percentage: '' as any,
      tasks_completed: '',
      issues_encountered: '',
      plan_for_tomorrow: ''
    };
    
    emit('report-submitted');
    emit('close');
  } catch (error: any) {
    console.error("Erreur soumission rapport", error);
    toast.error(error.response?.data?.detail || "Erreur lors de la soumission du rapport.");
  } finally {
    loading.value = false;
  }
}
</script>
