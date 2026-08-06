<template>
  <div class="custom-gantt-wrapper flex flex-col w-full h-[600px] bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
    
    <!-- Toolbar -->
    <div class="flex items-center justify-between p-4 border-b border-gray-200 bg-gray-50 shrink-0">
      <div class="flex items-center gap-4">
        <h3 class="font-semibold text-gray-800">Diagramme de Gantt</h3>
        <div class="flex items-center bg-white border border-gray-300 rounded-lg overflow-hidden shadow-sm">
          <button @click="zoomLevel = 'day'" :class="['px-3 py-1.5 text-sm font-medium transition', zoomLevel === 'day' ? 'bg-red-500 text-white' : 'text-gray-600 hover:bg-gray-100']">Jours</button>
          <button @click="zoomLevel = 'week'" :class="['px-3 py-1.5 text-sm font-medium transition border-l border-gray-300', zoomLevel === 'week' ? 'bg-red-500 text-white' : 'text-gray-600 hover:bg-gray-100']">Semaines</button>
          <button @click="zoomLevel = 'month'" :class="['px-3 py-1.5 text-sm font-medium transition border-l border-gray-300', zoomLevel === 'month' ? 'bg-red-500 text-white' : 'text-gray-600 hover:bg-gray-100']">Mois</button>
        </div>
      </div>
      <div>
         <button class="px-3 py-1.5 text-sm bg-white border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 shadow-sm" @click="scrollToToday">
            Aujourd'hui
         </button>
      </div>
    </div>

    <div class="flex flex-1 overflow-hidden relative">
       <!-- Left Sidebar for task names -->
       <div class="w-72 flex-shrink-0 border-r border-gray-200 bg-white flex flex-col z-20 shadow-[2px_0_5px_rgba(0,0,0,0.03)]">
         <div class="h-14 border-b border-gray-200 bg-gray-50 flex items-center px-4 font-semibold text-gray-600 text-sm shrink-0">
            Tâches
         </div>
         <div class="flex-1 overflow-y-auto no-scrollbar" ref="leftSidebarRef" @scroll="syncScroll('left')">
            <div v-for="task in tasksWithPositions" :key="'sidebar-'+task.id" class="h-12 border-b border-gray-100 flex flex-col justify-center px-4 hover:bg-gray-50 cursor-pointer transition-colors" @click="openEditModal(task)">
               <div class="truncate text-sm font-medium text-gray-800" :title="task.title">{{ task.title }}</div>
               <div class="text-[10px] text-gray-500 truncate mt-0.5 font-medium">
                  {{ formatDate(task.cleanStart) }} - {{ formatDate(task.cleanDue) }}
               </div>
            </div>
         </div>
       </div>

       <!-- Right Timeline -->
       <div class="flex-1 overflow-x-auto overflow-y-auto bg-[#fcfcfc] relative" ref="timelineRef" @scroll="syncScroll('right')">
         
         <!-- Timeline Header -->
         <div class="sticky top-0 z-10 bg-gray-50 border-b border-gray-200 flex flex-col h-14 shadow-sm">
            <!-- Months Row -->
            <div class="flex h-7 border-b border-gray-200">
               <div v-for="month in months" :key="month.key" class="flex-shrink-0 flex items-center justify-center text-xs font-semibold text-gray-600 border-r border-gray-200" :style="{ width: month.width + 'px' }">
                  {{ month.label }}
               </div>
            </div>
            <!-- Days Row -->
            <div class="flex h-7">
               <div v-for="day in days" :key="day.date.toISOString()" class="flex-shrink-0 flex items-center justify-center text-[10px] text-gray-500 border-r border-gray-100 transition-colors" :style="{ width: dayWidth + 'px' }" :class="{'bg-red-50 text-red-600 font-bold': day.isToday, 'bg-gray-100': day.isWeekend && zoomLevel !== 'month'}">
                  {{ zoomLevel === 'day' ? day.dayNumber : (zoomLevel === 'week' ? (day.dayOfWeek === 1 ? day.dayNumber : '') : '') }}
               </div>
            </div>
         </div>

         <!-- Timeline Body (Grid & Bars) -->
         <div class="relative" :style="{ width: totalTimelineWidth + 'px', height: Math.max(tasksWithPositions.length * 48, 100) + 'px' }">
            
            <!-- Vertical Grid Lines -->
            <div class="absolute inset-0 flex pointer-events-none">
               <div v-for="day in days" :key="'grid-'+day.date.toISOString()" class="flex-shrink-0 border-r border-gray-100 h-full" :style="{ width: dayWidth + 'px' }" :class="{'bg-gray-50/50': day.isWeekend}"></div>
            </div>

            <!-- Task Rows & Bars -->
            <div v-for="(task, index) in tasksWithPositions" :key="'bar-'+task.id" class="absolute left-0 right-0 h-12 border-b border-gray-100 flex items-center group hover:bg-gray-50/50 transition-colors" :style="{ top: (index * 48) + 'px' }">
               
               <!-- The Bar -->
               <div 
                 class="absolute h-8 rounded-md shadow-sm flex items-center px-2 cursor-pointer transition-all hover:brightness-110 hover:shadow-md border border-black/10 z-10"
                 :style="{ 
                   left: task.left + 'px', 
                   width: task.width + 'px', 
                   backgroundColor: task.color,
                   minWidth: '6px' 
                 }"
                 @click="openEditModal(task._original)"
                 :title="task.title + '\n' + formatDate(task.cleanStart) + ' - ' + formatDate(task.cleanDue)"
               >
                 <span v-if="task.width > 60" class="text-white text-xs font-semibold truncate">{{ task.title }}</span>
               </div>
            </div>
            
            <!-- Today Indicator Line -->
            <div v-if="todayLeft >= 0" class="absolute top-0 bottom-0 w-0.5 bg-red-500 z-10 pointer-events-none" :style="{ left: todayLeft + 'px' }">
                <div class="absolute -top-1 -left-1.5 w-3 h-3 rounded-full bg-red-500"></div>
            </div>
            
            <!-- Empty state -->
            <div v-if="tasksWithPositions.length === 0" class="absolute inset-0 flex items-center justify-center text-gray-400">
                Aucune tâche planifiée
            </div>
         </div>
       </div>
    </div>

    <TaskModal 
      v-if="isModalOpen" 
      :task="editingTask" 
      :employees="employees"
      :milestones="milestones"
      @close="closeModal" 
      @save="saveTaskChanges" 
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import TaskModal from './TaskModal.vue';

