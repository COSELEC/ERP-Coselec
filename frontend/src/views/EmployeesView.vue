<template>
  <AppLayout>
    <div class="w-full space-y-4 pb-20">
      <h1 class="text-xl sm:text-xl font-bold text-[#b30c27] flex items-center gap-2">
        <span class="material-symbols-outlined">badge</span>
        <span>Gestion des employés</span>
      </h1>
      <button
        v-if="canCreateEmployee"
        @click="openCreateModal"
        class="bg-[#d10f2f] w-max text-white px-4 py-2 rounded-xl hover:bg-[#97091f] shadow-[0_10px_30px_rgba(209,15,47,0.28)] transition flex items-center gap-2 mb-2"
      >
        <span class="material-symbols-outlined">person_add</span>
        <span>Ajouter un employé</span>
      </button>

      <div class="bg-white rounded-2xl shadow-[0_15px_40px_rgba(127,7,28,0.10)] border border-red-100 overflow-x-auto">
        <AppTable 
          :columns="tableColumns" 
          :items="sortedEmployees" 
          emptyMessage="Aucun employé trouvé."
          @rowClick="openEmployeeDetails"
        >
          <template #matricule="{ item }">
            <span class="text-gray-600 font-medium">
              {{ item.matricule || 'EMP' + String(item.id).padStart(3, "0") }}
            </span>
          </template>
          
          <template #first_name="{ item }">
            <div class="flex items-center gap-3">
              <UserAvatar :user="item" size="md" />
              <div>
                <p class="font-medium text-gray-900 flex items-center gap-2">
                  {{ item.first_name || 'Inconnu' }} {{ item.last_name || '' }}
                  <span v-if="item.has_expiring_documents" class="material-symbols-outlined text-orange-500 text-[16px]" title="Documents expirés ou expirant bientôt">warning</span>
                </p>
                <p class="text-xs text-gray-500">
                  {{ item.email }}
                </p>
              </div>
            </div>
          </template>
          
          <template #email="{ item }">
            <span class="text-gray-500">{{ item.email }}</span>
          </template>
          
          <template #position="{ item }">
            <span class="text-gray-700">{{ item.position }}</span>
          </template>
          
          <template #status="{ item }">
            <span :class="[getStatusClass(item.status), 'px-3 py-1 rounded-full text-xs font-medium uppercase']">
              {{ item.status }}
            </span>
          </template>
        </AppTable>
      </div>

      <!-- Modal Nouvel Employé -->
      <div v-if="showCreateModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[100] p-4">
        <div class="bg-white rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl">
          <div class="px-6 py-4 bg-[#b30c27] text-white flex justify-between items-center">
            <h2 class="text-xl font-bold flex items-center gap-2">
              <span class="material-symbols-outlined">person_add</span>
              Nouvel Employé
            </h2>
            <button @click="showCreateModal = false" class="hover:bg-[#d10f2f] p-1 rounded-full transition">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          
          <form @submit.prevent="submitEmployee" class="p-4 space-y-4 max-h-[80vh] overflow-y-auto">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Prénom</label>
                <input type="text" v-model="form.first_name" required class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Nom</label>
                <input type="text" v-model="form.last_name" required class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input type="email" v-model="form.email" required class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Téléphone</label>
                <input type="text" v-model="form.phone" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Matricule</label>
                <input type="text" v-model="form.matricule" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Poste(s)</label>
                <div class="w-full bg-gray-50 border border-gray-200 rounded-xl p-2 flex flex-wrap gap-2 focus-within:ring-2 focus-within:ring-red-500 focus-within:border-red-500 transition min-h-[42px]">
                  <div v-for="(pos, idx) in formPositions" :key="idx" class="flex items-center gap-1 bg-white border border-gray-200 px-2 py-1 rounded-lg text-sm text-gray-700 shadow-sm">
                    {{ pos }}
                    <button type="button" @click="removeFormPosition(idx)" class="text-gray-400 hover:text-red-500 flex items-center justify-center">
                      <span class="material-symbols-outlined text-[14px]">close</span>
                    </button>
                  </div>
                  <input 
                    type="text" 
                    v-model="newPositionTag" 
                    @keydown.enter.prevent="addFormPosition" 
                    placeholder="Taper et appuyer sur Entrée..." 
                    class="flex-1 min-w-[120px] bg-transparent border-none focus:ring-0 px-2 py-1 text-sm outline-none" 
                  />
                </div>
              </div>
              <div class="col-span-1 md:col-span-2 pt-2 mt-2 border-t border-gray-100">
                <h4 class="text-sm font-bold text-gray-900 mb-4">Contact d'urgence</h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Nom du contact</label>
                    <input type="text" v-model="form.emergency_contact_name" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Téléphone d'urgence</label>
                    <input type="text" v-model="form.emergency_contact_phone" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
                  </div>
                </div>
              </div>
              <div class="col-span-1 md:col-span-2">
                <label class="block text-sm font-medium text-gray-700 mb-1">Direction / Service</label>
                <select v-model="form.department_id" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition">
                  <option value="">-- Aucun --</option>
                  <option v-for="dep in departments" :key="dep.id" :value="dep.id">{{ dep.name }}</option>
                </select>
              </div>
              <div class="col-span-1 md:col-span-2">
                <label class="block text-sm font-medium text-gray-700 mb-1">Statut</label>
                <select v-model="form.status" required class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition">
                  <option value="CDI">CDI</option>
                  <option value="CDD">CDD</option>
                  <option value="STAGIAIRE">Stagiaire</option>
                  <option value="PRESTATAIRE">Prestataire</option>
                  <option value="INACTIF">Inactif</option>
                </select>
              </div>
            </div>
            <div class="mt-8 flex justify-end gap-3 pt-4 border-t">
              <button type="button" @click="showCreateModal = false" class="px-6 py-2 text-gray-700 hover:bg-gray-100 rounded-xl transition">Annuler</button>
              <button type="submit" class="px-6 py-2 bg-[#d10f2f] text-white hover:bg-[#97091f] rounded-xl shadow-lg transition">Créer</button>
            </div>
          </form>
        </div>
      </div>

      <!-- Modal Modifier l'Employé -->
      <div v-if="showEditModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[100] p-4">
        <div class="bg-white rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl">
          <div class="px-6 py-4 bg-[#b30c27] text-white flex justify-between items-center">
            <h2 class="text-xl font-bold flex items-center gap-2">
              <span class="material-symbols-outlined">edit</span>
              Modifier l'Employé
            </h2>
            <button @click="showEditModal = false" class="hover:bg-[#d10f2f] p-1 rounded-full transition">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          
          <form @submit.prevent="submitEditEmployee" class="p-4 space-y-4 max-h-[80vh] overflow-y-auto">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Prénom</label>
                <input type="text" v-model="editForm.first_name" required class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Nom</label>
                <input type="text" v-model="editForm.last_name" required class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input type="email" v-model="editForm.email" required class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Téléphone</label>
                <input type="text" v-model="editForm.phone" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Matricule</label>
                <input type="text" v-model="editForm.matricule" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Poste(s)</label>
                <div class="w-full bg-gray-50 border border-gray-200 rounded-xl p-2 flex flex-wrap gap-2 focus-within:ring-2 focus-within:ring-red-500 focus-within:border-red-500 transition min-h-[42px]">
                  <div v-for="(pos, idx) in editFormPositions" :key="idx" class="flex items-center gap-1 bg-white border border-gray-200 px-2 py-1 rounded-lg text-sm text-gray-700 shadow-sm">
                    {{ pos }}
                    <button type="button" @click="removeEditPosition(idx)" class="text-gray-400 hover:text-red-500 flex items-center justify-center">
                      <span class="material-symbols-outlined text-[14px]">close</span>
                    </button>
                  </div>
                  <input 
                    type="text" 
                    v-model="editPositionTag" 
                    @keydown.enter.prevent="addEditPosition" 
                    placeholder="Taper et appuyer sur Entrée..." 
                    class="flex-1 min-w-[120px] bg-transparent border-none focus:ring-0 px-2 py-1 text-sm outline-none" 
                  />
                </div>
              </div>
              <div class="col-span-1 md:col-span-2 pt-2 mt-2 border-t border-gray-100">
                <h4 class="text-sm font-bold text-gray-900 mb-4">Contact d'urgence</h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Nom du contact</label>
                    <input type="text" v-model="editForm.emergency_contact_name" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Téléphone d'urgence</label>
                    <input type="text" v-model="editForm.emergency_contact_phone" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition" />
                  </div>
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Direction / Service</label>
                <select v-model="editForm.department_id" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition">
                  <option value="">-- Aucun --</option>
                  <option v-for="dep in departments" :key="dep.id" :value="dep.id">{{ dep.name }}</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Statut</label>
                <select v-model="editForm.status" required class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition">
                  <option value="CDI">CDI</option>
                  <option value="CDD">CDD</option>
                  <option value="STAGIAIRE">Stagiaire</option>
                  <option value="PRESTATAIRE">Prestataire</option>
                  <option value="INACTIF">Inactif</option>
                </select>
              </div>
              <div class="col-span-1 md:col-span-2">
                <label class="block text-sm font-medium text-gray-700 mb-1">Supérieur hiérarchique (Manager)</label>
                <select v-model="editForm.manager_id" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 transition">
                  <option value="">-- Aucun --</option>
                  <option v-for="emp in availableManagers" :key="emp.id" :value="emp.id">{{ emp.first_name }} {{ emp.last_name }} - {{ emp.position }}</option>
                </select>
              </div>

              <div class="col-span-1 md:col-span-2 flex items-center gap-3 pt-2">
                <input type="checkbox" id="edit_is_active" v-model="editForm.is_active" class="w-4 h-4 text-red-600 rounded border-gray-300 focus:ring-red-500" />
                <label for="edit_is_active" class="text-sm font-medium text-gray-700">Compte employé actif</label>
              </div>
              <!-- Changer de photo directement dans le formulaire -->
              <div class="col-span-1 md:col-span-2 pt-2">
                <label class="block text-sm font-medium text-gray-700 mb-2">Changer de photo</label>
                <div class="flex items-center gap-4">
                  <div class="relative">
                    <div v-if="editPhotoPreview || editForm.id" class="w-16 h-16 rounded-full overflow-hidden border-2 border-red-200 bg-gray-100 flex items-center justify-center">
                      <img v-if="editPhotoPreview" :src="editPhotoPreview" class="w-full h-full object-cover" />
                      <span v-else class="material-symbols-outlined text-gray-400 text-3xl">person</span>
                    </div>
                  </div>
                  <label class="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-red-50 hover:text-red-700 text-gray-700 rounded-xl cursor-pointer transition border border-gray-200 hover:border-red-200">
                    <span class="material-symbols-outlined text-sm">photo_camera</span>
                    <span class="text-sm font-medium">Choisir une photo</span>
                    <input type="file" class="hidden" accept="image/*" @change="handleEditPhotoChange" />
                  </label>
                  <span v-if="editPhotoPreview" class="text-xs text-green-600 font-medium">✓ Photo sélectionnée</span>
                </div>
              </div>
            </div>
            <div class="mt-8 flex justify-end gap-3 pt-4 border-t">
              <button type="button" @click="showEditModal = false" class="px-6 py-2 text-gray-700 hover:bg-gray-100 rounded-xl transition">Annuler</button>
              <button type="submit" :disabled="isSubmittingEdit" class="px-6 py-2 bg-[#d10f2f] text-white hover:bg-[#97091f] rounded-xl shadow-lg transition flex items-center gap-2 disabled:opacity-50">
                <span v-if="isSubmittingEdit" class="material-symbols-outlined animate-spin text-sm">progress_activity</span>
                <span>{{ isSubmittingEdit ? 'Enregistrement...' : 'Enregistrer' }}</span>
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Volet de détails de l'employé (Slide-over) -->
      <div v-if="isSlideOverOpen" @click="closeSlideOver" class="fixed inset-0 bg-[#7f071c]/25 z-40 transition-opacity backdrop-blur-sm"></div>
      <div class="fixed inset-y-0 right-0 z-50 w-full max-w-3xl bg-gradient-to-b from-red-50 to-white shadow-2xl transform transition-transform duration-300 ease-in-out flex flex-col border-l border-red-100" :class="isSlideOverOpen ? 'translate-x-0' : 'translate-x-full'">
        <div v-if="selectedEmployee" class="px-6 py-6 bg-white border-b border-red-100 flex justify-between items-start shadow-sm z-10">
          <div class="flex items-center gap-4">
            <div class="relative group">
              <UserAvatar :user="selectedEmployee" size="lg" />
              <label v-if="canUpdateEmployee" class="absolute inset-0 bg-black/40 rounded-full opacity-0 group-hover:opacity-100 flex items-center justify-center cursor-pointer transition text-white" title="Modifier la photo">
                <span class="material-symbols-outlined text-sm">photo_camera</span>
                <input type="file" class="hidden" accept="image/*" @change="handleDrawerPhotoUpload" />
              </label>
            </div>
            <div>
              <h2 class="text-xl font-bold text-gray-900 flex items-center gap-2">
                <span class="material-symbols-outlined text-[#d10f2f]">account_circle</span>
                <span>{{ selectedEmployee.first_name }} {{ selectedEmployee.last_name }}</span>
              </h2>
              <div class="flex items-center gap-2 mt-1">
                <span class="text-sm text-gray-500 font-medium">{{ selectedEmployee.position }}</span>
                <span class="text-gray-300">•</span>
                <span :class="[getStatusClass(selectedEmployee.status), 'px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider']">
                  {{ selectedEmployee.status }}
                </span>
              </div>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button v-if="canUpdateEmployee" @click="openEditModal(selectedEmployee)" class="p-2 text-[#b30c27] hover:text-white hover:bg-[#b30c27] rounded-lg transition flex items-center justify-center border border-red-200" title="Modifier cet employé">
              <span class="material-symbols-outlined">edit</span>
            </button>
            <button v-if="canDeleteEmployee" @click="confirmDeleteEmployee" class="p-2 text-red-500 hover:text-white hover:bg-red-500 rounded-lg transition flex items-center justify-center border border-red-200" title="Supprimer cet employé">
              <span class="material-symbols-outlined">delete</span>
            </button>
            <button @click="closeSlideOver" class="p-2 text-[#b94a5d] hover:text-[#7f071c] hover:bg-red-100 rounded-full transition">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
        </div>

        <div v-if="selectedEmployee" class="flex-1 overflow-y-auto p-4 space-y-8">
          <section class="bg-white p-5 rounded-xl border border-red-100 shadow-sm">
            <h3 class="text-sm font-bold text-[#7f071c] uppercase tracking-wider mb-4 border-b border-red-100 pb-2 flex items-center gap-2">
              <span class="material-symbols-outlined text-base">info</span>
              <span>Informations Générales</span>
            </h3>
            <div class="grid grid-cols-2 gap-4">
              <div><p class="text-xs text-gray-500 uppercase">Matricule</p><p class="font-medium text-gray-900">{{ selectedEmployee.matricule || 'Non défini' }}</p></div>
              <div><p class="text-xs text-gray-500 uppercase">Email professionnel</p><p class="font-medium text-gray-900">{{ selectedEmployee.email }}</p></div>
              <div><p class="text-xs text-gray-500 uppercase">Téléphone</p><p class="font-medium text-gray-900">{{ selectedEmployee.phone || 'Non renseigné' }}</p></div>
              <div><p class="text-xs text-gray-500 uppercase">Direction / Service</p><p class="font-medium text-gray-900">{{ getDepartmentName(selectedEmployee.department_id) }}</p></div>
              <div><p class="text-xs text-gray-500 uppercase">Manager</p><p class="font-medium text-gray-900">{{ getManagerName(selectedEmployee.manager_id) }}</p></div>
              <div><p class="text-xs text-gray-500 uppercase">Compte</p><p class="font-medium text-gray-900"><span :class="selectedEmployee.is_active !== false ? 'text-emerald-600' : 'text-rose-600'">{{ selectedEmployee.is_active !== false ? 'Actif' : 'Inactif' }}</span></p></div>
              <div class="col-span-2 pt-2 border-t border-gray-100">
                <p class="text-xs text-gray-500 uppercase mb-1">Contact d'urgence</p>
                <p class="font-medium text-gray-900">
                  <span v-if="selectedEmployee.emergency_contact_name || selectedEmployee.emergency_contact_phone">
                    {{ selectedEmployee.emergency_contact_name || 'Nom non défini' }} — {{ selectedEmployee.emergency_contact_phone || 'Téléphone non défini' }}
                  </span>
                  <span v-else class="text-gray-400 italic">Non défini</span>
                </p>
              </div>
            </div>
          </section>

          <section class="bg-white p-5 rounded-xl border border-red-100 shadow-sm">
            <h3 class="text-sm font-bold text-[#7f071c] uppercase tracking-wider mb-4 border-b border-red-100 pb-2 flex items-center gap-2">
              <span class="material-symbols-outlined text-base">work_outline</span>
              <span>Fiche de Poste</span>
              <label 
                v-if="canUpdateEmployee"
                class="ml-auto text-[10px] font-semibold text-[#b30c27] hover:text-white hover:bg-[#b30c27] border border-red-200 px-2 py-0.5 rounded-lg transition cursor-pointer"
              >
                Importer PDF
                <input type="file" class="hidden" accept="application/pdf" @change="handleJobDescUpload" />
              </label>
            </h3>
            <div v-if="selectedEmployee.job_description" class="mt-4">
              <iframe :src="selectedEmployee.job_description" class="w-full h-[500px] border rounded-lg shadow-inner"></iframe>
              <div class="mt-2 text-right">
                <a :href="selectedEmployee.job_description" target="_blank" class="text-sm text-blue-600 hover:underline inline-flex items-center gap-1">
                  <span class="material-symbols-outlined text-[16px]">open_in_new</span>
                  Ouvrir dans un nouvel onglet
                </a>
              </div>
            </div>
            <p v-else class="text-sm text-gray-400 italic">Aucune fiche de poste définie pour cet employé.</p>
          </section>

          <section class="bg-white p-5 rounded-xl border border-red-100 shadow-sm">
            <h3 class="text-sm font-bold text-[#7f071c] uppercase tracking-wider mb-4 border-b border-red-100 pb-2 flex items-center gap-2">
              <span class="material-symbols-outlined text-base">contract</span>
              <span>Contrats</span>
            </h3>
            <EmployeeContracts :employeeId="selectedEmployee.id" />
          </section>

          <section class="bg-white p-5 rounded-xl border border-red-100 shadow-sm">
            <h3 class="text-sm font-bold text-[#7f071c] uppercase tracking-wider mb-4 border-b border-red-100 pb-2 flex items-center gap-2">
              <span class="material-symbols-outlined text-base">folder_shared</span>
              <span>Documents</span>
            </h3>
            <EmployeeDocuments :employeeId="selectedEmployee.id" />
          </section>

          <section class="bg-white p-5 rounded-xl border border-red-100 shadow-sm">
            <h3 class="text-sm font-bold text-[#7f071c] uppercase tracking-wider mb-4 border-b border-red-100 pb-2 flex items-center gap-2">
              <span class="material-symbols-outlined text-base">event_available</span>
              <span>Congés</span>
            </h3>
            <EmployeeLeaves :employeeId="selectedEmployee.id" />
          </section>

          <section class="bg-white p-5 rounded-xl border border-red-100 shadow-sm">
            <h3 class="text-sm font-bold text-[#7f071c] uppercase tracking-wider mb-4 border-b border-red-100 pb-2 flex items-center gap-2">
              <span class="material-symbols-outlined text-base">business_center</span>
              <span>Projets Assignés</span>
            </h3>
            <EmployeeProjects :employeeId="selectedEmployee.id" />
          </section>
        </div>
      </div>
    </div>
  </AppLayout>


