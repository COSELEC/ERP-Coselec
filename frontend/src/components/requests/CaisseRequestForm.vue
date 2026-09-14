<template>
  <form @submit.prevent="submitCaisseRequest" class="space-y-8">
    <!-- Header Banner -->
    <div class="rounded-2xl border border-red-100 bg-red-50/40 p-4">
      <div class="flex items-center gap-3">
        <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-red-600 text-white shadow-md shadow-red-200">
          <span class="material-symbols-outlined text-2xl">receipt_long</span>
        </div>
        <div>
          <h3 class="text-base font-bold text-gray-900">Demande de Pièce de Caisse</h3>
          <p class="text-xs text-gray-500">Renseignez les informations de la pièce, détaillez les dépenses et recettes pour validation et génération du bon officiel.</p>
        </div>
      </div>
    </div>

    <!-- General Info Grid -->
    <div class="rounded-2xl border border-gray-100 bg-white p-5 shadow-xs space-y-4">
      <h4 class="text-sm font-bold uppercase tracking-wider text-gray-700 flex items-center gap-2">
        <span class="material-symbols-outlined text-red-600 text-lg">info</span>
        Informations Générales
      </h4>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div>
          <label class="mb-1.5 block text-xs font-semibold text-gray-700">Date *</label>
          <input 
            type="date" 
            v-model="form.date" 
            required 
            class="w-full rounded-2xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:bg-white focus:ring-4 focus:ring-red-100" 
          />
        </div>

        <div>
          <label class="mb-1.5 block text-xs font-semibold text-gray-700">N° de Pièce (Optionnel)</label>
          <input 
            type="text" 
            v-model="form.num" 
            placeholder="Ex: PC-042" 
            class="w-full rounded-2xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:bg-white focus:ring-4 focus:ring-red-100" 
          />
        </div>

        <div>
          <label class="mb-1.5 block text-xs font-semibold text-gray-700">Projet / Affaire</label>
          <select 
            v-model="selectedProjectId" 
            @change="onProjectChange"
            class="w-full rounded-2xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:bg-white focus:ring-4 focus:ring-red-100"
          >
            <option :value="null">-- Saisie manuelle ou hors projet --</option>
            <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name || p.code || 'Projet #' + p.id }}</option>
          </select>
        </div>

        <div>
          <label class="mb-1.5 block text-xs font-semibold text-gray-700">N° Affaire</label>
          <input 
            type="text" 
            v-model="form.affaire" 
            placeholder="Ex: AFF-2026-08" 
            class="w-full rounded-2xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:bg-white focus:ring-4 focus:ring-red-100" 
          />
        </div>

        <div>
          <label class="mb-1.5 block text-xs font-semibold text-gray-700">N° CIA</label>
          <input 
            type="text" 
            v-model="form.cia" 
            placeholder="Ex: CIA-104" 
            class="w-full rounded-2xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:bg-white focus:ring-4 focus:ring-red-100" 
          />
        </div>

        <div class="sm:col-span-2 lg:col-span-3">
          <label class="mb-1.5 block text-xs font-semibold text-gray-700">Moyen de Paiement *</label>
          <select 
            v-model="form.payment_method" 
            required
            class="w-full rounded-2xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:bg-white focus:ring-4 focus:ring-red-100 font-medium"
          >
            <option value="">Sélectionner un moyen de paiement</option>
            <option value="Liquide">Liquide (Espèces)</option>
            <option value="Transfert (Wave/Orange Money)">Transfert (Wave / Orange Money)</option>
            <option value="Chèque">Chèque</option>
            <option value="Carte Bancaire">Carte Bancaire</option>
          </select>
        </div>

        <div class="sm:col-span-2 lg:col-span-4">
          <label class="mb-1.5 block text-xs font-semibold text-gray-700">Motif général de la demande *</label>
          <input 
            type="text" 
            v-model="form.motif" 
            required 
            placeholder="Ex: Achat fournitures chantier / Remboursement frais mission..." 
            class="w-full rounded-2xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 outline-none transition focus:border-red-400 focus:bg-white focus:ring-4 focus:ring-red-100" 
          />
        </div>
      </div>
    </div>

    <!-- Section Dépenses -->
    <div class="rounded-2xl border border-gray-100 bg-white p-5 shadow-xs space-y-4">
      <div class="flex items-center justify-between">
        <h4 class="text-sm font-bold uppercase tracking-wider text-gray-800 flex items-center gap-2">
          <span class="material-symbols-outlined text-red-600 text-lg">arrow_downward</span>
          Dépenses
        </h4>
        <button 
          type="button" 
          @click="addDepense" 
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-red-50 text-red-700 hover:bg-red-100 text-xs font-bold transition"
        >
          <span class="material-symbols-outlined text-sm">add</span>
          Ajouter une dépense
        </button>
      </div>

      <div class="overflow-x-auto rounded-xl border border-gray-100">
        <table class="w-full text-left text-sm">
          <thead class="bg-gray-50 text-gray-600 text-[11px] uppercase font-bold">
            <tr>
              <th class="px-3 py-2 w-10 text-center">N°</th>
              <th class="px-3 py-2">Désignation</th>
              <th class="px-3 py-2 w-24">Quantité</th>
              <th class="px-3 py-2 w-32">Prix Unit. (CFA)</th>
              <th class="px-3 py-2 w-36">Montant Total</th>
              <th class="px-3 py-2 w-12 text-center"></th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="(row, index) in form.depenses" :key="'dep-' + index" class="hover:bg-gray-50/50 transition">
              <td class="px-3 py-2 text-center text-xs font-bold text-gray-400">{{ index + 1 }}</td>
              <td class="px-3 py-2">
                <input 
                  type="text" 
                  v-model="row.designation" 
                  placeholder="Désignation de la dépense..." 
                  required
                  class="w-full rounded-xl border border-gray-200 bg-white px-3 py-1.5 text-xs text-gray-800 outline-none focus:border-red-400 focus:ring-2 focus:ring-red-100" 
                />
              </td>
              <td class="px-3 py-2">
                <input 
                  type="number" 
                  min="1" 
                  v-model.number="row.quantite" 
                  required 
                  class="w-full rounded-xl border border-gray-200 bg-white px-3 py-1.5 text-xs text-gray-800 outline-none focus:border-red-400 focus:ring-2 focus:ring-red-100" 
                />
              </td>
              <td class="px-3 py-2">
                <input 
                  type="number" 
                  min="0" 
                  step="1"
                  v-model.number="row.prix_unitaire" 
                  required 
                  class="w-full rounded-xl border border-gray-200 bg-white px-3 py-1.5 text-xs text-gray-800 outline-none focus:border-red-400 focus:ring-2 focus:ring-red-100 font-medium" 
                />
              </td>
              <td class="px-3 py-2 font-bold text-xs text-gray-900 whitespace-nowrap">
                {{ ((row.quantite || 0) * (row.prix_unitaire || 0)).toLocaleString('fr-FR') }} CFA
              </td>
              <td class="px-3 py-2 text-center">
                <button 
                  type="button" 
                  @click="removeDepense(index)" 
                  class="p-1 text-gray-400 hover:text-red-600 rounded-lg transition"
                  title="Supprimer la ligne"
                >
                  <span class="material-symbols-outlined text-lg">delete</span>
                </button>
              </td>
            </tr>
            <tr v-if="form.depenses.length === 0">
              <td colspan="6" class="px-4 py-4 text-center text-xs text-gray-400 italic">
                Aucune dépense ajoutée. Cliquez sur "Ajouter une dépense" si nécessaire.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Section Recettes -->
    <div class="rounded-2xl border border-gray-100 bg-white p-5 shadow-xs space-y-4">
      <div class="flex items-center justify-between">
        <h4 class="text-sm font-bold uppercase tracking-wider text-gray-800 flex items-center gap-2">
          <span class="material-symbols-outlined text-emerald-600 text-lg">arrow_upward</span>
          Recettes (Optionnel)
        </h4>
        <button 
          type="button" 
          @click="addRecette" 
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-50 text-emerald-700 hover:bg-emerald-100 text-xs font-bold transition"
        >
          <span class="material-symbols-outlined text-sm">add</span>
          Ajouter une recette
        </button>
      </div>

      <div class="overflow-x-auto rounded-xl border border-gray-100">
        <table class="w-full text-left text-sm">
          <thead class="bg-gray-50 text-gray-600 text-[11px] uppercase font-bold">
            <tr>
              <th class="px-3 py-2 w-10 text-center">N°</th>
              <th class="px-3 py-2">Désignation</th>
              <th class="px-3 py-2 w-24">Quantité</th>
              <th class="px-3 py-2 w-32">Prix Unit. (CFA)</th>
              <th class="px-3 py-2 w-36">Montant Total</th>
              <th class="px-3 py-2 w-12 text-center"></th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="(row, index) in form.recettes" :key="'rec-' + index" class="hover:bg-gray-50/50 transition">
              <td class="px-3 py-2 text-center text-xs font-bold text-gray-400">{{ index + 1 }}</td>
              <td class="px-3 py-2">
                <input 
                  type="text" 
                  v-model="row.designation" 
                  placeholder="Désignation de la recette..." 
                  class="w-full rounded-xl border border-gray-200 bg-white px-3 py-1.5 text-xs text-gray-800 outline-none focus:border-red-400 focus:ring-2 focus:ring-red-100" 
                />
              </td>
              <td class="px-3 py-2">
                <input 
                  type="number" 
                  min="1" 
                  v-model.number="row.quantite" 
                  class="w-full rounded-xl border border-gray-200 bg-white px-3 py-1.5 text-xs text-gray-800 outline-none focus:border-red-400 focus:ring-2 focus:ring-red-100" 
                />
              </td>
              <td class="px-3 py-2">
                <input 
                  type="number" 
                  min="0" 
                  step="1"
                  v-model.number="row.prix_unitaire" 
                  class="w-full rounded-xl border border-gray-200 bg-white px-3 py-1.5 text-xs text-gray-800 outline-none focus:border-red-400 focus:ring-2 focus:ring-red-100 font-medium" 
                />
              </td>
              <td class="px-3 py-2 font-bold text-xs text-gray-900 whitespace-nowrap">
                {{ ((row.quantite || 0) * (row.prix_unitaire || 0)).toLocaleString('fr-FR') }} CFA
              </td>
              <td class="px-3 py-2 text-center">
                <button 
                  type="button" 
                  @click="removeRecette(index)" 
                  class="p-1 text-gray-400 hover:text-red-600 rounded-lg transition"
                  title="Supprimer la ligne"
                >
                  <span class="material-symbols-outlined text-lg">delete</span>
                </button>
              </td>
            </tr>
            <tr v-if="form.recettes.length === 0">
              <td colspan="6" class="px-4 py-4 text-center text-xs text-gray-400 italic">
                Aucune recette ajoutée.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Live Financial Summary Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div class="rounded-2xl border border-red-100 bg-red-50/50 p-4">
        <div class="text-xs font-semibold text-red-700 uppercase tracking-wider">Total Dépenses</div>
        <div class="mt-1 text-xl font-black text-red-900">{{ totalDepenses.toLocaleString('fr-FR') }} CFA</div>
      </div>
      <div class="rounded-2xl border border-emerald-100 bg-emerald-50/50 p-4">
        <div class="text-xs font-semibold text-emerald-700 uppercase tracking-wider">Total Recettes</div>
        <div class="mt-1 text-xl font-black text-emerald-900">{{ totalRecettes.toLocaleString('fr-FR') }} CFA</div>
      </div>
      <div class="rounded-2xl border border-gray-100 bg-gray-50/80 p-4">
        <div class="text-xs font-semibold text-gray-600 uppercase tracking-wider">Solde Net</div>
        <div class="mt-1 text-xl font-black" :class="soldeNet >= 0 ? 'text-gray-900' : 'text-red-700'">
          {{ soldeNet.toLocaleString('fr-FR') }} CFA
        </div>
      </div>
    </div>

    <!-- Justificatifs / Pièces jointes -->
    <div class="rounded-2xl border border-gray-100 bg-white p-5 shadow-xs space-y-3">
      <h4 class="text-sm font-bold uppercase tracking-wider text-gray-700 flex items-center gap-2">
        <span class="material-symbols-outlined text-red-600 text-lg">attach_file</span>
        Pièces Justificatives (Reçus, Factures, Scan de bon)
      </h4>
      <p class="text-xs text-gray-500">Joignez vos factures ou reçus justificatifs (PDF, JPG, PNG).</p>
      
      <div class="flex items-center gap-4">
        <label class="cursor-pointer inline-flex items-center gap-2 rounded-xl bg-gray-100 hover:bg-gray-200 px-4 py-2.5 text-xs font-bold text-gray-700 transition">
          <span class="material-symbols-outlined text-base">upload_file</span>
          <span>{{ selectedFile ? selectedFile.name : 'Choisir un fichier justificatif' }}</span>
          <input 
            type="file" 
            @change="handleFileUpload" 
            accept=".pdf,.doc,.docx,.jpg,.jpeg,.png" 
            class="hidden" 
          />
        </label>
        <button 
          v-if="selectedFile" 
          type="button" 
          @click="selectedFile = null" 
          class="text-xs text-red-600 hover:underline"
        >
          Supprimer le fichier
        </button>
      </div>
    </div>

    <!-- Form Actions -->
    <div class="flex flex-wrap items-center gap-3 pt-4 border-t border-gray-100">
      <button 
        type="submit" 
        :disabled="isSubmitting"
        class="inline-flex items-center gap-2 rounded-2xl bg-red-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-red-200 transition hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <span v-if="isSubmitting" class="animate-spin material-symbols-outlined text-[18px]">sync</span>
        <span v-else class="material-symbols-outlined text-[18px]">send</span>
        {{ isSubmitting ? "Envoi en cours..." : "Envoyer la demande de pièce de caisse" }}
      </button>

      <button 
        type="button" 
        @click="resetForm"
        class="inline-flex items-center gap-2 rounded-2xl border border-red-100 bg-white px-5 py-3 text-sm font-semibold text-red-700 transition hover:bg-red-50"
      >
        Réinitialiser
      </button>
    </div>
  </form>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/services/api';
