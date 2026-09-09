<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getStoredProfile } from '@/services/session';
import api from '@/services/api';
import AppLayout from '@/layouts/AppLayout.vue';
import UserAvatar from '@/components/common/UserAvatar.vue';

const profile = ref(getStoredProfile());
const fileInput = ref<HTMLInputElement | null>(null);
const photoInput = ref<HTMLInputElement | null>(null);
const signatureUrl = ref<string | null>(null);
const photoUrl = ref<string | null>(null);
const isUploading = ref(false);
const isUploadingPhoto = ref(false);

onMounted(async () => {
    if (profile.value) {
        try {
            const res = await api.get(`/employees/${profile.value.id}`);
            signatureUrl.value = res.data.signature_url;
            photoUrl.value = res.data.photo_url;
        } catch (error) {
            console.error("Failed to load user profile", error);
        }
    }
});

const triggerPhotoInput = () => {
    photoInput.value?.click();
};

const handlePhotoUpload = async (event: Event) => {
    const target = event.target as HTMLInputElement;
    if (!target.files || target.files.length === 0) return;
    
    const file = target.files[0]!;
    const formData = new FormData();
    formData.append('file', file);
    
    isUploadingPhoto.value = true;
    try {
        const res = await api.post('/me/photo', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        photoUrl.value = res.data.photo_url;
        if (profile.value) {
            profile.value.photo_url = res.data.photo_url;
        }
        window.dispatchEvent(new Event('profile:updated'));
        alert("Photo de profil mise à jour avec succès !");
    } catch (error) {
        console.error("Erreur lors de l'upload de la photo", error);
        alert("Erreur lors de l'upload de la photo de profil.");
    } finally {
        isUploadingPhoto.value = false;
        target.value = '';
    }
};

const handleDeletePhoto = async () => {
    if (!confirm("Voulez-vous vraiment supprimer votre photo de profil ?")) return;
    try {
        await api.delete('/me/photo');
        photoUrl.value = null;
        if (profile.value) {
            profile.value.photo_url = null;
        }
        window.dispatchEvent(new Event('profile:updated'));
    } catch (error) {
        console.error("Erreur lors de la suppression de la photo", error);
        alert("Erreur lors de la suppression de la photo.");
    }
};

const triggerFileInput = () => {
    fileInput.value?.click();
};

const handleFileUpload = async (event: Event) => {
    const target = event.target as HTMLInputElement;
    if (!target.files || target.files.length === 0) return;
    
    const file = target.files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    isUploading.value = true;
    try {
        if (!profile.value) return;
        const res = await api.post(`/employees/${profile.value.id}/signature`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
        signatureUrl.value = res.data.signature_url;
        alert("Signature mise à jour avec succès !");
    } catch (error) {
        console.error("Erreur lors de l'upload de la signature", error);
        alert("Erreur lors de l'upload de la signature.");
    } finally {
        isUploading.value = false;
        target.value = ''; 
    }
};

const passwordForm = ref({
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
});
const isChangingPassword = ref(false);

const handleChangePassword = async () => {
    if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
        alert("Le nouveau mot de passe et la confirmation ne correspondent pas.");
        return;
    }
    if (!profile.value?.email) {
        alert("Erreur: Email introuvable.");
        return;
    }

    isChangingPassword.value = true;
    try {
        await api.post('/change-password', {
            email: profile.value.email,
            old_password: passwordForm.value.oldPassword,
            new_password: passwordForm.value.newPassword
        });
        alert("Mot de passe modifié avec succès !");
        passwordForm.value = { oldPassword: '', newPassword: '', confirmPassword: '' };
    } catch (error: any) {
        console.error("Erreur lors de la modification du mot de passe", error);
        alert(error.response?.data?.detail || "Erreur lors de la modification du mot de passe.");
    } finally {
        isChangingPassword.value = false;
    }
};
</script>

<template>
<AppLayout>
  <div class="p-4 sm:p-6 max-w-4xl mx-auto space-y-6">
    <h1 class="text-3xl font-bold text-gray-900 mb-8">Mon Profil</h1>
    
    <!-- Photo de profil -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div class="p-6">
            <h2 class="text-xl font-semibold mb-2 text-gray-800">Photo de profil</h2>
            <p class="text-sm text-gray-500 mb-6">
                Votre photo apparaîtra sur votre avatar dans la barre de navigation, l'organigramme, la liste des employés et les demandes.
            </p>
            <div class="flex flex-col sm:flex-row items-center sm:items-start gap-6">
                <UserAvatar 
                    :photo-url="photoUrl" 
                    :name="profile?.name || profile?.first_name + ' ' + profile?.last_name" 
                    size="2xl" 
                />
                <div class="flex flex-col gap-3 justify-center text-center sm:text-left">
                    <input type="file" ref="photoInput" class="hidden" accept="image/png,image/jpeg,image/webp,image/jpg" @change="handlePhotoUpload" />
                    <div class="flex flex-wrap gap-2 justify-center sm:justify-start">
                        <button 
                            type="button"
                            @click="triggerPhotoInput" 
                            :disabled="isUploadingPhoto"
                            class="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-xl hover:bg-red-700 transition flex items-center gap-2 shadow-sm disabled:opacity-50"
                        >
                            <span class="material-symbols-outlined text-base">{{ isUploadingPhoto ? 'sync' : 'photo_camera' }}</span>
                            {{ isUploadingPhoto ? 'Téléchargement...' : (photoUrl ? 'Changer la photo' : 'Ajouter une photo') }}
                        </button>
                        <button 
                            v-if="photoUrl"
                            type="button"
                            @click="handleDeletePhoto"
                            class="px-4 py-2 border border-gray-200 text-red-600 hover:bg-red-50 text-sm font-medium rounded-xl transition flex items-center gap-1.5"
                        >
                            <span class="material-symbols-outlined text-base">delete</span>
                            Supprimer
                        </button>
                    </div>
                    <p class="text-xs text-gray-400">Formats supportés : JPG, PNG, WEBP. Poids conseillé max 2Mo.</p>
                </div>
            </div>
        </div>
    </div>

    <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div class="p-6">
            <h2 class="text-xl font-semibold mb-4 text-gray-800">Informations Personnelles</h2>
            <div class="grid grid-cols-2 gap-6">
                <div>
                    <label class="block text-sm font-medium text-gray-500">Nom Complet</label>
                    <div class="mt-1 text-gray-900">{{ profile?.name || profile?.first_name + ' ' + profile?.last_name }}</div>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-500">Email</label>
                    <div class="mt-1 text-gray-900">{{ profile?.email }}</div>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-500">Poste</label>
                    <div class="mt-1 text-gray-900">{{ profile?.position || 'Non spécifié' }}</div>
                </div>
            </div>
        </div>
    </div>

    <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div class="p-6">
            <h2 class="text-xl font-semibold mb-4 text-gray-800">Signature Électronique</h2>
            <p class="text-sm text-gray-500 mb-6">
                Ajoutez votre signature électronique pour l'inclure automatiquement sur les documents générés (Bons de commande, Pièces de caisse, etc.).
            </p>
            
            <div class="flex items-start space-x-8">
                <!-- Aperçu -->
                <div class="flex-shrink-0 w-64 h-32 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center bg-gray-50 overflow-hidden">
                    <img v-if="signatureUrl" :src="'/api/storage/' + signatureUrl" alt="Ma signature" class="max-w-full max-h-full object-contain" />
                    <span v-else class="text-gray-400 text-sm">Aucune signature</span>
                </div>
                
                <!-- Actions -->
                <div class="flex flex-col space-y-4">
                    <input type="file" ref="fileInput" class="hidden" accept="image/*" @change="handleFileUpload" />
                    <button 
                        @click="triggerFileInput"
                        :disabled="isUploading"
                        class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center shadow-sm"
                    >
                        <span class="material-symbols-outlined mr-2 text-sm">{{ isUploading ? 'sync' : 'upload_file' }}</span>
                        {{ isUploading ? 'Téléchargement...' : 'Télécharger une image' }}
                    </button>
                    <p class="text-xs text-gray-500 max-w-xs">
                        Formats acceptés : PNG, JPG, JPEG. Poids max : 2Mo.
                    </p>
                </div>
            </div>
        </div>
    </div>

    <!-- Password Change Section -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div class="p-6">
            <h2 class="text-xl font-semibold mb-4 text-gray-800">Sécurité</h2>
            <p class="text-sm text-gray-500 mb-6">
                Modifiez votre mot de passe pour sécuriser votre compte.
            </p>
            
            <form @submit.prevent="handleChangePassword" class="space-y-4 max-w-md">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Ancien mot de passe</label>
                    <input 
                        type="password" 
                        v-model="passwordForm.oldPassword" 
                        required
                        class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none"
                    />
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Nouveau mot de passe</label>
                    <input 
                        type="password" 
                        v-model="passwordForm.newPassword" 
                        required
                        class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none"
                    />
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Confirmer le nouveau mot de passe</label>
                    <input 
                        type="password" 
                        v-model="passwordForm.confirmPassword" 
                        required
                        class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none"
                    />
                </div>
                
                <div class="pt-2">
                    <button 
                        type="submit"
                        :disabled="isChangingPassword"
                        class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center shadow-sm"
                    >
                        <span class="material-symbols-outlined mr-2 text-sm">{{ isChangingPassword ? 'sync' : 'lock_reset' }}</span>
                        {{ isChangingPassword ? 'Modification...' : 'Modifier le mot de passe' }}
                    </button>
                </div>
            </form>
        </div>
    </div>

  </div>
</AppLayout>
</template>

