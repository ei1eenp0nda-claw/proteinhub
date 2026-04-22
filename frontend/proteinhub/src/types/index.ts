// User types
export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  created_at: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterCredentials {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

// Protein types
export interface Protein {
  id: number;
  name: string;
  uniprot_id?: string;
  species: string;
  sequence: string;
  molecular_weight: number;
  function_description?: string;
  created_at: string;
  updated_at: string;
}

export interface ProteinListResponse {
  items: Protein[];
  total: number;
  page: number;
  page_size: number;
}

export interface ProteinSearchParams {
  query?: string;
  species?: string;
  page?: number;
  page_size?: number;
}

// Favorite types
export interface Favorite {
  id: number;
  user_id: number;
  protein_id: number;
  created_at: string;
  protein?: Protein;
}

// Auth context types
export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  logout: () => void;
}

// API response types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}
