<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { marked } from 'marked'
import { taskService } from '@/services/projects'

interface TaskDocument {
  id: number
  task_id: number
  file_name: string
  storage_path: string
  mime_type?: string
  uploaded_at: string
}

const props = defineProps<{
  task: any,
  employees : Array<{
    id: number,
    nom?: string,
    prenom?: string,
    first_name?: string,
    last_name?: string
  }>,
  milestones?: Array<{
    id: number,
    title: string
  }>
}>()

const emit = defineEmits(['close', 'save'])
const isDragging = ref(false)
const taskDocuments = ref<TaskDocument[]>([])
const loadingTaskDocuments = ref(false)
const documentActionId = ref<number | null>(null)
const documentError = ref('')
const descriptionMode = ref<'edit' | 'preview'>('edit')
const renderedDescription = computed(() => marked.parse(localTask.value.description || '') as string)

const onDragOver = (e: DragEvent) => {
  isDragging.value = true
}

const onDragLeave = (e: DragEvent) => {
  isDragging.value = false
}

const onDrop = (e: DragEvent) => {
  isDragging.value = false
  if (e.dataTransfer && e.dataTransfer.files) {
    uploadedFiles.value.push(...Array.from(e.dataTransfer.files))
  }
}
const localTask = ref({
  ...props.task,
  task_metadata: props.task.task_metadata ? JSON.stringify(props.task.task_metadata, null, 2) : ''
})

watch(() => props.task, (newTask) => {
  localTask.value = {
    ...newTask,
    task_metadata: newTask.task_metadata ? JSON.stringify(newTask.task_metadata, null, 2) : ''
  }

  descriptionMode.value = 'edit'

  void loadTaskDocuments()
}, { deep: true })

const uploadedFiles = ref<File[]>([])

const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files) {
    uploadedFiles.value.push(...Array.from(target.files))
  }
}

const removeFile = (index: number) => {
  uploadedFiles.value.splice(index, 1)
}

const getEmployeeLabel = (emp: {
  id: number,
  nom?: string,
  prenom?: string,
  first_name?: string,
  last_name?: string
}) => {
  const lastName = emp.nom || emp.last_name || ''
  const firstName = emp.prenom || emp.first_name || ''
  const fullName = `${lastName} ${firstName}`.trim()

  return fullName || `Employe n°${emp.id}`
}

const loadTaskDocuments = async () => {
  const taskId = props.task?.id
  const projectId = props.task?.project_id

  taskDocuments.value = []
  documentError.value = ''

  if (!taskId || !projectId) return

  try {
    loadingTaskDocuments.value = true
    const response = await taskService.getTaskDocuments(projectId, taskId)
    taskDocuments.value = response.data || []
  } catch (error: any) {
    console.error('Erreur lors du chargement des documents de tâche', error)

    const status = error?.response?.status
    const detail = error?.response?.data?.detail

    if (status === 404 && detail === 'Not Found') {
      documentError.value = 'Route API des documents indisponible. Redémarre le backend pour charger les nouvelles routes.'
      return
    }

    if (status === 404 && typeof detail === 'string') {
      documentError.value = detail
      return
    }

    if (status === 403) {
      documentError.value = 'Vous n\'avez pas la permission de lire les documents de tâche.'
      return
    }

    if (typeof detail === 'string' && detail.trim().length > 0) {
      documentError.value = detail
      return
    }

    documentError.value = 'Impossible de charger les documents existants.'
  } finally {
    loadingTaskDocuments.value = false
  }
}

const downloadTaskDocument = async (doc: TaskDocument) => {
  const projectId = props.task?.project_id
  if (!projectId) return

  try {
    documentActionId.value = doc.id
    documentError.value = ''
    await taskService.downloadTaskDocument(projectId, doc.id, doc.file_name)
  } catch (error) {
    console.error('Erreur lors du téléchargement du document', error)
    documentError.value = 'Téléchargement impossible pour ce document.'
  } finally {
    documentActionId.value = null
  }
}

