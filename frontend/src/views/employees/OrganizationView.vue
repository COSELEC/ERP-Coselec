<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import AppLayout from '@/layouts/AppLayout.vue';
import { employeeService } from '@/services/employees';
import { api } from '@/services/api';
import { getStoredProfile, hasPermission } from '@/services/session';
import { useToast } from '@/composables/useToast';

const toast = useToast();
const profile = getStoredProfile();
const canAssign = hasPermission(profile?.permissions || [], ['employees.update']);

// ─── Structure figée de l'organigramme COSELEC ────────────────────────────────
interface OrgNode {
  key: string;
  title: string;
  highlight?: 'yellow' | 'red';
  children?: OrgNode[];
}

const COSELEC_ORG: OrgNode = {
  key: 'dg',
  title: 'DIRECTEUR GÉNÉRAL',
  children: [
    {
      key: 'dga',
      title: 'DIRECTEUR GÉNÉRAL ADJOINT',
      children: [
        { key: 'assistant_smqse', title: 'ASSISTANT SMQSE' },
        { key: 'responsable_smqse', title: 'RESPONSABLE SMQSE' },
        { key: 'responsable_it', title: 'RESPONSABLE SUPPORT IT' },
      ]
    },
    {
      key: 'assistante_direction',
      title: 'ASSISTANTE DE DIRECTION',
    },
    {
      key: 'directeur_finances',
      title: 'DIRECTEUR DES FINANCES ET CONTRÔLE',
      highlight: 'yellow',
      children: [
        { key: 'comptable_rh', title: 'COMPTABLE ET RESPONSABLE RH' },
        { key: 'comptable_tresorerie', title: 'COMPTABLE TRÉSORERIE' },
        { key: 'comptable_fournisseurs', title: 'COMPTABLE FOURNISSEURS CLIENTS' },
        { key: 'chargee_recouvrement', title: 'CHARGÉE DU RECOUVREMENT' },
      ]
    },
    {
      key: 'resp_commercial',
      title: 'RESPONSABLE PÔLE COMMERCIAL & APPRO',
      highlight: 'yellow',
      children: [
        { key: 'service_commercial', title: 'SERVICE COMMERCIAL' },
        { key: 'service_appro', title: 'SERVICE APPRO' },
        { key: 'service_logistique', title: 'SERVICE LOGISTIQUE' },
      ]
    },
    {
      key: 'directeur_technique',
      title: 'DIRECTEUR TECHNIQUE',
      highlight: 'yellow',
      children: [
        {
          key: 'chef_etudes',
          title: 'CHEF SERVICE ÉTUDES',
          children: [
            { key: 'techniciens_etudes', title: "TECHNICIENS BUREAU D'ÉTUDES" },
            { key: 'charge_projet', title: 'CHARGÉ DE PROJET' },
            { key: 'charge_suivi', title: 'CHARGÉ DU SUIVI ET DES PLANNINGS' },
          ]
        },
        {
          key: 'chef_travaux',
          title: 'CHEF SERVICE TRAVAUX',
          children: [
            { key: 'conducteurs_travaux', title: 'CONDUCTEURS DE TRAVAUX' },
            { key: 'chef_atelier', title: "CHEF D'ATELIER" },
            { key: 'chefs_chantier', title: 'CHEFS DE CHANTIER' },
          ]
        },
      ]
    },
  ]
};

// ─── Affectations ──────────────────────────────────────────────────────────────
const assignments = ref<Record<string, number | null>>({});
const employees = ref<any[]>([]);
const isLoading = ref(true);

// Modal
const showModal = ref(false);
const selectedNode = ref<OrgNode | null>(null);
const selectedEmployeeId = ref<number | null>(null);

const getEmployeeName = (posKey: string): string => {
  const empId = assignments.value[posKey];
  if (!empId) return '';
  const emp = employees.value.find(e => e.id === empId);
  if (!emp) return '';
  return `${emp.first_name || ''} ${emp.last_name || ''}`.trim();
};

const getEmployeePhoto = (posKey: string): string | null => {
  const empId = assignments.value[posKey];
  if (!empId) return null;
  const emp = employees.value.find(e => e.id === empId);
  return emp?.photo_url || null;
};

const openAssignModal = (node: OrgNode) => {
  if (!canAssign) return;
  selectedNode.value = node;
  selectedEmployeeId.value = assignments.value[node.key] || null;
  showModal.value = true;
};

