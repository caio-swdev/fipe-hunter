import { create } from 'zustand'

interface FavoritesState {
  favoriteIds: Set<string>
  setFavoriteIds: (ids: string[]) => void
  addFavoriteId: (id: string) => void
  removeFavoriteId: (id: string) => void
}

export const useFavoritesStore = create<FavoritesState>((set) => ({
  favoriteIds: new Set(),
  setFavoriteIds: (ids) => set({ favoriteIds: new Set(ids) }),
  addFavoriteId: (id) =>
    set((s) => {
      const next = new Set(s.favoriteIds)
      next.add(id)
      return { favoriteIds: next }
    }),
  removeFavoriteId: (id) =>
    set((s) => {
      const next = new Set(s.favoriteIds)
      next.delete(id)
      return { favoriteIds: next }
    }),
}))