const deleteTaskDocument = async (doc: TaskDocument) => {
  const projectId = props.task?.project_id
  if (!projectId) return

  if (!confirm('Voulez-vous vraiment supprimer ce document ?')) {
    return
  }

  try {
    documentActionId.value = doc.id
    documentError.value = ''
    await taskService.deleteTaskDocument(projectId, doc.id)
    taskDocuments.value = taskDocuments.value.filter((d) => d.id !== doc.id)
  } catch (error) {
    console.error('Erreur lors de la suppression du document', error)
    documentError.value = 'Suppression impossible pour ce document.'
  } finally {
    documentActionId.value = null
  }
}

void loadTaskDocuments()

const handleSave = () => {
  const payload = {
    title: localTask.value.title,
    description: localTask.value.description,
    status: localTask.value.status,
    priority: localTask.value.priority,
    due_date: localTask.value.due_date,
    assignee_id: localTask.value.assignee_id,
    milestone_id: localTask.value.milestone_id,
    weight: Number(localTask.value.weight || 1),
    task_metadata: localTask.value.task_metadata ? JSON.parse(localTask.value.task_metadata) : null,
  }
  
  emit('save', { payload, files: uploadedFiles.value })
}
</script>

<template>
  <div
    class="fixed inset-0 bg-gray-900/50 backdrop-blur-sm flex justify-center items-center z-50 p-4"
    @click.self="emit('close')"
  >
    <!-- Conteneur principal : max-w-3xl pour avoir de la place, max-h-[90vh] pour scroller si l'écran est petit -->
    <div class="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden"> 
      
      <!-- En-tête -->
      <div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-red-50/50">
        <h3 class="text-xl font-semibold text-red-900">Modifier la tâche</h3>
        <button @click="emit('close')" class="text-gray-400 hover:text-red-600 transition-colors">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Corps (scrollable) -->
      <div class="p-6 overflow-y-auto space-y-6 flex-1">
        
        <!-- Ligne 1 : Titre -->
        <div>
          <label class="block text-sm font-medium text-gray-900 mb-1">Titre de la tâche</label>
          <input 
            class="w-full border border-gray-300 rounded-md px-4 py-2.5 text-gray-900 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-shadow" 
            v-model="localTask.title"
            placeholder="Ex: Mise à jour du composant d'authentification"
          >
        </div>

        <!-- Ligne 2 : Grille (Statut, Priorité, Date, Assigné) -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label class="block text-sm font-medium text-gray-900 mb-1">Statut</label>
            <select 
              class="w-full border border-gray-300 rounded-md px-4 py-2.5 text-gray-900 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 bg-white"
              v-model="localTask.status"
            >
              <option value="A faire">À faire</option>
              <option value="En cours">En cours</option>
              <option value="Revue">Revue</option>
              <option value="Terminée">Terminée</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-900 mb-1">Priorité</label>
            <select 
              class="w-full border border-gray-300 rounded-md px-4 py-2.5 text-gray-900 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 bg-white"
              v-model="localTask.priority"
            >
              <option value="Basse">Basse</option>
              <option value="Moyenne">Moyenne</option>
              <option value="Haute">Haute</option>
              <option value="Urgente">Urgente</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-900 mb-1">Date d'échéance (Due Date)</label>
            <input 
              type="date"
              class="w-full border border-gray-300 rounded-md px-4 py-2.5 text-gray-900 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
              v-model="localTask.due_date"
            >
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-900 mb-1">Jalon (Milestone)</label>
            <select 
              class="w-full border border-gray-300 rounded-md px-4 py-2.5 text-gray-900 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 bg-white"
              v-model="localTask.milestone_id"
            >
              <option :value="null">Sélectionner un jalon</option>
              <option v-for="m in milestones" :key="m.id" :value="m.id">
                {{ m.title }}
              </option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-900 mb-1">Poids / Effort</label>
            <select 
              class="w-full border border-gray-300 rounded-md px-4 py-2.5 text-gray-900 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 bg-white"
              v-model="localTask.weight"
            >
              <option :value="1">1 (Très facile)</option>
              <option :value="3">3 (Moyen)</option>
              <option :value="5">5 (Complexe)</option>
              <option :value="8">8 (Très complexe)</option>
            </select>
          </div>
        </div>

        <!-- Ligne 3 : Description -->
        <div>
          <div class="mb-1 flex items-center justify-between">
            <label class="block text-sm font-medium text-gray-900">Description (Markdown)</label>
            <div class="inline-flex rounded-md border border-gray-200 bg-gray-50 p-0.5 text-xs">
              <button
                type="button"
                class="rounded px-2 py-1"
                :class="descriptionMode === 'edit' ? 'bg-white text-red-700 shadow-sm' : 'text-gray-600'"
                @click="descriptionMode = 'edit'"
              >
                Edition
              </button>
              <button
                type="button"
                class="rounded px-2 py-1"
                :class="descriptionMode === 'preview' ? 'bg-white text-red-700 shadow-sm' : 'text-gray-600'"
                @click="descriptionMode = 'preview'"
              >
                Apercu
              </button>
            </div>
          </div>

          <textarea
            v-if="descriptionMode === 'edit'"
            class="w-full border border-gray-300 rounded-md px-4 py-3 text-gray-900 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 min-h-30 resize-y"
            v-model="localTask.description"
            placeholder="# Titre\n\n- Point 1\n- Point 2\n\n**Texte important**"
          ></textarea>

          <div
            v-else
            class="markdown-preview rounded-md border border-gray-200 bg-gray-50 px-4 py-3 text-gray-800 min-h-30"
            v-html="renderedDescription"
          />

          <p class="mt-1 text-xs text-gray-500">
            Astuce: utilise #, ##, -, **gras**, *italique*, [lien](https://...).
          </p>
        </div>

        <!-- Ligne 4 : Métadonnées -->
        <div>
          <label class="block text-sm font-medium text-gray-900 mb-1">Métadonnées (Format JSON)</label>
          <textarea 
            class="w-full border border-gray-300 rounded-md px-4 py-3 text-gray-600 font-mono text-sm bg-gray-50 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 min-h-25"
            v-model="localTask.task_metadata"
            placeholder='{ "cle": "valeur" }'
          ></textarea>
        </div>

        <!-- Ligne 5 : Documents (Setup MinIO) -->
        <div>
          <label class="block text-sm font-medium text-gray-900 mb-2">Documents joints</label>

          <p v-if="documentError" class="mb-2 text-xs text-red-600">{{ documentError }}</p>

          <div v-if="loadingTaskDocuments" class="mb-3 text-xs text-gray-500">
            Chargement des documents existants...
          </div>

          <ul v-else-if="taskDocuments.length > 0" class="mb-3 border border-gray-200 rounded-md divide-y divide-gray-200 bg-white">
            <li
              v-for="doc in taskDocuments"
              :key="doc.id"
              class="pl-3 pr-4 py-3 flex items-center justify-between text-sm"
            >
              <button
                type="button"
                class="min-w-0 flex-1 text-left truncate text-gray-900 hover:text-red-600"
                :disabled="documentActionId === doc.id"
                @click="downloadTaskDocument(doc)"
                :title="`Télécharger ${doc.file_name}`"
              >
                {{ doc.file_name }}
              </button>
              <button
                type="button"
                class="ml-4 shrink-0 font-medium text-red-600 hover:text-red-500 disabled:text-gray-400"
                :disabled="documentActionId === doc.id"
                @click="deleteTaskDocument(doc)"
              >
                {{ documentActionId === doc.id ? '...' : 'Supprimer' }}
              </button>
            </li>
          </ul>
          
          <!-- Zone de dépôt -->
          <div 
            class="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-dashed rounded-md transition-colors group"
            :class="isDragging ? 'border-red-500 bg-red-50' : 'border-gray-300 hover:border-red-400 bg-gray-50'"
            @dragover.prevent="onDragOver"
            @dragleave.prevent="onDragLeave"
            @drop.prevent="onDrop"
          >
            <div class="space-y-1 text-center pointer-events-none">
              <svg 
                class="mx-auto h-12 w-12 transition-colors" 
                :class="isDragging ? 'text-red-500' : 'text-gray-400 group-hover:text-red-500'"
                stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true"
              >
                <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <div class="flex text-sm text-gray-600 justify-center pointer-events-auto">
                <label for="file-upload" class="relative cursor-pointer rounded-md font-medium text-red-600 hover:text-red-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-red-500">
                  <span>Téléverser un fichier</span>
                  <input id="file-upload" name="file-upload" type="file" multiple class="sr-only" @change="handleFileUpload">
                </label>
                <p class="pl-1">ou glisser-déposer</p>
              </div>
              <p class="text-xs text-gray-500">PDF, PNG, JPG, DOCX</p>
            </div>
          </div>

          <!-- Liste des fichiers sélectionnés -->
          <ul v-if="uploadedFiles.length > 0" class="mt-4 border border-gray-200 rounded-md divide-y divide-gray-200">
            <li v-for="(file, index) in uploadedFiles" :key="index" class="pl-3 pr-4 py-3 flex items-center justify-between text-sm">
              <div class="w-0 flex-1 flex items-center">
                <span class="ml-2 flex-1 w-0 truncate text-gray-900">{{ file.name }}</span>
              </div>
              <div class="ml-4 shrink-0">
                <button @click="removeFile(index)" class="font-medium text-red-600 hover:text-red-500">Retirer</button>
              </div>
            </li>
          </ul>
        </div>

      </div>

      <!-- Pied de page (Boutons) -->
      <div class="px-6 py-4 bg-gray-50 border-t border-gray-100 flex justify-end gap-3">
        <button
          class="px-5 py-2.5 bg-white border border-gray-300 text-gray-700 font-medium rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
          @click="emit('close')"
        >
          Annuler
        </button>
        <button
          class="px-5 py-2.5 bg-red-600 text-white font-medium rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 shadow-sm transition-colors"
          @click="handleSave"
        >
          Enregistrer les modifications
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.markdown-preview {
  line-height: 1.6;
}

