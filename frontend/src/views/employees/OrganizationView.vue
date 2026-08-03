<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue';
import type { NodeMouseEvent } from '@vue-flow/core';
import { VueFlow, useVueFlow, Position } from '@vue-flow/core';
import { Background } from '@vue-flow/background';
import { Controls } from '@vue-flow/controls';
import dagre from 'dagre';
import { toPng } from 'html-to-image';
import { jsPDF } from 'jspdf';
import { employeeService } from '@/services/employees';
import AppLayout from '@/layouts/AppLayout.vue';

import '@vue-flow/core/dist/style.css';
import '@vue-flow/core/dist/theme-default.css';
import '@vue-flow/controls/dist/style.css';

const { fitView } = useVueFlow();

const nodes = ref([]);
const edges = ref([]);
const isLoading = ref(true);

const selectedNode = ref<any>(null);
const isModalOpen = ref(false);

const onNodeClick = (event: NodeMouseEvent) => {
  selectedNode.value = event.node.data;
  isModalOpen.value = true;
};

const fetchOrgChart = async () => {
  try {
    isLoading.value = true;
    const response = await employeeService.getOrgChart();
    const rawData = response.data;
    
    const { newNodes, newEdges } = buildGraph(rawData);
    
    // Apply Dagre layout
    const layouted = getLayoutedElements(newNodes, newEdges);
    nodes.value = layouted.nodes;
    edges.value = layouted.edges;

    await nextTick();
    setTimeout(() => {
      fitView({ padding: 0.2, includeHiddenNodes: true });
    }, 100);

  } catch (error) {
    console.error("Failed to load org chart", error);
  } finally {
    isLoading.value = false;
  }
};

const buildGraph = (rootNodes: any[]) => {
  const n = [];
  const e = [];
  const queue = [...rootNodes];
  
  while (queue.length > 0) {
    const current = queue.shift();
    
    n.push({
      id: current.id.toString(),
      label: current.name,
      position: { x: 0, y: 0 },
      type: 'customNode', // We will use a custom node template
      data: { 
        name: current.name,
        position: current.position,
        department: current.department,
        email: current.email,
        phone: current.phone,
        matricule: current.matricule,
        status: current.status
      }
    });
    
    for (const child of current.children) {
      e.push({
        id: `e${current.id}-${child.id}`,
        source: current.id.toString(),
        target: child.id.toString(),
        type: 'smoothstep',
        animated: true,
        style: { stroke: '#9ca3af', strokeWidth: 2, fill: 'none' }
      });
      queue.push(child);
    }
  }
  
  return { newNodes: n, newEdges: e };
};

