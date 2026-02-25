import { create } from 'zustand'

interface FilterState {
  searchQuery: string
  minScore: number
  minDiscount: number
  sortBy: 'score' | 'discount_percent' | 'listing_price'
  sortOrder: 'asc' | 'desc'
  setSearchQuery: (query: string) => void
  setMinScore: (score: number) => void
  setMinDiscount: (discount: number) => void
  setSortBy: (field: FilterState['sortBy']) => void
  toggleSortOrder: () => void
  resetFilters: () => void
}

export const useFilterStore = create<FilterState>((set) => ({
  searchQuery: '',
  minScore: 0,
  minDiscount: -50,
  sortBy: 'score',
  sortOrder: 'desc',
  setSearchQuery: (query) => set({ searchQuery: query }),
  setMinScore: (score) => set({ minScore: score }),
  setMinDiscount: (discount) => set({ minDiscount: discount }),
  setSortBy: (field) => set({ sortBy: field }),
  toggleSortOrder: () => set((s) => ({ sortOrder: s.sortOrder === 'asc' ? 'desc' : 'asc' })),
  resetFilters: () => set({ searchQuery: '', minScore: 0, minDiscount: -50, sortBy: 'score', sortOrder: 'desc' }),
}))
