<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { marked } from 'marked';

const props = defineProps<{
  open: boolean;
  employees?: Array<{
    id: number;
    nom?: string;
    prenom?: string;
    first_name?: string;
    last_name?: string;
  }>;
  milestones?: Array<{
      id: number;
      title: string;
  }>;
  defaultMilestoneId?: number | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'create', value: { payload: any; files: File[] }): void;
}>();

const form = ref({
  title: '',
  description: '',
  start_date: '',
  due_date: '',
  assignee_id: '' as string | number,
  priority: 'Moyenne',
  status: 'A faire',
  milestone_id: '' as string | number,
  weight: 1,
});

const uploadedFiles = ref<File[]>([]);
const errors = ref<string[]>([]);
const descriptionMode = ref<'edit' | 'preview'>('edit');
const showMarkdownHelp = ref(false);
const descriptionTextareaRef = ref<HTMLTextAreaElement | null>(null);

const applyMarkdown = (prefix: string, suffix = '', defaultPlaceholder = '') => {
  const textarea = descriptionTextareaRef.value;
  const currentText = form.value.description || '';

  if (!textarea) {
    form.value.description = currentText + `${prefix}${defaultPlaceholder}${suffix}`;
    return;
  }

  const start = textarea.selectionStart ?? currentText.length;
  const end = textarea.selectionEnd ?? currentText.length;
  const selectedText = currentText.substring(start, end);
  const textToInsert = selectedText || defaultPlaceholder;
  const newContent = `${prefix}${textToInsert}${suffix}`;

  form.value.description =
    currentText.substring(0, start) + newContent + currentText.substring(end);

  setTimeout(() => {
    textarea.focus();
    const newCursorStart = start + prefix.length;
    const newCursorEnd = newCursorStart + textToInsert.length;
    textarea.setSelectionRange(newCursorStart, newCursorEnd);
  }, 0);
};

const employeesList = computed(() => props.employees ?? []);
const renderedDescription = computed(() => marked.parse(form.value.description || '') as string);

const getEmployeeLabel = (emp: {
  id: number;
  nom?: string;
  prenom?: string;
  first_name?: string;
  last_name?: string;
}) => {
  const lastName = emp.nom || emp.last_name || '';
  const firstName = emp.prenom || emp.first_name || '';
  const fullName = `${lastName} ${firstName}`.trim();
  return fullName || `Employe n${emp.id}`;
};

const resetForm = () => {
  form.value = {
    title: '',
    description: '',
    start_date: '',
    due_date: '',
    assignee_id: '',
    priority: 'Moyenne',
    status: 'A faire',
    milestone_id: props.defaultMilestoneId || '',
    weight: 1,
  };
  uploadedFiles.value = [];
  errors.value = [];
  descriptionMode.value = 'edit';
  showMarkdownHelp.value = false;
};

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      resetForm();
    }
  }
);

const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (!target.files) return;
  uploadedFiles.value.push(...Array.from(target.files));
  target.value = '';
};

const removeFile = (index: number) => {
  uploadedFiles.value.splice(index, 1);
};

const validateForm = () => {
  const nextErrors: string[] = [];

  if (!form.value.title.trim()) {
    nextErrors.push('Le nom de la tache est obligatoire.');
  }

  if (!form.value.due_date) {
    nextErrors.push('La date de fin est obligatoire.');
  }

  if (form.value.start_date && form.value.due_date && form.value.start_date > form.value.due_date) {
    nextErrors.push('La date de debut doit etre inferieure ou egale a la date de fin.');
  }

  errors.value = nextErrors;
  return nextErrors.length === 0;
};

const submitTaskCreate = () => {
  if (!validateForm()) {
    return;
  }

  const payload = {
    title: form.value.title.trim(),
    description: form.value.description.trim() || null,
    status: form.value.status,
    priority: form.value.priority,
    due_date: form.value.due_date,
    start_date: form.value.start_date || null,
    assignee_id: form.value.assignee_id === '' ? null : Number(form.value.assignee_id),
    milestone_id: form.value.milestone_id === '' ? null : Number(form.value.milestone_id),
    weight: Number(form.value.weight),
  };

  emit('create', {
    payload,
    files: uploadedFiles.value,
  });
};
</script>