const getLayoutedElements = (nodes: any[], edges: any[], direction = 'TB') => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  // Direction: TB (Top-to-Bottom) or LR (Left-to-Right)
  dagreGraph.setGraph({ rankdir: direction, nodesep: 100, ranksep: 120 });

  nodes.forEach((node) => {
    // Assuming approx width and height for our custom node
    dagreGraph.setNode(node.id, { width: 250, height: 100 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  nodes.forEach((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    node.targetPosition = direction === 'LR' ? Position.Left : Position.Top;
    node.sourcePosition = direction === 'LR' ? Position.Right : Position.Bottom;

    // We are shifting the dagre node position (anchor=center) to the top left
    // so it matches the Vue Flow node anchor point (top left).
    node.position = {
      x: nodeWithPosition.x - 250 / 2,
      y: nodeWithPosition.y - 100 / 2,
    };
  });

  return { nodes, edges };
};

const exportChart = async (format: 'png' | 'pdf') => {
  // Use the viewport which contains the actual nodes instead of the transformation pane
  const element = document.querySelector('.vue-flow__viewport') as HTMLElement;
  if (!element) return;
  
  // Fit view before exporting to make sure everything is visible
  fitView({ padding: 0.1 });
  // Wait for animation and rendering
  await new Promise(r => setTimeout(r, 600));

  try {
    // Get the bounding box of the actual graph to crop the image perfectly
    const bounds = element.getBoundingClientRect();
    
    // Use high pixel ratio for maximum sharpness
    const imgData = await toPng(element, { 
      pixelRatio: 4, // Higher resolution for crisp text
      backgroundColor: '#f9fafb', // Lighter background (gray-50)
      style: {
        transform: 'translate(0, 0)', // Reset transform to avoid offset bugs
      }
    });
    
    if (format === 'png') {
      const link = document.createElement('a');
      link.href = imgData;
      link.download = 'organigramme.png';
      link.click();
    } else {
      const pdf = new jsPDF('landscape', 'mm', 'a4');
      const imgProps = pdf.getImageProperties(imgData);
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;
      
      pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
      pdf.save('organigramme.pdf');
    }
  } catch(e) {
    console.error("Export failed", e);
  }
};

onMounted(() => {
  fetchOrgChart();
});
</script>

<template>
  <AppLayout>
    <div class="h-[calc(100vh-6rem)] w-full bg-gray-50 flex flex-col p-4">
    
    <!-- Header & Actions -->
    <div class="flex justify-between items-center mb-4 bg-white p-4 rounded-xl shadow-sm border border-gray-100">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">Organigramme Entreprise</h1>
        <p class="text-sm text-gray-500">Vue hiérarchique de l'organisation</p>
      </div>
      
      <div class="flex gap-3">
        <button 
          @click="exportChart('png')"
          class="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors shadow-sm"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Export PNG
        </button>
        <button 
          @click="exportChart('pdf')"
          class="flex items-center gap-2 px-4 py-2 bg-[#d10f2f] border border-transparent rounded-lg text-sm font-medium text-white hover:bg-[#97091f] transition-colors shadow-sm"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Export PDF
        </button>
      </div>
    </div>

    <!-- Org Chart Container -->
    <div class="flex-1 bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden relative" id="org-chart-container">
      
      <!-- Loading State -->
      <div v-if="isLoading" class="absolute inset-0 z-10 bg-white/80 backdrop-blur-sm flex flex-col items-center justify-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
        <p class="mt-4 text-gray-600 font-medium">Chargement de l'organigramme...</p>
      </div>

      <VueFlow 
        :nodes="nodes" 
        :edges="edges" 
        :default-edge-options="{ type: 'smoothstep' }"
        :nodes-draggable="false"
        @node-click="onNodeClick"
        :min-zoom="0.1"
        :max-zoom="4"
        fit-view-on-init
      >
        <Background pattern-color="#e5e7eb" :gap="20" />
        <Controls />

        <!-- Custom Node Template -->
        <template #node-customNode="props">
          <div class="w-[250px] bg-white rounded-xl shadow-md border-t-4 hover:shadow-lg transition-shadow overflow-hidden"
               :class="{'border-red-600': props.data.department === 'Direction', 
                        'border-green-500': props.data.department === 'RH',
                        'border-purple-500': props.data.department === 'IT',
                        'border-orange-500': props.data.department === 'Achats',
                        'border-gray-500': !['Direction', 'RH', 'IT', 'Achats'].includes(props.data.department)
               }">
            
            <div class="p-4">
              <!-- Header: Avatar & Info -->
              <div class="flex items-center gap-3 mb-3">
                <div class="w-12 h-12 rounded-full bg-gray-100 border border-gray-200 flex items-center justify-center text-lg font-bold text-gray-600">
                  {{ props.data.name.charAt(0) }}
                </div>
                <div>
                  <h3 class="text-sm font-bold text-gray-900 truncate w-32" :title="props.data.name">{{ props.data.name }}</h3>
                  <p class="text-xs text-red-600 font-medium truncate w-32" :title="props.data.position">{{ props.data.position }}</p>
                </div>
              </div>
              
              <!-- Footer: Department Badge -->
              <div class="pt-2 border-t border-gray-100 flex justify-between items-center">
                <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                  {{ props.data.department }}
                </span>
              </div>
            </div>
          </div>
        </template>
        
      </VueFlow>
    </div>

    <!-- Employee Detail Modal -->
    <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm" @click.self="isModalOpen = false">
      <div class="bg-white rounded-xl shadow-xl max-w-md w-full overflow-hidden transform transition-all">
        <!-- Modal Header -->
        <div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
          <h3 class="text-lg font-bold text-gray-900">Détails de l'employé</h3>
          <button @click="isModalOpen = false" class="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-md hover:bg-gray-100">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <!-- Modal Body -->
        <div class="p-6" v-if="selectedNode">
          <div class="flex items-center gap-4 mb-6">
            <div class="w-16 h-16 rounded-full bg-gray-100 border border-gray-200 flex items-center justify-center text-2xl font-bold text-gray-600 shadow-sm">
              {{ selectedNode.name ? selectedNode.name.charAt(0) : '?' }}
            </div>
            <div>
              <h4 class="text-xl font-bold text-gray-900">{{ selectedNode.name }}</h4>
              <p class="text-red-600 font-medium">{{ selectedNode.position }}</p>
            </div>
          </div>
          
          <div class="space-y-4">
            <div class="bg-gray-50 p-3 rounded-lg border border-gray-100">
              <p class="text-xs text-gray-500 font-medium mb-1">Département</p>
              <p class="text-sm text-gray-900 font-medium">{{ selectedNode.department }}</p>
            </div>
            
            <div class="grid grid-cols-2 gap-4">
              <div class="bg-gray-50 p-3 rounded-lg border border-gray-100">
                <p class="text-xs text-gray-500 font-medium mb-1">Email</p>
                <p class="text-sm text-gray-900 truncate font-medium" :title="selectedNode.email">{{ selectedNode.email || 'Non renseigné' }}</p>
              </div>
              <div class="bg-gray-50 p-3 rounded-lg border border-gray-100">
                <p class="text-xs text-gray-500 font-medium mb-1">Téléphone</p>
                <p class="text-sm text-gray-900 font-medium">{{ selectedNode.phone || 'Non renseigné' }}</p>
              </div>
              <div class="bg-gray-50 p-3 rounded-lg border border-gray-100">
                <p class="text-xs text-gray-500 font-medium mb-1">Matricule</p>
                <p class="text-sm text-gray-900 font-medium">{{ selectedNode.matricule || 'Non renseigné' }}</p>
              </div>
              <div class="bg-gray-50 p-3 rounded-lg border border-gray-100">
                <p class="text-xs text-gray-500 font-medium mb-1">Statut</p>
                <p class="text-sm text-gray-900">
                  <span v-if="selectedNode.status === 'Actif' || selectedNode.status === 'Active'" class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                    Actif
                  </span>
                  <span v-else-if="selectedNode.status === 'Inactif' || selectedNode.status === 'Inactive'" class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                    Inactif
                  </span>
                  <span v-else class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                    {{ selectedNode.status || 'Non renseigné' }}
                  </span>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  </AppLayout>
</template>

<style scoped>
/* Optional styling */
</style>
