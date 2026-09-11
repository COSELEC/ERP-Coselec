<template>
  <AppLayout>
    <div class="h-full bg-[linear-gradient(180deg,_#fff_0%,_#fff8f9_100%)] px-6 py-8 lg:px-8">
      <section class="mx-auto max-w-7xl">
        <div class="overflow-hidden rounded-[30px] border border-red-100 bg-white shadow-[0_18px_50px_rgba(127,7,28,0.12)]">
          <div class="bg-gradient-to-r from-[#d10f2f] to-[#97091f] px-6 py-3 sm:py-4 text-white sm:px-3 sm:px-4">
            <div class="mx-auto max-w-4xl text-center">
              <p class="text-xs font-semibold uppercase tracking-[0.4em] text-white/80">
                Demandes internes unifiées
              </p>
              <h1 class="mt-4 text-xl font-black tracking-tight sm:text-xl">
                Portail des demandes internes
              </h1>
              <p class="mx-auto mt-4 max-w-2xl text-sm leading-6 text-white/85 sm:text-base">
                Sélectionnez une catégorie pour créer une nouvelle demande ou accédez au suivi de toutes vos demandes.
              </p>
              <div class="mt-6 flex justify-center gap-4">
                <RouterLink 
                  to="/admin/requests"
                  class="inline-flex items-center gap-2 rounded-2xl bg-white/15 hover:bg-white/25 px-5 py-2.5 text-sm font-semibold text-white backdrop-blur-sm border border-white/20 transition"
                >
                  <span class="material-symbols-outlined text-lg">assignment</span>
                  Voir mes demandes
                </RouterLink>
                <RouterLink 
                  v-if="isAdminOrValidator"
                  to="/admin/requests"
                  class="inline-flex items-center gap-2 rounded-2xl bg-white/15 hover:bg-white/25 px-5 py-2.5 text-sm font-semibold text-white backdrop-blur-sm border border-white/20 transition"
                >
                  <span class="material-symbols-outlined text-lg">manage_accounts</span>
                  Toutes les demandes
                </RouterLink>
              </div>
            </div>
          </div>

          <div class="px-6 py-8 sm:px-3 sm:px-4 sm:py-3 sm:py-4">
            <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              <RouterLink
                v-for="section in requestSections"
                :key="section.key"
                :id="section.key"
                :to="{ name: 'request-form', params: { section: section.key } }"
                class="group rounded-3xl border border-gray-200 bg-white p-4 text-center shadow-[0_10px_30px_rgba(15,23,42,0.06)] transition duration-300 hover:-translate-y-1 hover:border-red-200 hover:shadow-[0_18px_40px_rgba(127,7,28,0.12)] flex flex-col justify-between"
              >
                <div>
                  <div class="mx-auto flex h-20 w-20 items-center justify-center rounded-full border border-red-100 bg-red-50 shadow-inner group-hover:scale-105 transition-transform duration-300">
                    <span class="material-symbols-outlined text-[34px] text-red-600">{{ section.icon }}</span>
                  </div>

                  <span class="inline-block mt-4 text-[11px] font-bold uppercase tracking-wider text-red-600/80">
                    {{ section.eyebrow }}
                  </span>

                  <h2 class="mt-1 text-xl font-black tracking-tight text-gray-950">
                    {{ section.title }}
                  </h2>

                  <p class="mt-3 text-sm leading-6 text-gray-500">
                    {{ section.description }}
                  </p>
                </div>

                <div class="mt-6 pt-4 border-t border-gray-100">
                  <div class="flex items-center justify-center gap-2">
                    <span class="rounded-full bg-red-600 px-3 py-1 text-xs font-bold text-white">
                      {{ section.requests.length }} demande{{ section.requests.length > 1 ? 's' : '' }}
                    </span>
                    <span class="rounded-full border border-red-100 bg-white px-3 py-1 text-xs font-semibold text-red-700">
                      Créer
                    </span>
                  </div>

                  <p class="mt-4 text-sm font-semibold text-red-700 transition group-hover:text-red-900">
                    Cliquer pour créer une demande →
                  </p>
                </div>
              </RouterLink>

              <!-- Carte Pièce de Caisse (visible uniquement pour ceux ayant la permission finance) -->
              <div
                v-if="canViewCaisse"
                id="caisse"
                @click="openCaisseModal"
                class="group rounded-3xl border border-gray-200 bg-white p-4 text-center shadow-[0_10px_30px_rgba(15,23,42,0.06)] transition duration-300 hover:-translate-y-1 hover:border-red-200 hover:shadow-[0_18px_40px_rgba(127,7,28,0.12)] flex flex-col justify-between cursor-pointer"
              >
                <div>
                  <div class="mx-auto flex h-20 w-20 items-center justify-center rounded-full border border-red-100 bg-red-50 shadow-inner group-hover:scale-105 transition-transform duration-300">
                    <span class="material-symbols-outlined text-[34px] text-red-600">receipt_long</span>
                  </div>

                  <span class="inline-block mt-4 text-[11px] font-bold uppercase tracking-wider text-red-600/80">
                    Trésorerie
                  </span>

                  <h2 class="mt-1 text-xl font-black tracking-tight text-gray-950">
                    Pièce de Caisse
                  </h2>

                  <p class="mt-3 text-sm leading-6 text-gray-500">
                    Créer et enregistrer une pièce de caisse avec les dépenses et recettes associées.
                  </p>
                </div>

                <div class="mt-6 pt-4 border-t border-gray-100">
                  <div class="flex items-center justify-center gap-2">
                    <span class="rounded-full bg-red-600 px-3 py-1 text-xs font-bold text-white">
                      {{ caisseHistoryCount }} pièce{{ caisseHistoryCount > 1 ? 's' : '' }}
                    </span>
                    <span class="rounded-full border border-red-100 bg-white px-3 py-1 text-xs font-semibold text-red-700">
                      Créer
                    </span>
                  </div>
                  <p class="mt-4 text-sm font-semibold text-red-700 transition group-hover:text-red-900">
                    Cliquer pour créer une pièce de caisse →
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>

    <!-- Modal Pièce de Caisse -->
    <div v-if="showCaisseModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[100] p-4">
      <div class="bg-white rounded-2xl w-full max-w-3xl overflow-hidden shadow-2xl max-h-[90vh] flex flex-col">
        <div class="px-6 py-4 bg-[#b30c27] text-white flex justify-between items-center flex-shrink-0">
          <h2 class="text-xl font-bold flex items-center gap-2">
            <span class="material-symbols-outlined">receipt_long</span>
            Nouvelle Pièce de Caisse
          </h2>
          <button @click="showCaisseModal = false" class="hover:bg-[#d10f2f] p-1 rounded-full transition">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>

        <div class="flex-1 overflow-y-auto p-6 space-y-6">
          <!-- En-tête de la pièce -->
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">DATE</label>
              <input v-model="caisseForm.date" type="date" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">NUM</label>
              <input v-model="caisseForm.num" type="text" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">N° AFFAIRE</label>
              <input v-model="caisseForm.affaire" type="text" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">N° CIA</label>
              <input v-model="caisseForm.cia" type="text" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
            </div>
            <div class="col-span-2 md:col-span-4">
              <label class="block text-sm font-medium text-gray-700 mb-1">MOYEN DE PAIEMENT</label>
              <select v-model="caisseForm.payment_method" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition">
                <option value="">Sélectionner</option>
                <option value="Transfert (Wave/Orange Money)">Transfert (Wave/Orange Money)</option>
                <option value="Liquide">Liquide</option>
                <option value="Chèque">Chèque</option>
                <option value="Carte Bancaire">Carte Bancaire</option>
              </select>
            </div>
          </div>

          <!-- Tableau Dépenses -->
          <div>
            <div class="flex justify-between items-center mb-3">
              <h3 class="text-base font-semibold text-gray-800">Dépenses</h3>
              <button @click="addCaisseDepense" class="text-sm text-red-600 font-medium hover:text-red-800 flex items-center gap-1">
                <span class="material-symbols-outlined text-sm">add</span> Ajouter
              </button>
            </div>
            <div class="overflow-x-auto rounded-xl border border-gray-200">
              <table class="w-full text-left text-sm">
                <thead class="bg-gray-50 text-gray-700 text-xs uppercase">
                  <tr>
                    <th class="px-3 py-2">N°</th>
                    <th class="px-3 py-2 w-2/5">Désignation</th>
                    <th class="px-3 py-2">Quantité</th>
                    <th class="px-3 py-2">Prix Unitaire</th>
                    <th class="px-3 py-2">Montant Total</th>
                    <th class="px-3 py-2 w-10"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, index) in caisseForm.depenses" :key="'dep-'+index" class="border-t border-gray-100">
                    <td class="px-3 py-1.5 text-gray-500 text-xs font-medium">{{ index + 1 }}</td>
                    <td class="px-3 py-1.5">
                      <textarea v-model="row.designation" rows="2" class="w-full px-2 py-1 border border-gray-200 rounded-lg text-sm resize-none" placeholder="Désignation..." style="word-break:break-word;white-space:pre-wrap;"></textarea>
                    </td>
                    <td class="px-3 py-1.5"><input v-model.number="row.quantite" type="number" min="0" class="w-20 px-2 py-1 border border-gray-200 rounded-lg text-sm" placeholder="1" /></td>
                    <td class="px-3 py-1.5"><input v-model.number="row.prix_unitaire" type="number" min="0" class="w-24 px-2 py-1 border border-gray-200 rounded-lg text-sm" placeholder="0 CFA" /></td>
                    <td class="px-3 py-1.5 font-semibold text-gray-900">{{ ((row.quantite || 0) * (row.prix_unitaire || 0)).toLocaleString('fr-FR') }} CFA</td>
                    <td class="px-3 py-1.5 text-right">
                      <button @click="removeCaisseDepense(index)" class="text-gray-400 hover:text-red-500"><span class="material-symbols-outlined text-lg">delete</span></button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Tableau Recettes -->
          <div>
            <div class="flex justify-between items-center mb-3">
              <h3 class="text-base font-semibold text-gray-800">Recettes</h3>
              <button @click="addCaisseRecette" class="text-sm text-red-600 font-medium hover:text-red-800 flex items-center gap-1">
                <span class="material-symbols-outlined text-sm">add</span> Ajouter
              </button>
            </div>
            <div class="overflow-x-auto rounded-xl border border-gray-200">
              <table class="w-full text-left text-sm">
                <thead class="bg-gray-50 text-gray-700 text-xs uppercase">
                  <tr>
                    <th class="px-3 py-2">N°</th>
                    <th class="px-3 py-2 w-2/5">Désignation</th>
                    <th class="px-3 py-2">Quantité</th>
                    <th class="px-3 py-2">Prix Unitaire</th>
                    <th class="px-3 py-2">Montant Total</th>
                    <th class="px-3 py-2 w-10"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, index) in caisseForm.recettes" :key="'rec-'+index" class="border-t border-gray-100">
                    <td class="px-3 py-1.5 text-gray-500 text-xs font-medium">{{ index + 1 }}</td>
                    <td class="px-3 py-1.5">
                      <textarea v-model="row.designation" rows="2" class="w-full px-2 py-1 border border-gray-200 rounded-lg text-sm resize-none" placeholder="Désignation..." style="word-break:break-word;white-space:pre-wrap;"></textarea>
                    </td>
                    <td class="px-3 py-1.5"><input v-model.number="row.quantite" type="number" min="0" class="w-20 px-2 py-1 border border-gray-200 rounded-lg text-sm" placeholder="1" /></td>
                    <td class="px-3 py-1.5"><input v-model.number="row.prix_unitaire" type="number" min="0" class="w-24 px-2 py-1 border border-gray-200 rounded-lg text-sm" placeholder="0 CFA" /></td>
                    <td class="px-3 py-1.5 font-semibold text-gray-900">{{ ((row.quantite || 0) * (row.prix_unitaire || 0)).toLocaleString('fr-FR') }} CFA</td>
                    <td class="px-3 py-1.5 text-right">
                      <button @click="removeCaisseRecette(index)" class="text-gray-400 hover:text-red-500"><span class="material-symbols-outlined text-lg">delete</span></button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div class="flex-shrink-0 px-6 py-4 border-t border-gray-100 flex justify-between items-center bg-gray-50">
          <RouterLink to="/caisse" class="text-sm text-[#b30c27] font-semibold hover:underline flex items-center gap-1">
            <span class="material-symbols-outlined text-base">history</span>
            Voir l'historique complet
          </RouterLink>
          <div class="flex gap-3">
            <button @click="showCaisseModal = false" class="px-6 py-2 text-gray-700 hover:bg-gray-100 rounded-xl transition">Annuler</button>
            <button @click="submitCaisse" :disabled="isSubmittingCaisse" class="px-6 py-2 bg-[#d10f2f] text-white hover:bg-[#97091f] rounded-xl shadow-lg transition flex items-center gap-2 disabled:opacity-50">
              <div v-if="isSubmittingCaisse" class="animate-spin rounded-full h-4 w-4 border-2 border-white/30 border-t-white"></div>
              <span class="material-symbols-outlined text-sm" v-else>download</span>
              {{ isSubmittingCaisse ? 'Génération...' : 'Générer & Enregistrer' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { RouterLink } from 'vue-router';
import AppLayout from '@/layouts/AppLayout.vue';
import api from '@/services/api';
import { getStoredProfile, hasPermission } from '@/services/session';
import { useToast } from '@/composables/useToast';

const toast = useToast();
const profile = getStoredProfile();
const permissions = profile?.permissions || [];

// Permissions
const isAdminOrValidator = computed(() => {
  return hasPermission(permissions, ['requests.validate_hr', 'requests.validate_it', 'requests.validate_facility', 'requests.validate_finance']);
});

const canViewCaisse = computed(() => {
  return hasPermission(permissions, ['requests.validate_finance']);
});

// ── Sections de demandes ──────────────────────────────────────────────────────
type RequestSection = {
  key: 'hr' | 'it' | 'facilities' | 'facilities-site' | 'fuel';
  eyebrow: string;
  title: string;
  description: string;
  icon: string;
  badgeClass: string;
  requests: any[];
};

const requestSections = ref<RequestSection[]>([
  {
    key: 'hr',
    eyebrow: 'Ressources Humaines',
    title: 'Demandes RH',
    description: 'Congés, absences, attestations, avances sur salaire et informations collaborateur.',
    icon: 'groups',
    badgeClass: 'bg-gradient-to-br from-red-600 to-red-700 shadow-lg shadow-red-200',
    requests: []
  },
  {
    key: 'it',
    eyebrow: 'Systèmes & Matériel',
    title: 'Tickets IT',
    description: 'Incidents techniques, matériel informatique, accès VPN, logiciels et support utilisateur.',
    icon: 'memory',
    badgeClass: 'bg-gradient-to-br from-[#97091f] to-[#d10f2f] shadow-lg shadow-red-200',
    requests: []
  },
  {
    key: 'facilities',
    eyebrow: 'Services Généraux & Bureau',
    title: 'Réparation & Matériel bureau',
    description: 'Maintenance des locaux, climatisation, plomberie, électricité et fournitures de bureau.',
    icon: 'home_repair_service',
    badgeClass: 'bg-gradient-to-br from-gray-800 to-red-700 shadow-lg shadow-red-200',
    requests: []
  },
  {
    key: 'facilities-site',
    eyebrow: 'Logistique Projet',
    title: 'Matériel de Chantier',
    description: 'Outillage spécialisé, équipements de protection (EPI), machines et fournitures pour un chantier.',
    icon: 'construction',
    badgeClass: 'bg-gradient-to-br from-amber-600 to-red-700 shadow-lg shadow-red-200',
    requests: []
  },
  {
    key: 'fuel',
    eyebrow: 'Flotte & Déplacements',
    title: 'Demande Carburant (DMCAR)',
    description: 'Bons de carburant pour véhicules de société, déplacements opérationnels et missions chantier.',
    icon: 'local_gas_station',
    badgeClass: 'bg-gradient-to-br from-red-600 to-amber-700 shadow-lg shadow-red-200',
    requests: []
  }
]);

// ── Pièce de caisse ────────────────────────────────────────────────────────────
const showCaisseModal = ref(false);
const isSubmittingCaisse = ref(false);
const caisseHistoryCount = ref(0);

const todayStr = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};

const caisseForm = ref({
  date: todayStr(),
  num: '',
  affaire: '',
  cia: '',
  payment_method: '',
  depenses: [{ designation: '', quantite: 1, prix_unitaire: 0 }],
  recettes: [{ designation: '', quantite: 1, prix_unitaire: 0 }]
});

const openCaisseModal = () => {
  caisseForm.value = {
    date: todayStr(),
    num: '',
    affaire: '',
    cia: '',
    payment_method: '',
    depenses: [{ designation: '', quantite: 1, prix_unitaire: 0 }],
    recettes: [{ designation: '', quantite: 1, prix_unitaire: 0 }]
  };
  showCaisseModal.value = true;
};

const addCaisseDepense = () => caisseForm.value.depenses.push({ designation: '', quantite: 1, prix_unitaire: 0 });
const removeCaisseDepense = (i: number) => caisseForm.value.depenses.splice(i, 1);
const addCaisseRecette = () => caisseForm.value.recettes.push({ designation: '', quantite: 1, prix_unitaire: 0 });
const removeCaisseRecette = (i: number) => caisseForm.value.recettes.splice(i, 1);

const submitCaisse = async () => {
  isSubmittingCaisse.value = true;
  try {
    // Transformer le nouveau format (qté x PU) vers le format attendu par le backend
    const payload = {
      ...caisseForm.value,
      depenses: caisseForm.value.depenses.map((r, idx) => ({
        date: caisseForm.value.date,
        designation: r.designation,
        montant: ((r.quantite || 0) * (r.prix_unitaire || 0)).toString(),
        quantite: r.quantite,
        prix_unitaire: r.prix_unitaire,
        num: String(idx + 1)
      })),
      recettes: caisseForm.value.recettes.map((r, idx) => ({
        date: caisseForm.value.date,
        designation: r.designation,
        montant: ((r.quantite || 0) * (r.prix_unitaire || 0)).toString(),
        quantite: r.quantite,
        prix_unitaire: r.prix_unitaire,
        num: String(idx + 1)
      }))
    };
    const res = await api.post('/caisse/generate', payload);
    toast.success('Pièce de caisse générée et enregistrée avec succès !');
    showCaisseModal.value = false;
    caisseHistoryCount.value++;
    if (res.data?.pdf_url) {
      window.open(res.data.pdf_url, '_blank');
    }
  } catch (e) {
    console.error('Erreur pièce de caisse', e);
    toast.error('Une erreur est survenue lors de la génération du PDF.');
  } finally {
    isSubmittingCaisse.value = false;
  }
};

// ── Requests count ─────────────────────────────────────────────────────────────
onMounted(async () => {
  try {
    const res = await api.get('/requests/');
    const allRequests = res.data || [];
    
    const hr = allRequests.filter((r: any) => ['LEAVE', 'DOCUMENT'].includes(r.type));
    const it = allRequests.filter((r: any) => r.type && r.type.startsWith('IT_'));
    const facilitiesRepair = allRequests.filter((r: any) => 
      r.type === 'FACILITY_MAINTENANCE' || (r.type === 'FACILITY_SUPPLIES' && !r.project_id) || r.type === 'FACILITY_BADGE'
    );
    const facilitiesSite = allRequests.filter((r: any) => 
      r.type === 'FACILITY_SUPPLIES' && !!r.project_id
    );
    const fuel = allRequests.filter((r: any) => r.type === 'FUEL');
    
    requestSections.value[0]!.requests = hr;
    requestSections.value[1]!.requests = it;
    requestSections.value[2]!.requests = facilitiesRepair;
    requestSections.value[3]!.requests = facilitiesSite;
    requestSections.value[4]!.requests = fuel;

    // Récupérer le nombre de pièces de caisse existantes
    if (canViewCaisse.value) {
      try {
        const caisseRes = await api.get('/caisse/');
        caisseHistoryCount.value = (caisseRes.data || []).length;
      } catch { /* silencieux */ }
    }
  } catch (error) {
    console.error("Error fetching requests:", error);
  }
});
</script>