const saveAssignment = async () => {
  if (!selectedNode.value) return;
  try {
    await api.post('/org-assignments', {
      position_key: selectedNode.value.key,
      employee_id: selectedEmployeeId.value
    });
    assignments.value[selectedNode.value.key] = selectedEmployeeId.value;
    showModal.value = false;
    toast.success('Affectation mise à jour.');
  } catch (e) {
    toast.error("Erreur lors de la sauvegarde de l'affectation.");
  }
};

onMounted(async () => {
  try {
    const [empRes, assignRes] = await Promise.all([
      employeeService.getAllEmployees(),
      api.get('/org-assignments').catch(() => ({ data: [] }))
    ]);
    employees.value = empRes.data || [];
    const asgList: any[] = assignRes.data || [];
    const map: Record<string, number | null> = {};
    asgList.forEach((a: any) => { map[a.position_key] = a.employee_id; });
    assignments.value = map;
  } catch (e) {
    console.error('Erreur chargement organigramme', e);
  } finally {
    isLoading.value = false;
  }
});
</script>

<template>
  <AppLayout>
    <div class="h-full w-full bg-gray-50 flex flex-col p-4 min-h-screen">

      <!-- Header -->
      <div class="flex justify-between items-center mb-6 bg-white p-4 rounded-xl shadow-sm border border-gray-100">
        <div>
          <h1 class="text-xl font-bold text-gray-800 flex items-center gap-2">
            <span class="material-symbols-outlined text-[#d10f2f]">account_tree</span>
            Organigramme COSELEC
          </h1>
          <p class="text-sm text-gray-500 mt-1">
            Structure officielle — 
            <span v-if="canAssign" class="text-[#d10f2f] font-medium">Cliquez sur un poste pour affecter un employé</span>
            <span v-else class="text-gray-400">Vue en lecture seule</span>
          </p>
        </div>
        <div class="flex gap-2 items-center text-xs text-gray-400">
          <span class="inline-block w-4 h-3 bg-yellow-200 border border-yellow-400 rounded"></span> Direction
          <span class="inline-block w-4 h-3 bg-gray-200 border border-gray-400 rounded ml-2"></span> Service
        </div>
      </div>

      <!-- Loading -->
      <div v-if="isLoading" class="flex-1 flex items-center justify-center">
        <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-red-600"></div>
      </div>

      <!-- Org Chart (scrollable) -->
      <div v-else class="flex-1 bg-white rounded-xl shadow-sm border border-gray-100 overflow-auto p-6">
        <div class="org-chart relative w-full overflow-auto h-[80vh] flex justify-center items-start pt-10">
