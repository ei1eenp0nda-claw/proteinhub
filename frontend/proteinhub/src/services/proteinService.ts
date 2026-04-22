import api from './api';
import { Protein, ProteinListResponse, ProteinSearchParams, Favorite } from '../types';

export const proteinService = {
  async getProteins(params: ProteinSearchParams = {}): Promise<ProteinListResponse> {
    const response = await api.get<ProteinListResponse>('/proteins', { params });
    return response.data;
  },

  async getProteinById(id: number): Promise<Protein> {
    const response = await api.get<Protein>(`/proteins/${id}`);
    return response.data;
  },

  async searchProteins(query: string, page: number = 1, pageSize: number = 10): Promise<ProteinListResponse> {
    const response = await api.get<ProteinListResponse>('/proteins/search', {
      params: { query, page, page_size: pageSize },
    });
    return response.data;
  },

  // Favorites
  async getFavorites(): Promise<Favorite[]> {
    const response = await api.get<Favorite[]>('/favorites');
    return response.data;
  },

  async addFavorite(proteinId: number): Promise<Favorite> {
    const response = await api.post<Favorite>('/favorites', { protein_id: proteinId });
    return response.data;
  },

  async removeFavorite(favoriteId: number): Promise<void> {
    await api.delete(`/favorites/${favoriteId}`);
  },
};