</template>

<script setup lang="ts">
import { onMounted, ref, computed } from "vue";
import AppLayout from "@/layouts/AppLayout.vue";
import AppTable from "@/components/common/AppTable.vue";
import { employeeService } from "@/services/employees";
import { api } from "@/services/api";
import { getStoredProfile, hasPermission } from '@/services/session';
import { useToast, useStatusBadges, useTableSort } from '@/composables';

const toast = useToast();
const profile = getStoredProfile();
const permissions = computed(() => profile?.permissions || []);

const canCreateEmployee = computed(() => hasPermission(permissions.value, ['employees.create']));
const canUpdateEmployee = computed(() => hasPermission(permissions.value, ['employees.update']));
const canDeleteEmployee = computed(() => hasPermission(permissions.value, ['employees.delete']));

const { getStatusBadgeClass: getStatusClass } = useStatusBadges();

const tableColumns = [
  { key: 'matricule', label: 'Matricule' },
  { key: 'first_name', label: 'Employé' },
  { key: 'email', label: 'Email' },
  { key: 'position', label: 'Poste' },
  { key: 'status', label: 'Statut' },
];

import EmployeeContracts from "@/components/employees/EmployeeContracts.vue";
import EmployeeDocuments from "@/components/employees/EmployeeDocuments.vue";
import EmployeeLeaves from "@/components/employees/EmployeeLeaves.vue";
import EmployeeProjects from "@/components/employees/EmployeeProjects.vue";
import UserAvatar from "@/components/common/UserAvatar.vue";