import { useToast } from '@/composables/useToast';

const emit = defineEmits(['submitted']);
const router = useRouter();
const toast = useToast();

const isSubmitting = ref(false);
const projects = ref<any[]>([]);
const selectedProjectId = ref<number | null>(null);
const selectedFile = ref<File | null>(null);

const todayStr = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};

interface CaisseLine {
  designation: string;
  quantite: number;
  prix_unitaire: number;
}

const getInitialForm = () => ({
  date: todayStr(),
  num: '',
  affaire: '',
  cia: '',
  payment_method: '',
  motif: '',
  depenses: [
    { designation: '', quantite: 1, prix_unitaire: 0 }
  ] as CaisseLine[],
  recettes: [] as CaisseLine[]
});

const form = reactive(getInitialForm());

const totalDepenses = computed(() => {
  return form.depenses.reduce((sum, item) => sum + ((Number(item.quantite) || 0) * (Number(item.prix_unitaire) || 0)), 0);
});

const totalRecettes = computed(() => {
  return form.recettes.reduce((sum, item) => sum + ((Number(item.quantite) || 0) * (Number(item.prix_unitaire) || 0)), 0);
});

const soldeNet = computed(() => {
  return totalRecettes.value - totalDepenses.value;
});

const addDepense = () => {
  form.depenses.push({ designation: '', quantite: 1, prix_unitaire: 0 });
};