.markdown-preview :deep(h1) {
  margin: 0.2rem 0 0.8rem;
  font-size: 1.5rem;
  line-height: 1.2;
  font-weight: 700;
}

.markdown-preview :deep(h2) {
  margin: 1rem 0 0.65rem;
  font-size: 1.25rem;
  line-height: 1.25;
  font-weight: 700;
}

.markdown-preview :deep(h3) {
  margin: 0.9rem 0 0.55rem;
  font-size: 1.1rem;
  line-height: 1.3;
  font-weight: 600;
}

.markdown-preview :deep(p) {
  margin: 0.5rem 0;
  font-size: 0.95rem;
}

.markdown-preview :deep(ul),
.markdown-preview :deep(ol) {
  margin: 0.5rem 0 0.75rem 1.2rem;
}

.markdown-preview :deep(li) {
  margin: 0.2rem 0;
}

.markdown-preview :deep(ul) {
  list-style: disc;
}

.markdown-preview :deep(ol) {
  list-style: decimal;
}

.markdown-preview :deep(strong) {
  font-weight: 700;
}

.markdown-preview :deep(em) {
  font-style: italic;
}

.markdown-preview :deep(a) {
  color: #b91c1c;
  text-decoration: underline;
}

.markdown-preview :deep(blockquote) {
  margin: 0.7rem 0;
  border-left: 3px solid #fecaca;
  padding-left: 0.75rem;
  color: #4b5563;
}

.markdown-preview :deep(code) {
  border-radius: 0.3rem;
  background: #f3f4f6;
  padding: 0.08rem 0.32rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, Courier New, monospace;
  font-size: 0.85rem;
}

.markdown-preview :deep(pre) {
  overflow-x: auto;
  margin: 0.75rem 0;
  border-radius: 0.45rem;
  background: #111827;
  padding: 0.75rem;
}

.markdown-preview :deep(pre code) {
  background: transparent;
  color: #f9fafb;
  padding: 0;
}
</style>