<div class="relative w-[1900px] h-[1000px] shrink-0">
<!-- NODES -->
          <div class="absolute z-10 hover:z-20 transition-all duration-300" style="left: 660px; top: 15px; width: 180px;">
            <OrgCard :node="{ key: 'dg', title: 'DIRECTEUR GÉNÉRAL' }" :assignments="assignments" :get-employee-name="getEmployeeName" :get-employee-photo="getEmployeePhoto" :can-assign="canAssign" @click="openAssignModal({ key: 'dg', title: 'DIRECTEUR GÉNÉRAL' })" class="shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-t-4" :class="[{ key: 'dg', title: 'DIRECTEUR GÉNÉRAL' }.highlight === 'yellow' ? 'border-yellow-400' : 'border-red-600']" />
          </div>
          <div class="absolute z-10 hover:z-20 transition-all duration-300" style="left: 360px; top: 105px; width: 180px;">
            <OrgCard :node="{ key: 'dga', title: 'DIRECTEUR GÉNÉRAL ADJOINT' }" :assignments="assignments" :get-employee-name="getEmployeeName" :get-employee-photo="getEmployeePhoto" :can-assign="canAssign" @click="openAssignModal({ key: 'dga', title: 'DIRECTEUR GÉNÉRAL ADJOINT' })" class="shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-t-4" :class="[{ key: 'dga', title: 'DIRECTEUR GÉNÉRAL ADJOINT' }.highlight === 'yellow' ? 'border-yellow-400' : 'border-red-600']" />
          </div>
          <div class="absolute z-10 hover:z-20 transition-all duration-300" style="left: 960px; top: 155px; width: 180px;">
            <OrgCard :node="{ key: 'assistante', title: 'ASSISTANTE DE DIRECTION' }" :assignments="assignments" :get-employee-name="getEmployeeName" :get-employee-photo="getEmployeePhoto" :can-assign="canAssign" @click="openAssignModal({ key: 'assistante', title: 'ASSISTANTE DE DIRECTION' })" class="shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-t-4" :class="[{ key: 'assistante', title: 'ASSISTANTE DE DIRECTION' }.highlight === 'yellow' ? 'border-yellow-400' : 'border-red-600']" />
          </div>
          <div class="absolute z-10 hover:z-20 transition-all duration-300" style="left: 460px; top: 215px; width: 180px;">
            <OrgCard :node="{ key: 'resp_smqse', title: 'RESPONSABLE SMQSE' }" :assignments="assignments" :get-employee-name="getEmployeeName" :get-employee-photo="getEmployeePhoto" :can-assign="canAssign" @click="openAssignModal({ key: 'resp_smqse', title: 'RESPONSABLE SMQSE' })" class="shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-t-4" :class="[{ key: 'resp_smqse', title: 'RESPONSABLE SMQSE' }.highlight === 'yellow' ? 'border-yellow-400' : 'border-red-600']" />
          </div>
          <div class="absolute z-10 hover:z-20 transition-all duration-300" style="left: 160px; top: 215px; width: 180px;">
            <OrgCard :node="{ key: 'ast_smqse', title: 'ASSISTANT SMQSE' }" :assignments="assignments" :get-employee-name="getEmployeeName" :get-employee-photo="getEmployeePhoto" :can-assign="canAssign" @click="openAssignModal({ key: 'ast_smqse', title: 'ASSISTANT SMQSE' })" class="shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-t-4" :class="[{ key: 'ast_smqse', title: 'ASSISTANT SMQSE' }.highlight === 'yellow' ? 'border-yellow-400' : 'border-red-600']" />
          </div>
          <div class="absolute z-10 hover:z-20 transition-all duration-300" style="left: 360px; top: 295px; width: 180px;">
            <OrgCard :node="{ key: 'resp_it', title: 'RESPONSABLE SUPPORT IT' }" :assignments="assignments" :get-employee-name="getEmployeeName" :get-employee-photo="getEmployeePhoto" :can-assign="canAssign" @click="openAssignModal({ key: 'resp_it', title: 'RESPONSABLE SUPPORT IT' })" class="shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-t-4" :class="[{ key: 'resp_it', title: 'RESPONSABLE SUPPORT IT' }.highlight === 'yellow' ? 'border-yellow-400' : 'border-red-600']" />
          </div>
          <div class="absolute z-10 hover:z-20 transition-all duration-300" style="left: 160px; top: 445px; width: 180px;">
            <OrgCard :node="{ key: 'dir_fin', title: 'DIRECTEUR DES FINANCES ET CONTRÔLE', highlight: 'yellow' }" :assignments="assignments" :get-employee-name="getEmployeeName" :get-employee-photo="getEmployeePhoto" :can-assign="canAssign" @click="openAssignModal({ key: 'dir_fin', title: 'DIRECTEUR DES FINANCES ET CONTRÔLE', highlight: 'yellow' })" class="shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-t-4" :class="[{ key: 'dir_fin', title: 'DIRECTEUR DES FINANCES ET CONTRÔLE', highlight: 'yellow' }.highlight === 'yellow' ? 'border-yellow-400' : 'border-red-600']" />
          </div>
          <div class="absolute z-10 hover:z-20 transition-all duration-300" style="left: 160px; top: 545px; width: 180px;">
            <OrgCard :node="{ key: 'comp_rh', title: 'COMPTABLE ET RESPONSABLE RH' }" :assignments="assignments" :get-employee-name="getEmployeeName" :get-employee-photo="getEmployeePhoto" :can-assign="canAssign" @click="openAssignModal({ key: 'comp_rh', title: 'COMPTABLE ET RESPONSABLE RH' })" class="shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-t-4" :class="[{ key: 'comp_rh', title: 'COMPTABLE ET RESPONSABLE RH' }.highlight === 'yellow' ? 'border-yellow-400' : 'border-red-600']" />
          </div>
          <div class="absolute z-10 hover:z-20 transition-all duration-300" style="left: 160px; top: 625px; width: 180px;">
            <OrgCard :node="{ key: 'comp_tres', title: 'COMPTABLE TRÉSORERIE' }" :assignments="assignments" :get-employee-name="getEmployeeName" :get-employee-photo="getEmployeePhoto" :can-assign="canAssign" @click="openAssignModal({ key: 'comp_tres', title: 'COMPTABLE TRÉSORERIE' })" class="shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-t-4" :class="[{ key: 'comp_tres', title: 'COMPTABLE TRÉSORERIE' }.highlight === 'yellow' ? 'border-yellow-400' : 'border-red-600']" />
          </div>
          <div class="absolute z-10 hover:z-20 transition-all duration-300" style="left: 160px; top: 705px; width: 180px;">
            <OrgCard :node="{ key: 'comp_fourn', title: 'COMPTABLE FOURNISSEURS CLIENTS' }" :assignments="assignments" :get-employee-name="getEmployeeName" :get-employee-photo="getEmployeePhoto" :can-assign="canAssign" @click="openAssignModal({ key: 'comp_fourn', title: 'COMPTABLE FOURNISSEURS CLIENTS' })" class="shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-t-4" :class="[{ key: 'comp_fourn', title: 'COMPTABLE FOURNISSEURS CLIENTS' }.highlight === 'yellow' ? 'border-yellow-400' : 'border-red-600']" />
          </div>
          <div class="absolute z-10 hover:z-20 transition-all duration-300" style="left: 160px; top: 785px; width: 180px;">
            <OrgCard :node="{ key: 'recouv', title: 'CHARGÉE DU RECOUVREMENT' }" :assignments="assignments" :get-employee-name="getEmployeeName" :get-employee-photo="getEmployeePhoto" :can-assign="canAssign" @click="openAssignModal({ key: 'recouv', title: 'CHARGÉE DU RECOUVREMENT' })" class="shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-t-4" :class="[{ key: 'recouv', title: 'CHARGÉE DU RECOUVREMENT' }.highlight === 'yellow' ? 'border-yellow-400' : 'border-red-600']" />
          </div>
          <div class="absolute z-10 hover:z-20 transition-all duration-300" style="left: 660px; top: 445px; width: 180px;">
            <OrgCard :node="{ key: 'resp_com', title: 'RESPONSABLE PÔLE COMMERCIAL & APPRO', highlight: 'yellow' }" :assignments="assignments" :get-employee-name="getEmployeeName" :get-employee-photo="getEmployeePhoto" :can-assign="canAssign" @click="openAssignModal({ key: 'resp_com', title: 'RESPONSABLE PÔLE COMMERCIAL & APPRO', highlight: 'yellow' })" class="shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-t-4" :class="[{ key: 'resp_com', title: 'RESPONSABLE PÔLE COMMERCIAL & APPRO', highlight: 'yellow' }.highlight === 'yellow' ? 'border-yellow-400' : 'border-red-600']" />
          </div>
          <div class="absolute z-10 hover:z-20 transition-all duration-300" style="left: 410px; top: 545px; width: 180px;">
            <OrgCard :node="{ key: 'serv_com', title: 'SERVICE COMMERCIAL' }" :assignments="assignments" :get-employee-name="getEmployeeName" :get-employee-photo="getEmployeePhoto" :can-assign="canAssign" @click="openAssignModal({ key: 'serv_com', title: 'SERVICE COMMERCIAL' })" class="shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-t-4" :class="[{ key: 'serv_com', title: 'SERVICE COMMERCIAL' }.highlight === 'yellow' ? 'border-yellow-400' : 'border-red-600']" />
          </div>
          <div class="absolute z-10 hover:z-20 transition-all duration-300" style="left: 660px; top: 545px; width: 180px;">
            <OrgCard :node="{ key: 'serv_appro', title: 'SERVICE APPRO' }" :assignments="assignments" :get-employee-name="getEmployeeName" :get-employee-photo="getEmployeePhoto" :can-assign="canAssign" @click="openAssignModal({ key: 'serv_appro', title: 'SERVICE APPRO' })" class="shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-t-4" :class="[{ key: 'serv_appro', title: 'SERVICE APPRO' }.highlight === 'yellow' ? 'border-yellow-400' : 'border-red-600']" />
          </div>
          <div class="absolute z-10 hover:z-20 transition-all duration-300" style="left: 910px; top: 545px; width: 180px;">
            <OrgCard :node="{ key: 'serv_log', title: 'SERVICE LOGISTIQUE' }" :assignments="assignments" :get-employee-name="getEmployeeName" :get-employee-photo="getEmployeePhoto" :can-assign="canAssign" @click="openAssignModal({ key: 'serv_log', title: 'SERVICE LOGISTIQUE' })" class="shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-t-4" :class="[{ key: 'serv_log', title: 'SERVICE LOGISTIQUE' }.highlight === 'yellow' ? 'border-yellow-400' : 'border-red-600']" />
          </div>
          <div class="absolute z-10 hover:z-20 transition-all duration-300" style="left: 1360px; top: 445px; width: 180px;">
            <OrgCard :node="{ key: 'dir_tech', title: 'DIRECTEUR TECHNIQUE', highlight: 'yellow' }" :assignments="assignments" :get-employee-name="getEmployeeName" :get-employee-photo="getEmployeePhoto" :can-assign="canAssign" @click="openAssignModal({ key: 'dir_tech', title: 'DIRECTEUR TECHNIQUE', highlight: 'yellow' })" class="shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-t-4" :class="[{ key: 'dir_tech', title: 'DIRECTEUR TECHNIQUE', highlight: 'yellow' }.highlight === 'yellow' ? 'border-yellow-400' : 'border-red-600']" />
          </div>
          <div class="absolute z-10 hover:z-20 transition-all duration-300" style="left: 1210px; top: 545px; width: 180px;">
            <OrgCard :node="{ key: 'chef_etudes', title: 'CHEF SERVICE ÉTUDES' }" :assignments="assignments" :get-employee-name="getEmployeeName" :get-employee-photo="getEmployeePhoto" :can-assign="canAssign" @click="openAssignModal({ key: 'chef_etudes', title: 'CHEF SERVICE ÉTUDES' })" class="shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-t-4" :class="[{ key: 'chef_etudes', title: 'CHEF SERVICE ÉTUDES' }.highlight === 'yellow' ? 'border-yellow-400' : 'border-red-600']" />
          </div>
          <div class="absolute z-10 hover:z-20 transition-all duration-300" style="left: 1510px; top: 545px; width: 180px;">
            <OrgCard :node="{ key: 'chef_travaux', title: 'CHEF SERVICE TRAVAUX' }" :assignments="assignments" :get-employee-name="getEmployeeName" :get-employee-photo="getEmployeePhoto" :can-assign="canAssign" @click="openAssignModal({ key: 'chef_travaux', title: 'CHEF SERVICE TRAVAUX' })" class="shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-t-4" :class="[{ key: 'chef_travaux', title: 'CHEF SERVICE TRAVAUX' }.highlight === 'yellow' ? 'border-yellow-400' : 'border-red-600']" />
          </div>
          <div class="absolute z-10 hover:z-20 transition-all duration-300" style="left: 1330px; top: 625px; width: 180px;">
            <OrgCard :node="{ key: 'tech_etudes', title: 'TECHNICIENS BUREAU D\'ÉTUDES' }" :assignments="assignments" :get-employee-name="getEmployeeName" :get-employee-photo="getEmployeePhoto" :can-assign="canAssign" @click="openAssignModal({ key: 'tech_etudes', title: 'TECHNICIENS BUREAU D\'ÉTUDES' })" class="shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-t-4" :class="[{ key: 'tech_etudes', title: 'TECHNICIENS BUREAU D\'ÉTUDES' }.highlight === 'yellow' ? 'border-yellow-400' : 'border-red-600']" />
          </div>
          <div class="absolute z-10 hover:z-20 transition-all duration-300" style="left: 1330px; top: 705px; width: 180px;">
            <OrgCard :node="{ key: 'charge_projet', title: 'CHARGÉS DE PROJET' }" :assignments="assignments" :get-employee-name="getEmployeeName" :get-employee-photo="getEmployeePhoto" :can-assign="canAssign" @click="openAssignModal({ key: 'charge_projet', title: 'CHARGÉS DE PROJET' })" class="shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-t-4" :class="[{ key: 'charge_projet', title: 'CHARGÉS DE PROJET' }.highlight === 'yellow' ? 'border-yellow-400' : 'border-red-600']" />
          </div>
          <div class="absolute z-10 hover:z-20 transition-all duration-300" style="left: 1330px; top: 785px; width: 180px;">
            <OrgCard :node="{ key: 'charge_suivi', title: 'CHARGÉ DU SUIVI ET DES PLANNINGS' }" :assignments="assignments" :get-employee-name="getEmployeeName" :get-employee-photo="getEmployeePhoto" :can-assign="canAssign" @click="openAssignModal({ key: 'charge_suivi', title: 'CHARGÉ DU SUIVI ET DES PLANNINGS' })" class="shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-t-4" :class="[{ key: 'charge_suivi', title: 'CHARGÉ DU SUIVI ET DES PLANNINGS' }.highlight === 'yellow' ? 'border-yellow-400' : 'border-red-600']" />
          </div>
          <div class="absolute z-10 hover:z-20 transition-all duration-300" style="left: 1630px; top: 625px; width: 180px;">
            <OrgCard :node="{ key: 'cond_travaux', title: 'CONDUCTEURS DE TRAVAUX' }" :assignments="assignments" :get-employee-name="getEmployeeName" :get-employee-photo="getEmployeePhoto" :can-assign="canAssign" @click="openAssignModal({ key: 'cond_travaux', title: 'CONDUCTEURS DE TRAVAUX' })" class="shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-t-4" :class="[{ key: 'cond_travaux', title: 'CONDUCTEURS DE TRAVAUX' }.highlight === 'yellow' ? 'border-yellow-400' : 'border-red-600']" />
          </div>
          <div class="absolute z-10 hover:z-20 transition-all duration-300" style="left: 1630px; top: 705px; width: 180px;">
            <OrgCard :node="{ key: 'chef_atelier', title: 'CHEF D\'ATELIER' }" :assignments="assignments" :get-employee-name="getEmployeeName" :get-employee-photo="getEmployeePhoto" :can-assign="canAssign" @click="openAssignModal({ key: 'chef_atelier', title: 'CHEF D\'ATELIER' })" class="shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-t-4" :class="[{ key: 'chef_atelier', title: 'CHEF D\'ATELIER' }.highlight === 'yellow' ? 'border-yellow-400' : 'border-red-600']" />
          </div>
          <div class="absolute z-10 hover:z-20 transition-all duration-300" style="left: 1630px; top: 785px; width: 180px;">
            <OrgCard :node="{ key: 'chef_chantier', title: 'CHEFS DE CHANTIER' }" :assignments="assignments" :get-employee-name="getEmployeeName" :get-employee-photo="getEmployeePhoto" :can-assign="canAssign" @click="openAssignModal({ key: 'chef_chantier', title: 'CHEFS DE CHANTIER' })" class="shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-t-4" :class="[{ key: 'chef_chantier', title: 'CHEFS DE CHANTIER' }.highlight === 'yellow' ? 'border-yellow-400' : 'border-red-600']" />
          </div>
          <div class="absolute z-10 hover:z-20 transition-all duration-300" style="left: 1630px; top: 865px; width: 180px;">
            <OrgCard :node="{ key: 'vigiles', title: 'VIGILES' }" :assignments="assignments" :get-employee-name="getEmployeeName" :get-employee-photo="getEmployeePhoto" :can-assign="canAssign" @click="openAssignModal({ key: 'vigiles', title: 'VIGILES' })" class="shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-t-4" :class="[{ key: 'vigiles', title: 'VIGILES' }.highlight === 'yellow' ? 'border-yellow-400' : 'border-red-600']" />
          </div>