const props = defineProps<{
  tasks: Array<any>;
  employeesList?: Array<any>;
  milestonesList?: Array<any>;
}>();

const emit = defineEmits<{
  (e: 'update-task', taskId: number, data: any): void;
}>();

// Editing state
const isModalOpen = ref(false);
const editingTask = ref<any>({});
const employees = ref<any[]>(props.employeesList || []);
const milestones = ref<any[]>(props.milestonesList || []);

watch(() => props.employeesList, (n) => employees.value = n || []);
watch(() => props.milestonesList, (n) => milestones.value = n || []);

const statusMap: Record<string, string> = {
  TODO: 'A faire',
  IN_PROGRESS: 'En cours',
  REVIEW: 'Revue',
  DONE: 'Terminée',
  ARCHIVED: 'Archivée',
  'A faire': 'A faire',
  'En cours': 'En cours',
  Revue: 'Revue',
  'Terminée': 'Terminée',
  'Archivée': 'Archivée'
};

const normalizeStatus = (status?: string) => {
  if (!status) return 'A faire';
  return statusMap[status] || status;
};

const openEditModal = (task: any) => {
  editingTask.value = { 
    id: task.id,
    title: task.title || '',
    description: task.description || '',
    priority: task.priority || 'Moyenne',
    status: normalizeStatus(task.status),
    due_date: task.due_date || task.date_fin || '', 
    start_date: task.start_date || task.date_debut || '',
    assignee_id: task.assignee_id || null,
    project_id: task.project_id,
    milestone_id: task.milestone_id || null,
    weight: task.weight || 1
  };
  isModalOpen.value = true;
};

const closeModal = () => {
  isModalOpen.value = false;
  editingTask.value = {};
};

const saveTaskChanges = (eventData: { payload: any, files: File[] }) => {
  emit('update-task', editingTask.value.id, eventData);
  closeModal();
};

const zoomLevel = ref<'day' | 'week' | 'month'>('day');

const dayWidth = computed(() => {
  if (zoomLevel.value === 'day') return 45;
  if (zoomLevel.value === 'week') return 15;
  return 4; // month
});

const statusColor = (status?: string | null): string => {
  if (!status) return '#64748b'; // slate-500
  const s = status.toLowerCase();
  if (s.includes('terminé') || s === 'done') return '#10b981'; // emerald-500
  if (s.includes('en cours') || s === 'in_progress') return '#f59e0b'; // amber-500
  if (s.includes('revue') || s === 'review') return '#8b5cf6'; // violet-500
  if (s.includes('a faire') || s === 'to do' || s === 'todo') return '#3b82f6'; // blue-500
  return '#ef4444'; // red-500
};

// Date utilities
const normalizeDate = (d: string | null | undefined, fallback: Date): Date => {
  if (!d) return fallback;
  const parsed = new Date(d);
  if (isNaN(parsed.getTime())) return fallback;
  return parsed;
};

const formatDate = (d: Date) => {
    return d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' });
}

const processedTasks = computed(() => {
  if (!props.tasks) return [];
  
  return props.tasks.map(t => {
    // Intelligent date fallback
    const created = normalizeDate(t.created_at, new Date());
    let start = normalizeDate(t.start_date, created);
    
    // If start is parsed but time is 00:00, use it
    let due = t.due_date ? new Date(t.due_date) : new Date(start.getTime() + 7 * 86400000);
    if (isNaN(due.getTime())) due = new Date(start.getTime() + 7 * 86400000);
    
    // Ensure due is after start
    if (due.getTime() < start.getTime()) {
      due = new Date(start.getTime() + 86400000);
    }
    
    return {
      ...t,
      cleanStart: start,
      cleanDue: due,
      color: statusColor(t.status),
      _original: t
    };
  }).sort((a, b) => a.cleanStart.getTime() - b.cleanStart.getTime());
});

