import api from "./api";

export type CurrentUserProfile = {
  id: number;
  name: string;
  email: string;
  roles: string[];
  permissions: string[];
};

const PROFILE_STORAGE_KEY = "erp_current_user";

export function saveCurrentUserProfile(profile: CurrentUserProfile): void {
  const serialized = JSON.stringify(profile);
  localStorage.setItem(PROFILE_STORAGE_KEY, serialized);
  sessionStorage.setItem(PROFILE_STORAGE_KEY, serialized);
}

export function getStoredProfile(): CurrentUserProfile | null {
  const raw = localStorage.getItem(PROFILE_STORAGE_KEY) || sessionStorage.getItem(PROFILE_STORAGE_KEY);

  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as CurrentUserProfile;

    if (!Array.isArray(parsed.roles)) {
      parsed.roles = [];
    }

    if (!Array.isArray(parsed.permissions)) {
      parsed.permissions = [];
    }

    return parsed;
  } catch {
    return null;
  }
}

export function clearStoredProfile(): void {
  localStorage.removeItem(PROFILE_STORAGE_KEY);
  sessionStorage.removeItem(PROFILE_STORAGE_KEY);
}

export function hasPermission(userPermissions: string[] | undefined, requiredPermissions: string[]): boolean {
  if (!userPermissions || userPermissions.length === 0) {
    return false;
  }

  // If no required permissions, access is granted
  if (!requiredPermissions || requiredPermissions.length === 0) {
    return true;
  }


  return requiredPermissions.some((perm) => userPermissions.includes(perm));
}



export async function refreshCurrentUserProfile(): Promise<CurrentUserProfile> {
  const response = await api.get("/me");
  const data = response.data as CurrentUserProfile;

  const normalized: CurrentUserProfile = {
    id: data.id,
    name: data.name,
    email: data.email,
    roles: Array.isArray(data.roles) ? data.roles : [],
    permissions: Array.isArray(data.permissions) ? data.permissions : [],
  };

  saveCurrentUserProfile(normalized);
  return normalized;
}
