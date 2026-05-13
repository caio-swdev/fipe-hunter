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
    
    
    mutationFn: async ({ id, wasFavorited }: ToggleVars) => {
      if (wasFavorited) {
        await removeFavorite(id)
      } else {
        await addFavorite(id)
      }
      return id
    },
    onMutate: ({ id, wasFavorited }: ToggleVars) => {
      
      if (wasFavorited) {
        removeFavoriteId(id)
      } else {
        addFavoriteId(id)
      }
      return { opportunityId: id, wasFavorited }
    },
    onError: (_err, _vars, context) => {
      
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
