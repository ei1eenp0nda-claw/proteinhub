import apiClient from './client'

export const authApi = {
  login: (data) => apiClient.post('/auth/login', data),
  register: (data) => apiClient.post('/auth/register', data),
  logout: () => apiClient.post('/auth/logout'),
  getCurrentUser: () => apiClient.get('/auth/me'),
  updateProfile: (data) => apiClient.put('/auth/profile', data),
}

export const noteApi = {
  getNotes: (params) => apiClient.get('/notes', { params }),
  getNoteById: (id) => apiClient.get(`/notes/${id}`),
  createNote: (data) => apiClient.post('/notes', data),
  updateNote: (id, data) => apiClient.put(`/notes/${id}`, data),
  deleteNote: (id) => apiClient.delete(`/notes/${id}`),
  likeNote: (id) => apiClient.post(`/notes/${id}/like`),
  unlikeNote: (id) => apiClient.delete(`/notes/${id}/like`),
  favoriteNote: (id) => apiClient.post(`/notes/${id}/favorite`),
  unfavoriteNote: (id) => apiClient.delete(`/notes/${id}/favorite`),
  getComments: (id, params) => apiClient.get(`/notes/${id}/comments`, { params }),
  addComment: (id, data) => apiClient.post(`/notes/${id}/comments`, data),
  getRelatedNotes: (id) => apiClient.get(`/notes/${id}/related`),
}

export const userApi = {
  getUserById: (id) => apiClient.get(`/users/${id}`),
  getUserNotes: (id, params) => apiClient.get(`/users/${id}/notes`, { params }),
  getUserFavorites: (params) => apiClient.get('/users/me/favorites', { params }),
  followUser: (id) => apiClient.post(`/users/${id}/follow`),
  unfollowUser: (id) => apiClient.delete(`/users/${id}/follow`),
  uploadAvatar: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post('/users/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

export const searchApi = {
  search: (params) => apiClient.get('/search', { params }),
  getHotKeywords: () => apiClient.get('/search/hot'),
  getSuggestions: (query) => apiClient.get('/search/suggestions', { params: { q: query } }),
}

export const adminApi = {
  getDashboardStats: () => apiClient.get('/admin/stats'),
  getPendingNotes: (params) => apiClient.get('/admin/notes/pending', { params }),
  approveNote: (id) => apiClient.post(`/admin/notes/${id}/approve`),
  rejectNote: (id, reason) => apiClient.post(`/admin/notes/${id}/reject`, { reason }),
  getUsers: (params) => apiClient.get('/admin/users', { params }),
  updateUserStatus: (id, status) => apiClient.put(`/admin/users/${id}/status`, { status }),
}

export const uploadApi = {
  uploadImage: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post('/upload/image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  uploadMultiple: (files) => {
    const formData = new FormData()
    files.forEach((file) => formData.append('files', file))
    return apiClient.post('/upload/multiple', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}