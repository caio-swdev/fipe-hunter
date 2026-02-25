import { create } from 'zustand'

interface AdminAuthState {
  token: string | null
  setToken: (token: string) => void
  clearToken: () => void
}

export const useAdminAuthStore = create<AdminAuthState>((set) => ({
  token: null,
  setToken: (token) => set({ token }),
  clearToken: () => set({ token: null }),
}))