<!-- LINES -->
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 750px; top: 85px; width: 2px; height: 345px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 540px; top: 140px; width: 210px; height: 2px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 750px; top: 190px; width: 210px; height: 2px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 640px; top: 250px; width: 110px; height: 2px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 340px; top: 250px; width: 120px; height: 2px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 540px; top: 330px; width: 210px; height: 2px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 250px; top: 430px; width: 1200px; height: 2px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 250px; top: 430px; width: 2px; height: 15px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 750px; top: 430px; width: 2px; height: 15px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 1450px; top: 430px; width: 2px; height: 15px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 250px; top: 515px; width: 2px; height: 15px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 130px; top: 530px; width: 120px; height: 2px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 130px; top: 530px; width: 2px; height: 290px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 130px; top: 580px; width: 30px; height: 2px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 130px; top: 660px; width: 30px; height: 2px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 130px; top: 740px; width: 30px; height: 2px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 130px; top: 820px; width: 30px; height: 2px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 750px; top: 515px; width: 2px; height: 25px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 500px; top: 540px; width: 500px; height: 2px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 500px; top: 540px; width: 2px; height: 5px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 750px; top: 540px; width: 2px; height: 5px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 1000px; top: 540px; width: 2px; height: 5px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 1450px; top: 515px; width: 2px; height: 25px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 1300px; top: 540px; width: 300px; height: 2px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 1300px; top: 540px; width: 2px; height: 5px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 1600px; top: 540px; width: 2px; height: 5px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 1300px; top: 615px; width: 2px; height: 15px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 1300px; top: 630px; width: 2px; height: 190px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 1300px; top: 660px; width: 30px; height: 2px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 1300px; top: 740px; width: 30px; height: 2px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 1300px; top: 820px; width: 30px; height: 2px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 1600px; top: 615px; width: 2px; height: 15px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 1600px; top: 630px; width: 2px; height: 270px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 1600px; top: 660px; width: 30px; height: 2px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 1600px; top: 740px; width: 30px; height: 2px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 1600px; top: 820px; width: 30px; height: 2px;"></div>
          <div class="absolute bg-slate-300 z-0 rounded-full" style="left: 1600px; top: 900px; width: 30px; height: 2px;"></div>

