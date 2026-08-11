<template>
  <div class="kanban-board">
    <div
      v-for="column in columns"
      :key="column.status"
      class="kanban-column"
    >
      <h3>{{ column.label }}</h3>
      <draggable
        v-model="column.tasks"
        group="tasks"
        class="task-list"
        item-key="id"
        @change="onColumnChange($event, column.status)"
      >
        <template #item="{ element: task }">
          <div class="task-card">
            <p>{{ task.title }}</p>
            <div class="actions-menu-container">
                <button class="btn-dots" @click.stop="toggleMenu(task.id)">⋮</button>
                <div v-if="activeMenuId === task.id" class="dropdown-menu">
                  <button @click="openEditModal(task)">Modifier</button>
                  <button class="delete-action" @click="emitDelete(task.id)">Supprimer</button>
                </div>
              </div>
            <small>{{ task.priority }}</small>
          </div>
        </template>
      </draggable>
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
import { ref, watch, onMounted, onUnmounted } from 'vue';
import draggable from 'vuedraggable';
import TaskModal from './TaskModal.vue';

const props = defineProps<{
  tasks: any[];
  employeesList?: any[];
  projectsList?: any[];
  milestonesList?: any[];
}>();

const emit = defineEmits<{
  (e: 'update-task', taskId: number, data: any): void;
  (e: 'delete-task', taskId: number): void;
}>();

const employees = ref<any[]>(props.employeesList || []);
const projects = ref<any[]>(props.projectsList || []);
const milestones = ref<any[]>(props.milestonesList || []);

const activeMenuId = ref<number | null>(null);
const isModalOpen = ref(false);
const editingTask = ref<any>({});

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

const columns = ref(
  ['A faire', 'En cours', 'Revue', 'Terminée'].map((status) => ({
    status,
    label: status,
    tasks: [] as any[]
  }))
);

watch(
  () => props.tasks,
  (newTasks) => {
    const grouped: Record<string, any[]> = {};
    newTasks.forEach(t => {
      const st = normalizeStatus(t.status);

      if (!grouped[st]) grouped[st] = [];
      grouped[st]?.push(t);
    });

    columns.value.forEach(col => {
      col.tasks = grouped[col.status] || [];
    });
  },
  { immediate: true, deep: true }
);

watch(
  () => props.milestonesList,
  (newMilestones) => {
    milestones.value = newMilestones || [];
  },
  { immediate: true, deep: true }
);

const toggleMenu = (taskId: number) => {
  activeMenuId.value = activeMenuId.value === taskId ? null : taskId;
};

const closeAllMenus = () => {
  activeMenuId.value = null;
};

onMounted(() => {
  window.addEventListener('click', closeAllMenus);
});

onUnmounted(() => {
  window.removeEventListener('click', closeAllMenus);
});

const emitDelete = (taskId: number) => {
  if (confirm("Êtes-vous sûr de vouloir supprimer (archiver) cette tâche ?")) {
    emit('delete-task', taskId);
  }
  closeAllMenus();
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
  closeAllMenus();
};
const closeModal = () => {
  isModalOpen.value = false;
  editingTask.value = {};
};

const saveTaskChanges = (eventData: { payload: any, files: File[] }) => {
  emit('update-task', editingTask.value.id, eventData);
  closeModal();
};

const onColumnChange = (event: any, targetStatus: string) => {
  const movedTask = event?.added?.element;
  if (!movedTask) return;

  if (normalizeStatus(movedTask.status) === targetStatus) return;
  emit('update-task', movedTask.id, { status: targetStatus });
};
</script>

<style scoped>
.kanban-board {
  display: flex;
  gap: 1.5rem;
  overflow-x: auto;
  padding: 1rem 0;
}
.kanban-column {
  flex: 0 0 280px;
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1rem;
}
.kanban-column h3 {
  margin-top: 0;
  font-size: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #6c757d;
}
.task-list {
  min-height: 100px;
}
.task-card {
  background: white;
  padding: 0.75rem;
  margin-bottom: 0.5rem;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}
.task-header p {
  margin: 0 0 0.25rem 0;
  font-weight: 500;
}
.btn-dots {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: #6c757d;
  padding: 0 0.25rem;
}
.actions-menu-container {
  position: relative;
}
.dropdown-menu {
  position: absolute;
  right: 0;
  top: 100%;
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  z-index: 10;
  display: flex;
  flex-direction: column;
  min-width: 100px;
}
.dropdown-menu button {
  background: none;
  border: none;
  padding: 0.5rem 1rem;
  text-align: left;
  cursor: pointer;
  font-size: 0.85rem;
}
.dropdown-menu button:hover {
  background: #f8f9fa;
}
.dropdown-menu .delete-action {
  color: #dc3545;
}
.dropdown-menu .delete-action:hover {
  background: #f8d7da;
}
.task-assignee {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
}
.avatar {
  background: #0d6efd;
  color: white;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
}

/* Styles Modale */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}
.modal-content {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  width: 450px;
  max-width: 90%;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}
.form-group {
  margin-bottom: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.form-row {
  display: flex;
  gap: 1rem;
}
.form-row .form-group {
  flex: 1;
}
label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #495057;
}
input, select {
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1.5rem;
}
.btn-cancel {
  background: #e9ecef;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}
.btn-save {
  background: #0d6efd;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}
</style>