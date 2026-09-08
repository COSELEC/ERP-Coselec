<template>
  <AppLayout>
    <div class="min-h-screen bg-[linear-gradient(180deg,_#fff_0%,_#fff8f9_100%)] px-6 py-8 lg:px-8">
      <section class="mx-auto max-w-7xl">
        <div class="overflow-hidden rounded-[30px] border border-red-100 bg-white shadow-[0_18px_50px_rgba(127,7,28,0.12)]">
          <div class="bg-gradient-to-r from-[#d10f2f] to-[#97091f] px-6 py-10 text-white sm:px-10">
            <div class="mx-auto max-w-4xl text-center">
              <p class="text-xs font-semibold uppercase tracking-[0.4em] text-white/80">
                Demandes internes unifiées
              </p>
              <h1 class="mt-4 text-3xl font-black tracking-tight sm:text-5xl">
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
                  Voir toutes les demandes
                </RouterLink>
              </div>
            </div>
          </div>

          <div class="px-6 py-8 sm:px-10 sm:py-10">
            <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              <RouterLink
                v-for="section in requestSections"
                :key="section.key"
                :id="section.key"
                :to="{ name: 'request-form', params: { section: section.key } }"
                class="group rounded-3xl border border-gray-200 bg-white p-6 text-center shadow-[0_10px_30px_rgba(15,23,42,0.06)] transition duration-300 hover:-translate-y-1 hover:border-red-200 hover:shadow-[0_18px_40px_rgba(127,7,28,0.12)] flex flex-col justify-between"
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
            </div>
          </div>
        </div>
      </section>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { RouterLink } from 'vue-router';
import AppLayout from '@/layouts/AppLayout.vue';
import api from '@/services/api';

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
  } catch (error) {
    console.error("Error fetching requests:", error);
  }
});
</script>