</div>
</div>

</div>
</div>

    <!-- Modal d'affectation -->
    <div v-if="showModal && canAssign" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl w-full max-w-md overflow-hidden shadow-2xl">
        <div class="px-6 py-4 bg-[#b30c27] text-white flex justify-between items-center">
          <div>
            <h2 class="text-lg font-bold">Affecter un employé</h2>
            <p class="text-sm text-white/80 mt-0.5">{{ selectedNode?.title }}</p>
          </div>
          <button @click="showModal = false" class="hover:bg-[#d10f2f] p-1 rounded-full transition">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        <div class="p-6 space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Employé affecté à ce poste</label>
            <select
              v-model="selectedEmployeeId"
              class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition"
            >
              <option :value="null">— Poste vacant —</option>
              <option v-for="emp in employees" :key="emp.id" :value="emp.id">
                {{ emp.first_name || '' }} {{ emp.last_name || '' }}
                <span v-if="emp.position"> — {{ emp.position }}</span>
              </option>
            </select>
          </div>
          <div class="flex justify-end gap-3 pt-2 border-t border-gray-100">
            <button @click="showModal = false" class="px-6 py-2 text-gray-700 hover:bg-gray-100 rounded-xl transition">Annuler</button>
            <button @click="saveAssignment" class="px-6 py-2 bg-[#d10f2f] text-white hover:bg-[#97091f] rounded-xl shadow-lg transition">Enregistrer</button>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<!-- Composant OrgCard inline via script -->