<template>
  <div
    v-if="open"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
    @click.self="emit('close')"
  >
    <div class="w-full max-w-2xl rounded-xl bg-white shadow-2xl">
      <div class="flex items-center justify-between border-b border-gray-100 px-6 py-4">
        <h2 class="text-xl font-bold text-gray-900">
        Nouvelle tâche
      </h2>
        <button
          class="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-gray-700"
          @click="emit('close')"
          type="button"
        >
          <span class="material-symbols-outlined text-xl">close</span>
        </button>
      </div>

      <div class="max-h-[75vh] overflow-y-auto px-6 py-5">
        <div v-if="errors.length" class="mb-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          <p class="font-semibold">Veuillez corriger ces champs:</p>
          <ul class="mt-2 list-disc pl-5">
            <li v-for="error in errors" :key="error">{{ error }}</li>
          </ul>
        </div>

        <div class="space-y-4">
          <div>
            <label class="mb-1 block text-sm font-medium text-gray-800">Nom de la tâche</label>
            <input
              v-model="form.title"
              type="text"
              class="w-full rounded-md border border-gray-300 px-3 py-2.5 text-gray-900 focus:border-red-500 focus:outline-none focus:ring-2 focus:ring-red-500/20"
              placeholder="Ex: Préparer le sprint planning"
            >
          </div>

          <div>
            <div class="mb-2 flex flex-wrap items-center justify-between gap-2">
              <div class="flex items-center gap-2">
                <label class="block text-sm font-medium text-gray-800">Description (Markdown)</label>
                <button
                  type="button"
                  @click="showMarkdownHelp = !showMarkdownHelp"
                  title="Afficher/Masquer le guide Markdown"
                  class="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-xs text-gray-500 hover:bg-gray-100 hover:text-red-600 transition"
                >
                  <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>{{ showMarkdownHelp ? 'Masquer guide' : 'Guide' }}</span>
                </button>
              </div>

              <div class="flex items-center gap-2">
                <!-- Outils rapides (visibles en mode édition) -->
                <div v-if="descriptionMode === 'edit'" class="flex items-center border border-gray-200 rounded-md bg-gray-50 p-0.5 text-xs">
                  <button
                    type="button"
                    @click="applyMarkdown('**', '**', 'texte en gras')"
                    title="Gras (**texte**)"
                    class="rounded px-2 py-1 font-bold text-gray-700 hover:bg-white hover:text-red-700 transition"
                  >
                    B
                  </button>
                  <button
                    type="button"
                    @click="applyMarkdown('*', '*', 'texte en italique')"
                    title="Italique (*texte*)"
                    class="rounded px-2 py-1 italic font-serif text-gray-700 hover:bg-white hover:text-red-700 transition"
                  >
                    I
                  </button>
                  <button
                    type="button"
                    @click="applyMarkdown('### ', '', 'Titre')"
                    title="Titre (### Titre)"
                    class="rounded px-2 py-1 font-bold text-gray-700 hover:bg-white hover:text-red-700 transition"
                  >
                    H
                  </button>
                  <div class="h-3 w-px bg-gray-300 mx-0.5" />
                  <button
                    type="button"
                    @click="applyMarkdown('- ', '', 'Élément')"
                    title="Liste à puces (- élément)"
                    class="rounded px-2 py-1 text-gray-700 hover:bg-white hover:text-red-700 transition"
                  >
                    •
                  </button>
                  <button
                    type="button"
                    @click="applyMarkdown('- [ ] ', '', 'Tâche')"
                    title="Liste de tâches (- [ ] tâche)"
                    class="rounded px-2 py-1 text-gray-700 hover:bg-white hover:text-red-700 transition"
                  >
                    ☑
                  </button>
                  <button
                    type="button"
                    @click="applyMarkdown('[', '](https://...)', 'texte du lien')"
                    title="Lien ([texte](url))"
                    class="rounded px-2 py-1 text-gray-700 hover:bg-white hover:text-red-700 transition"
                  >
                    🔗
                  </button>
                  <button
                    type="button"
                    @click="applyMarkdown('`', '`', 'code')"
                    title="Code (`code`)"
                    class="rounded px-2 py-1 font-mono text-gray-700 hover:bg-white hover:text-red-700 transition"
                  >
                    &lt;/&gt;
                  </button>
                  <button
                    type="button"
                    @click="applyMarkdown('> ', '', 'Citation')"
                    title="Citation (> texte)"
                    class="rounded px-2 py-1 text-gray-700 hover:bg-white hover:text-red-700 transition"
                  >
                    ”
                  </button>
                </div>

                <!-- Switcher Édition / Aperçu -->
                <div class="inline-flex rounded-md border border-gray-200 bg-gray-50 p-0.5 text-xs">
                  <button
                    type="button"
                    class="rounded px-2 py-1 transition"
                    :class="descriptionMode === 'edit' ? 'bg-white text-red-700 shadow-xs font-medium' : 'text-gray-600'"
                    @click="descriptionMode = 'edit'"
                  >
                    Édition
                  </button>
                  <button
                    type="button"
                    class="rounded px-2 py-1 transition"
                    :class="descriptionMode === 'preview' ? 'bg-white text-red-700 shadow-xs font-medium' : 'text-gray-600'"
                    @click="descriptionMode = 'preview'"
                  >
                    Aperçu
                  </button>
                </div>
              </div>
            </div>

            <textarea
              v-if="descriptionMode === 'edit'"
              ref="descriptionTextareaRef"
              v-model="form.description"
              rows="6"
              class="w-full rounded-md border border-gray-300 px-3 py-2.5 font-mono text-sm text-gray-900 focus:border-red-500 focus:outline-none focus:ring-2 focus:ring-red-500/20"
              placeholder="# Titre\n\n- Point 1\n- Point 2\n\n**Texte important**"
            />

            <div
              v-else
              class="markdown-preview rounded-md border border-gray-200 bg-gray-50 px-4 py-3 text-gray-800 min-h-32"
              v-html="renderedDescription"
            />

            <!-- Aide-mémoire interactif dépliable -->
            <div
              v-if="showMarkdownHelp"
              class="mt-2 rounded-md border border-red-100 bg-red-50/40 p-3 text-xs text-gray-700 shadow-xs transition-all"
            >
              <div class="mb-2 font-semibold text-gray-900 flex items-center justify-between">
                <span>Aide-mémoire de mise en page Markdown</span>
                <span class="text-[11px] text-gray-500 font-normal">Cliquez sur les boutons de la barre d'outils pour insérer rapidement</span>
              </div>
              <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono">
                <div class="rounded bg-white p-2 border border-gray-200">
                  <span class="text-red-700"># Titre</span>
                  <p class="font-sans text-[11px] text-gray-500 mt-0.5">Titre principal</p>
                </div>
                <div class="rounded bg-white p-2 border border-gray-200">
                  <span class="text-red-700">**Gras**</span>
                  <p class="font-sans text-[11px] text-gray-500 mt-0.5">Texte en <b>gras</b></p>
                </div>
                <div class="rounded bg-white p-2 border border-gray-200">
                  <span class="text-red-700">*Italique*</span>
                  <p class="font-sans text-[11px] text-gray-500 mt-0.5">Texte en <i>italique</i></p>
                </div>
                <div class="rounded bg-white p-2 border border-gray-200">
                  <span class="text-red-700">- [ ] À faire</span>
                  <p class="font-sans text-[11px] text-gray-500 mt-0.5">Case à cocher</p>
                </div>
                <div class="rounded bg-white p-2 border border-gray-200">
                  <span class="text-red-700">- Liste</span>
                  <p class="font-sans text-[11px] text-gray-500 mt-0.5">Puce non ordonnée</p>
                </div>
                <div class="rounded bg-white p-2 border border-gray-200">
                  <span class="text-red-700">[Titre](url)</span>
                  <p class="font-sans text-[11px] text-gray-500 mt-0.5">Lien hypertexte</p>
                </div>
                <div class="rounded bg-white p-2 border border-gray-200">
                  <span class="text-red-700">`code`</span>
                  <p class="font-sans text-[11px] text-gray-500 mt-0.5">Code en ligne</p>
                </div>
                <div class="rounded bg-white p-2 border border-gray-200">
                  <span class="text-red-700">&gt; Citation</span>
                  <p class="font-sans text-[11px] text-gray-500 mt-0.5">Bloc citation</p>
                </div>
              </div>
            </div>
          </div>

          <div class="grid gap-4 md:grid-cols-2">
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-800">Date de début</label>
              <input
                v-model="form.start_date"
                type="date"
                class="w-full rounded-md border border-gray-300 px-3 py-2.5 text-gray-900 focus:border-red-500 focus:outline-none focus:ring-2 focus:ring-red-500/20"
              >
            </div>

            <div>
              <label class="mb-1 block text-sm font-medium text-gray-800">Date de fin</label>
              <input
                v-model="form.due_date"
                type="date"
                class="w-full rounded-md border border-gray-300 px-3 py-2.5 text-gray-900 focus:border-red-500 focus:outline-none focus:ring-2 focus:ring-red-500/20"
              >
            </div>
          </div>

          <div>
            <label class="mb-1 block text-sm font-medium text-gray-800">Nom de l'assigné</label>
            <select
              v-model="form.assignee_id"
              class="w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-gray-900 focus:border-red-500 focus:outline-none focus:ring-2 focus:ring-red-500/20"
            >
              <option value="">Non assigné</option>
              <option v-for="emp in employeesList" :key="emp.id" :value="emp.id">
                {{ getEmployeeLabel(emp) }}
              </option>
            </select>
          </div>

          <div class="grid gap-4 md:grid-cols-2">
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-800">Jalon (Milestone)</label>
              <select
                v-model="form.milestone_id"
                class="w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-gray-900 focus:border-red-500 focus:outline-none focus:ring-2 focus:ring-red-500/20"
              >
                <option value="">Sélectionner un jalon</option>
                <option v-for="m in milestones" :key="m.id" :value="m.id">
                  {{ m.title }}
                </option>
              </select>
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-800">Poids / Effort</label>
              <select
                v-model="form.weight"
                class="w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-gray-900 focus:border-red-500 focus:outline-none focus:ring-2 focus:ring-red-500/20"
              >
                <option :value="1">1 (Très facile)</option>
                <option :value="3">3 (Moyen)</option>
                <option :value="5">5 (Complexe)</option>
                <option :value="8">8 (Très complexe)</option>
              </select>
            </div>
          </div>

          <div>
            <label class="mb-1 block text-sm font-medium text-gray-800">Documents</label>
            <input
              type="file"
              multiple
              class="w-full rounded-md border border-gray-300 px-3 py-2.5 text-sm text-gray-700 file:mr-3 file:rounded file:border-0 file:bg-red-50 file:px-3 file:py-1.5 file:text-red-700 hover:file:bg-red-100"
              @change="handleFileUpload"
            >

            <ul v-if="uploadedFiles.length" class="mt-3 divide-y divide-gray-100 rounded-md border border-gray-200 bg-gray-50">
              <li v-for="(file, index) in uploadedFiles" :key="`${file.name}-${index}`" class="flex items-center justify-between px-3 py-2 text-sm">
                <span class="truncate text-gray-700">{{ file.name }}</span>
                <button
                  type="button"
                  class="rounded px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50"
                  @click="removeFile(index)"
                >
                  Retirer
                </button>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <div class="flex justify-end gap-3 border-t border-gray-100 px-6 py-4">
        <button
          @click="emit('close')"
          type="button"
          class="rounded border border-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-50"
        >
          Annuler
        </button>
        <button
          @click="submitTaskCreate"
          type="button"
          class="rounded bg-red-500 px-4 py-2 text-white"
        >
          Créer la tâche
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