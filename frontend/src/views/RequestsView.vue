<template>
  <AppLayout>
    <div class="min-h-screen bg-[linear-gradient(180deg,_#fff_0%,_#fff8f9_100%)] px-6 py-8 lg:px-8">
      <section class="mx-auto max-w-7xl">
        <div class="overflow-hidden rounded-[30px] border border-red-100 bg-white shadow-[0_18px_50px_rgba(127,7,28,0.12)]">
          <div class="bg-gradient-to-r from-[#d10f2f] to-[#97091f] px-6 py-10 text-white sm:px-10">
            <div class="mx-auto max-w-4xl text-center">
              <p class="text-xs font-semibold uppercase tracking-[0.4em] text-white/80">
                Demandes internes
              </p>
              <h1 class="mt-4 text-3xl font-black tracking-tight sm:text-5xl">
                Bienvenue au portail de demandes internes
              </h1>
              <p class="mx-auto mt-4 max-w-2xl text-sm leading-6 text-white/85 sm:text-base">
                Choisissez une catégorie pour créer une nouvelle demande.
              </p>

            </div>
          </div>


          <div class="px-6 py-8 sm:px-10 sm:py-10">
            <div class="grid gap-6 md:grid-cols-3">
              <RouterLink
                v-for="section in requestSections"
                :key="section.key"
                :id="section.key"
                :to="{ name: 'request-form', params: { section: section.key } }"
                class="group rounded-3xl border border-gray-200 bg-white p-6 text-center shadow-[0_10px_30px_rgba(15,23,42,0.06)] transition duration-300 hover:-translate-y-1 hover:border-red-200 hover:shadow-[0_18px_40px_rgba(127,7,28,0.12)]"
              >
                <div class="mx-auto flex h-20 w-20 items-center justify-center rounded-full border border-red-100 bg-red-50 shadow-inner">
                  <span class="material-symbols-outlined text-[34px] text-red-600">{{ section.icon }}</span>
                </div>

                <h2 class="mt-5 text-xl font-black tracking-tight text-gray-950">
                  {{ section.title }}
                </h2>

                <p class="mt-3 min-h-16 text-sm leading-6 text-gray-500">
                  {{ section.description }}
                </p>

                <div class="mt-5 flex items-center justify-center gap-2">
                  <span class="rounded-full bg-red-600 px-3 py-1 text-xs font-bold text-white">
                    {{ section.requests.length }} requests
                  </span>
                  <span class="rounded-full border border-red-100 bg-white px-3 py-1 text-xs font-semibold text-red-700">
                    Open
                  </span>
                </div>

                <p class="mt-6 text-sm font-semibold text-red-700 transition group-hover:text-red-900">
                  Cliquer pour créer une demande →
                </p>
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
  key: 'hr' | 'it' | 'facilities';
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
    eyebrow: 'Section 01',
    title: 'HR',
    description: 'Demandes de congés, onboarding, contrat et informations collaborateur.',
    icon: 'groups',
    badgeClass: 'bg-gradient-to-br from-red-600 to-red-700 shadow-lg shadow-red-200',
    requests: []
  },
  {
    key: 'it',
    eyebrow: 'Section 02',
    title: 'IT',
    description: 'Tickets liés aux accès, équipements, bugs applicatifs et support utilisateur.',
    icon: 'memory',
    badgeClass: 'bg-gradient-to-br from-[#97091f] to-[#d10f2f] shadow-lg shadow-red-200',
    requests: []
  },
  {
    key: 'facilities',
    eyebrow: 'Section 03',
    title: 'Facilities',
    description: 'Maintenance, locaux, badge, salles de réunion et demandes logistiques.',
    icon: 'home_repair_service',
    badgeClass: 'bg-gradient-to-br from-gray-800 to-red-700 shadow-lg shadow-red-200',
    requests: []
  }
]);

onMounted(async () => {
  try {
    const res = await api.get('/requests/');
    const allRequests = res.data || [];
    
    // Distribute into categories
    const hr = allRequests.filter((r: any) => ['LEAVE', 'DOCUMENT'].includes(r.type));
    const it = allRequests.filter((r: any) => r.type && r.type.startsWith('IT_'));
    const facilities = allRequests.filter((r: any) => r.type && r.type.startsWith('FACILITY_'));
    
    requestSections.value[0]!.requests = hr;
    requestSections.value[1]!.requests = it;
    requestSections.value[2]!.requests = facilities;
  } catch (error) {
    console.error("Error fetching requests:", error);
  }
});
</script>