<script lang="ts">
import { defineComponent, h } from 'vue';

export const OrgCard = defineComponent({
  name: 'OrgCard',
  props: {
    node: { type: Object, required: true },
    assignments: { type: Object, required: true },
    getEmployeeName: { type: Function, required: true },
    getEmployeePhoto: { type: Function, required: true },
    canAssign: { type: Boolean, default: false },
  },
  emits: ['click'],
  setup(props, { emit }) {
    return () => {
      const node = props.node as any;
      const empName = props.getEmployeeName(node.key);
      const photoUrl = props.getEmployeePhoto(node.key);

      const bgClass = node.highlight === 'yellow'
        ? 'bg-yellow-50 border-yellow-300'
        : 'bg-white border-gray-300';

      return h('div', {
        class: `relative border-2 rounded-lg px-3 py-2 min-w-[140px] max-w-[180px] text-center shadow-sm transition-all
          ${bgClass}
          ${props.canAssign ? 'cursor-pointer hover:shadow-md hover:border-red-300' : 'cursor-default'}`,
        onClick: () => emit('click'),
      }, [
        h('p', { class: 'text-[10px] font-bold text-gray-800 leading-tight uppercase' }, node.title),
        empName
          ? h('div', { class: 'mt-1.5 flex items-center justify-center gap-1' }, [
              photoUrl
                ? h('img', { src: photoUrl, class: 'w-4 h-4 rounded-full object-cover' })
                : h('span', { class: 'material-symbols-outlined text-[12px] text-gray-400' }, 'person'),
              h('p', { class: 'text-[10px] text-red-700 font-semibold truncate' }, empName),
            ])
          : props.canAssign
            ? h('p', { class: 'text-[9px] text-gray-300 italic mt-1' }, '+ Affecter')
            : h('p', { class: 'text-[9px] text-gray-300 italic mt-1' }, 'Vacant'),
      ]);
    };
  },
});
</script>

<style scoped>
.org-chart {
  display: flex;
  justify-content: center;
  min-width: max-content;
  padding: 2rem;
}
</style>