// Calculate timeline bounds
const timelineBounds = computed(() => {
  let minTime = new Date().getTime();
  let maxTime = new Date().getTime();
  
  if (processedTasks.value.length > 0) {
    minTime = Math.min(...processedTasks.value.map(t => t.cleanStart.getTime()));
    maxTime = Math.max(...processedTasks.value.map(t => t.cleanDue.getTime()));
  }
  
  // Add padding: 14 days before, 30 days after
  const start = new Date(minTime - 14 * 86400000);
  // Start on a Monday
  const day = start.getDay();
  const diff = start.getDate() - day + (day == 0 ? -6:1);
  start.setDate(diff);
  start.setHours(0,0,0,0);

  const end = new Date(maxTime + 30 * 86400000);
  end.setHours(23,59,59,999);
  
  return { start, end };
});

const days = computed(() => {
  const result = [];
  const { start, end } = timelineBounds.value;
  let current = new Date(start);
  const todayStr = new Date().toDateString();
  
  while (current <= end) {
    result.push({
      date: new Date(current),
      dayNumber: current.getDate(),
      dayOfWeek: current.getDay(),
      month: current.getMonth(),
      year: current.getFullYear(),
      isWeekend: current.getDay() === 0 || current.getDay() === 6,
      isToday: current.toDateString() === todayStr
    });
    current.setDate(current.getDate() + 1);
  }
  return result;
});

const totalTimelineWidth = computed(() => days.value.length * dayWidth.value);

const months = computed(() => {
  const result = [];
  if (days.value.length === 0) return result;
  
  let currentMonth = days.value[0].month;
  let currentYear = days.value[0].year;
  let daysInMonth = 0;
  
  const monthNames = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"];
  
  days.value.forEach(d => {
    if (d.month === currentMonth && d.year === currentYear) {
      daysInMonth++;
    } else {
      result.push({
        key: `${currentYear}-${currentMonth}`,
        label: `${monthNames[currentMonth]} ${currentYear}`,
        width: daysInMonth * dayWidth.value
      });
      currentMonth = d.month;
      currentYear = d.year;
      daysInMonth = 1;
    }
  });
  
  if (daysInMonth > 0) {
    result.push({
      key: `${currentYear}-${currentMonth}`,
      label: `${monthNames[currentMonth]} ${currentYear}`,
      width: daysInMonth * dayWidth.value
    });
  }
  
  return result;
});

// Calculate positions for tasks
const tasksWithPositions = computed(() => {
  const { start } = timelineBounds.value;
  const startMs = start.getTime();
  
  return processedTasks.value.map(t => {
    const startTaskMs = t.cleanStart.getTime();
    const endTaskMs = t.cleanDue.getTime();
    
    // Convert ms to precise days including fractions for accurate rendering
    const leftDays = (startTaskMs - startMs) / 86400000;
    const durationDays = (endTaskMs - startTaskMs) / 86400000;
    
    return {
      ...t,
      left: leftDays * dayWidth.value,
      width: Math.max(durationDays * dayWidth.value, 6) // min 6px width
    };
  });
});

const todayLeft = computed(() => {
  const today = new Date().getTime();
  const start = timelineBounds.value.start.getTime();
  if (today < start || today > timelineBounds.value.end.getTime()) return -1;
  return ((today - start) / 86400000) * dayWidth.value;
});

// Sync scrolling
const leftSidebarRef = ref<HTMLElement | null>(null);
const timelineRef = ref<HTMLElement | null>(null);

let isSyncingLeft = false;
let isSyncingRight = false;

const syncScroll = (source: 'left' | 'right') => {
  if (!leftSidebarRef.value || !timelineRef.value) return;
  
  if (source === 'left') {
    if (isSyncingRight) {
      isSyncingRight = false;
      return;
    }
    isSyncingLeft = true;
    timelineRef.value.scrollTop = leftSidebarRef.value.scrollTop;
  } else {
    if (isSyncingLeft) {
      isSyncingLeft = false;
      return;
    }
    isSyncingRight = true;
    leftSidebarRef.value.scrollTop = timelineRef.value.scrollTop;
  }
};

const scrollToToday = () => {
    if (timelineRef.value && todayLeft.value >= 0) {
        const containerWidth = timelineRef.value.clientWidth;
        timelineRef.value.scrollTo({
            left: Math.max(0, todayLeft.value - (containerWidth / 2)),
            behavior: 'smooth'
        });
    }
};

onMounted(() => {
    // Scroll timeline to today
    setTimeout(() => {
        scrollToToday();
    }, 100);
});
</script>

<style scoped>
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>