const removeDepense = (index: number) => {
  form.depenses.splice(index, 1);
};

const addRecette = () => {
  form.recettes.push({ designation: '', quantite: 1, prix_unitaire: 0 });
};

const removeRecette = (index: number) => {
  form.recettes.splice(index, 1);
};

const onProjectChange = () => {
  if (selectedProjectId.value) {
    const proj = projects.value.find(p => p.id === selectedProjectId.value);
    if (proj) {
      form.affaire = proj.code || proj.name || `PROJ-${proj.id}`;
    }
  }
};

const handleFileUpload = (e: Event) => {
  const target = e.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0] || null;
  }
};

const resetForm = () => {
  Object.assign(form, getInitialForm());
  selectedProjectId.value = null;
  selectedFile.value = null;
};

onMounted(async () => {
  try {
    const res = await api.get('/projects/');
    projects.value = res.data || [];
  } catch (err) {
    console.error('Erreur chargement projets', err);
  }
});

const submitCaisseRequest = async () => {
  if (isSubmitting.value) return;

  if (form.depenses.length === 0 && form.recettes.length === 0) {
    toast.error('Veuillez ajouter au moins une ligne de dépense ou de recette.');
    return;
  }

  isSubmitting.value = true;

  try {
    const payload = {
      type: 'PIECE_CAISSE',
      project_id: selectedProjectId.value || null,
      description: form.motif || `Pièce de caisse ${form.num || form.affaire || ''}`.trim(),
      payload: {
        type: 'PIECE_CAISSE',
        date: form.date,
        num: form.num,
        affaire: form.affaire,
        cia: form.cia,
        payment_method: form.payment_method,
        subject: form.motif,
        description: form.motif,
        depenses: form.depenses.map((d, idx) => ({
          date: form.date,
          designation: d.designation,
          quantite: Number(d.quantite) || 1,
          prix_unitaire: Number(d.prix_unitaire) || 0,
          montant: String((Number(d.quantite) || 1) * (Number(d.prix_unitaire) || 0)),
          num: String(idx + 1)
        })),
        recettes: form.recettes.map((r, idx) => ({
          date: form.date,
          designation: r.designation,
          quantite: Number(r.quantite) || 1,
          prix_unitaire: Number(r.prix_unitaire) || 0,
          montant: String((Number(r.quantite) || 1) * (Number(r.prix_unitaire) || 0)),
          num: String(idx + 1)
        })),
        total_depenses: totalDepenses.value,
        total_recettes: totalRecettes.value,
        solde_net: soldeNet.value
      }
    };

    const res = await api.post('/requests/', payload);
    const createdReq = res.data;

    // Si justificatif sélectionné, téléversement
    if (selectedFile.value && createdReq?.id) {
      try {
        const formData = new FormData();
        formData.append('file', selectedFile.value);
        await api.post(`/requests/${createdReq.id}/attachment`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
      } catch (attErr) {
        console.error('Erreur upload justificatif', attErr);
        toast.warning('Demande créée mais échec lors de l’envoi de la pièce jointe.');
      }
    }

    toast.success('Demande de pièce de caisse créée avec succès !');
    resetForm();
    emit('submitted');
    router.push('/admin/requests?category=caisse');
  } catch (error: any) {
    console.error('Erreur création pièce de caisse', error);
    toast.error(error.response?.data?.detail || 'Impossible de créer la demande de pièce de caisse.');
  } finally {
    isSubmitting.value = false;
  }
};
</script>