interface Employee {
  id: number;
  matricule: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  position: string;
  status: string;
  department_id?: number | null;
  manager_id?: number | null;
  supervised_employee_ids?: number[];
  is_active?: boolean;
  has_expiring_documents?: boolean;
  photo_url?: string | null;
  signature_url?: string | null;
  job_description?: string | null;
  emergency_contact_name?: string | null;
  emergency_contact_phone?: string | null;
}

const showCreateModal = ref(false);
const showEditModal = ref(false);
const isSubmittingEdit = ref(false);
const editPhotoPreview = ref<string | null>(null);
const editPhotoFile = ref<File | null>(null);

// Fiche de poste modal
const showJobDescModal = ref(false);
const jobDescDraft = ref('');

// Upload Fiche de Poste PDF
const handleJobDescUpload = async (e: Event) => {
  const target = e.target as HTMLInputElement;
  if (!target.files || !target.files[0] || !selectedEmployee.value) return;
  const file = target.files[0];
  const formData = new FormData();
  formData.append('file', file);
  try {
    const res = await api.post(`/employees/${selectedEmployee.value.id}/job_description`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    selectedEmployee.value.job_description = res.data.job_description_url;
    const empInList = employees.value.find(emp => emp.id === selectedEmployee.value?.id) as any;
    if (empInList) {
      empInList.job_description = res.data.job_description_url;
    }
    toast.success("Fiche de poste importée avec succès !");
  } catch (error) {
    console.error("Erreur lors de l'import de la fiche de poste", error);
    toast.error("Impossible d'importer le document.");
  } finally {
    target.value = '';
  }
};

const handleEditPhotoChange = (e: Event) => {
  const target = e.target as HTMLInputElement;
  if (!target.files || !target.files[0]) return;
  editPhotoFile.value = target.files[0];
  editPhotoPreview.value = URL.createObjectURL(target.files[0]);
};

const employees = ref<Employee[]>([]);
const departments = ref<any[]>([]);

const fetchDepartments = async () => {
  try {
    const res = await api.get('/departments');
    departments.value = res.data;
  } catch (e) {
    console.error("Error fetching departments", e);
  }
};

const getDepartmentName = (deptId?: number | null) => {
  if (!deptId) return 'Non défini';
  const dep = departments.value.find(d => d.id === deptId);
  return dep ? dep.name : 'Non défini';
};

const getManagerName = (managerId?: number | null) => {
  if (!managerId) return 'Aucun';
  const manager = employees.value.find(emp => emp.id === managerId);
  return manager ? `${manager.first_name || ''} ${manager.last_name || ''}`.trim() : 'Inconnu';
};

const openCreateModal = () => {
  fetchDepartments();
  showCreateModal.value = true;
};

const { sortColumn, sortOrder, sortBy, sortedItems: sortedEmployees } = useTableSort(employees, '', 'asc');

const form = ref({
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  matricule: '',
  position: '',
  department_id: '',
  manager_id: '',
  status: 'CDI',
  supervised_employee_ids: [] as number[],
  emergency_contact_name: '',
  emergency_contact_phone: ''
});

const editForm = ref({
  id: 0,
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  matricule: '',
  position: '',
  department_id: '' as string | number,
  manager_id: '' as string | number,
  status: 'CDI',
  supervised_employee_ids: [] as number[],
  is_active: true,
  emergency_contact_name: '',
  emergency_contact_phone: ''
});

const availableManagers = computed(() => {
  if (!editForm.value.id) return employees.value;
  return employees.value.filter(emp => emp.id !== editForm.value.id);
});

const availableSubordinates = computed(() => {
  if (!editForm.value.id) return employees.value;
  return employees.value.filter(emp => emp.id !== editForm.value.id);
});

const formPositions = ref<string[]>([]);
const editFormPositions = ref<string[]>([]);
const newPositionTag = ref('');
const editPositionTag = ref('');

const addFormPosition = () => {
  if (newPositionTag.value.trim()) {
    formPositions.value.push(newPositionTag.value.trim());
    newPositionTag.value = '';
    form.value.position = formPositions.value.join(', ');
  }
};
const removeFormPosition = (index: number) => {
  formPositions.value.splice(index, 1);
  form.value.position = formPositions.value.join(', ');
};

const addEditPosition = () => {
  if (editPositionTag.value.trim()) {
    editFormPositions.value.push(editPositionTag.value.trim());
    editPositionTag.value = '';
    editForm.value.position = editFormPositions.value.join(', ');
  }
};
const removeEditPosition = (index: number) => {
  editFormPositions.value.splice(index, 1);
  editForm.value.position = editFormPositions.value.join(', ');
};

const openEditModal = async (employee: Employee) => {
  await fetchDepartments();
  
  try {
    const res = await employeeService.getEmployee(employee.id);
    const fullEmp = res.data;
    
    // Set editForm positions
    editFormPositions.value = fullEmp.position ? fullEmp.position.split(',').map((p: string) => p.trim()).filter(Boolean) : [];
    
    editForm.value = {
      id: fullEmp.id,
      first_name: fullEmp.first_name || '',
      last_name: fullEmp.last_name || '',
      email: fullEmp.email || '',
      phone: fullEmp.phone || '',
      matricule: fullEmp.matricule || '',
      position: fullEmp.position || '',
      department_id: fullEmp.department_id ?? '',
      manager_id: fullEmp.manager_id ?? '',
      status: fullEmp.status || 'CDI',
      supervised_employee_ids: fullEmp.supervised_employee_ids || [],
      is_active: fullEmp.is_active ?? true,
      emergency_contact_name: fullEmp.emergency_contact_name || '',
      emergency_contact_phone: fullEmp.emergency_contact_phone || ''
    };
    editPhotoPreview.value = fullEmp.photo_url || null;
    editPhotoFile.value = null;
    showEditModal.value = true;
  } catch (e) {
    console.error("Failed to fetch full employee details", e);
    // Fallback
    editFormPositions.value = employee.position ? employee.position.split(',').map((p: string) => p.trim()).filter(Boolean) : [];
    
    editForm.value = {
      id: employee.id,
      first_name: employee.first_name || '',
      last_name: employee.last_name || '',
      email: employee.email || '',
      phone: employee.phone || '',
      matricule: employee.matricule || '',
      position: employee.position || '',
      department_id: employee.department_id ?? '',
      manager_id: employee.manager_id ?? '',
      status: employee.status || 'CDI',
      supervised_employee_ids: employee.supervised_employee_ids || [],
      is_active: employee.is_active ?? true,
      emergency_contact_name: employee.emergency_contact_name || '',
      emergency_contact_phone: employee.emergency_contact_phone || ''
    };
    editPhotoPreview.value = employee.photo_url || null;
    editPhotoFile.value = null;
    showEditModal.value = true;
  }
};

const handleDrawerPhotoUpload = async (e: Event) => {
  const target = e.target as HTMLInputElement;
  if (!target.files || !target.files[0] || !selectedEmployee.value) return;
  const file = target.files[0];
  const formData = new FormData();
  formData.append('file', file);
  try {
    const res = await api.post(`/employees/${selectedEmployee.value.id}/photo`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    selectedEmployee.value.photo_url = res.data.photo_url;
    const empInList = employees.value.find(emp => emp.id === selectedEmployee.value?.id);
    if (empInList) {
      empInList.photo_url = res.data.photo_url;
    }
    toast.success("Photo de profil mise à jour !");
  } catch (error) {
    console.error("Erreur lors du téléversement de la photo", error);
    toast.error("Impossible de mettre à jour la photo.");
  } finally {
    target.value = '';
  }
};

async function submitEmployee() {
  if (newPositionTag.value.trim()) addFormPosition();
  try {
    const payload = {
      ...form.value,
      department_id: form.value.department_id ? Number(form.value.department_id) : null,
      manager_id: form.value.manager_id ? Number(form.value.manager_id) : null
    };
    await employeeService.createEmployee(payload);
    toast.success("Employé créé avec succès");
    showCreateModal.value = false;
    form.value = {
      first_name: '',
      last_name: '',
      email: '',
      phone: '',
      matricule: '',
      position: '',
      department_id: '',
      manager_id: '',
      status: 'CDI',
      supervised_employee_ids: [] as number[],
      emergency_contact_name: '',
      emergency_contact_phone: ''
    };
    formPositions.value = [];
    
    await fetchEmployees();
  } catch (e: any) {
    console.error("Error creating employee", e);
    const errorMsg = e.response?.data?.detail || "Erreur lors de la création de l'employé";
    toast.error(errorMsg);
  }
}

async function submitEditEmployee() {
  if (editPositionTag.value.trim()) addEditPosition();
  isSubmittingEdit.value = true;
  try {
    const payload = {
      first_name: editForm.value.first_name,
      last_name: editForm.value.last_name,
      email: editForm.value.email,
      phone: editForm.value.phone,
      matricule: editForm.value.matricule,
      position: editForm.value.position,
      department_id: editForm.value.department_id !== '' && editForm.value.department_id !== null ? Number(editForm.value.department_id) : null,
      manager_id: editForm.value.manager_id !== '' && editForm.value.manager_id !== null ? Number(editForm.value.manager_id) : null,
      status: editForm.value.status,
      supervised_employee_ids: editForm.value.supervised_employee_ids,
      is_active: editForm.value.is_active,
      emergency_contact_name: editForm.value.emergency_contact_name,
      emergency_contact_phone: editForm.value.emergency_contact_phone
    };

    const res = await employeeService.updateEmployee(editForm.value.id, payload);

    // Upload la photo si une nouvelle a été sélectionnée dans le formulaire
    if (editPhotoFile.value) {
      const formDataPhoto = new FormData();
      formDataPhoto.append('file', editPhotoFile.value);
      try {
        const photoRes = await api.post(`/employees/${editForm.value.id}/photo`, formDataPhoto, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        if (selectedEmployee.value && selectedEmployee.value.id === editForm.value.id) {
          (selectedEmployee.value as any).photo_url = photoRes.data.photo_url;
        }
      } catch (photoErr) {
        console.error('Erreur upload photo', photoErr);
      }
      editPhotoFile.value = null;
      editPhotoPreview.value = null;
    }

    toast.success("Employé mis à jour avec succès");
    showEditModal.value = false;

    const response = await employeeService.getAllEmployees();
    employees.value = response.data.filter((e: any) => e.is_employee === true);

    if (selectedEmployee.value && selectedEmployee.value.id === editForm.value.id) {
      selectedEmployee.value = res.data;
    }
  } catch (e: any) {
    console.error("Error updating employee", e);
    const errorMsg = e.response?.data?.detail || "Erreur lors de la modification de l'employé";
    toast.error(errorMsg);
  } finally {
    isSubmittingEdit.value = false;
  }
}

const isSlideOverOpen = ref(false);
const selectedEmployee = ref<Employee | null>(null);

const openEmployeeDetails = (employee: Employee) => {
  selectedEmployee.value = employee;
  setTimeout(() => {
    isSlideOverOpen.value = true;
  }, 10);
};

const closeSlideOver = () => {
  isSlideOverOpen.value = false;
  setTimeout(() => {
    selectedEmployee.value = null;
  }, 300);
};

const confirmDeleteEmployee = async () => {
  if (!selectedEmployee.value) return;
  
  if (!confirm(`Voulez-vous vraiment supprimer l'employé ${selectedEmployee.value.first_name} ${selectedEmployee.value.last_name} ?`)) {
    return;
  }
  
  try {
    await employeeService.deleteEmployee(selectedEmployee.value.id);
    toast.success("Employé supprimé avec succès");
    
    const response = await employeeService.getAllEmployees();
    employees.value = response.data.filter((e: any) => e.is_employee === true);
    
    closeSlideOver();
  } catch (e: any) {
    console.error("Error deleting employee", e);
    const errorMsg = e.response?.data?.detail || "Erreur lors de la suppression de l'employé";
    toast.error(errorMsg);
  }
};

onMounted(async () => {
  try {
    const [empRes, depRes] = await Promise.all([
      employeeService.getAllEmployees(),
      api.get('/departments')
    ]);
    employees.value = empRes.data.filter((e: any) => e.is_employee === true);
    
    departments.value = depRes.data;
  } catch (e) {
    console.error("Error loading data", e);
  }
});
</script>