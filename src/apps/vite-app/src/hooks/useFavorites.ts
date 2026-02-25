import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchFavorites, addFavorite, removeFavorite } from '../services/api'
import { useFavoritesStore } from '../store/favorites'

export function useFavorites() {
  return useQuery({
    queryKey: ['favorites'],
    queryFn: fetchFavorites,
  })
}

interface ToggleVars {
  id: string
  wasFavorited: boolean
}

export function useToggleFavorite() {
  const queryClient = useQueryClient()
  const { addFavoriteId, removeFavoriteId } = useFavoritesStore()

  return useMutation({
    // TanStack Query v5 stores mutationFn in a ref updated on every render.
    // If mutationFn read from the Zustand store, onMutate's optimistic update
    // would trigger a re-render that swaps the ref to a new closure where the
    // id is already present — causing DELETE instead of POST (or vice-versa).
    // Fix: receive the initial state as part of the mutation variables so the
    // decision is made at call-site (click time) rather than at execution time.
    mutationFn: async ({ id, wasFavorited }: ToggleVars) => {
      if (wasFavorited) {
        await removeFavorite(id)
      } else {
        await addFavorite(id)
      }
      return id
    },
    onMutate: ({ id, wasFavorited }: ToggleVars) => {
      // Optimistic update using the caller-supplied initial state
      if (wasFavorited) {
        removeFavoriteId(id)
      } else {
        addFavoriteId(id)
      }
      return { opportunityId: id, wasFavorited }
    },
    onError: (_err, _vars, context) => {
      // Rollback on failure
      if (!context) return
      if (context.wasFavorited) {
        addFavoriteId(context.opportunityId)
      } else {
        removeFavoriteId(context.opportunityId)
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['favorites'] })
    },
  })
}
