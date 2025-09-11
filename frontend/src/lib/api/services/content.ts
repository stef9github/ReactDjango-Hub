/**
 * Content Service API Client
 * Handles document management, file storage, and search through Kong Gateway
 */

import { BaseServiceClient, BaseServiceConfig, TokenStorage } from './base';

// Content Service Types
export interface Document {
  id: string;
  title: string;
  description?: string;
  content_type: string;
  file_size: number;
  file_url: string;
  thumbnail_url?: string;
  tags: string[];
  metadata: Record<string, any>;
  owner_id: string;
  organization_id: string;
  version: number;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface DocumentVersion {
  id: string;
  document_id: string;
  version: number;
  title: string;
  file_url: string;
  file_size: number;
  changes: string;
  created_by: string;
  created_at: string;
}

export interface SearchResult {
  documents: Document[];
  total: number;
  page: number;
  limit: number;
  query: string;
  facets?: Record<string, any>;
}

export interface CreateDocumentRequest {
  title: string;
  description?: string;
  tags?: string[];
  is_public?: boolean;
  metadata?: Record<string, any>;
}

export interface UpdateDocumentRequest {
  title?: string;
  description?: string;
  tags?: string[];
  is_public?: boolean;
  metadata?: Record<string, any>;
}

export interface SearchDocumentsRequest {
  query: string;
  filters?: Record<string, any>;
  tags?: string[];
  content_types?: string[];
  page?: number;
  limit?: number;
  sort_by?: 'relevance' | 'created_at' | 'updated_at' | 'title';
  sort_order?: 'asc' | 'desc';
}

export interface UploadResponse {
  document: Document;
  upload_url: string;
}

// Content Service Client
export class ContentServiceClient extends BaseServiceClient {
  constructor(
    config?: Partial<BaseServiceConfig>,
    tokenStorage?: TokenStorage
  ) {
    const defaultConfig: BaseServiceConfig = {
      baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8080',
      timeout: 30000, // Longer timeout for file uploads
      headers: {
        'Content-Type': 'application/json',
      },
    };

    super({ ...defaultConfig, ...config }, tokenStorage);
  }

  // Document endpoints
  async getDocuments(limit?: number, offset?: number, filters?: Record<string, any>): Promise<Document[]> {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    if (offset) params.append('offset', offset.toString());
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString());
        }
      });
    }
    
    const query = params.toString() ? `?${params.toString()}` : '';
    return this.makeRequest<Document[]>('GET', `/api/v1/documents${query}`);
  }

  async getDocumentById(id: string): Promise<Document> {
    return this.makeRequest<Document>('GET', `/api/v1/documents/${id}`);
  }

  async createDocument(data: CreateDocumentRequest): Promise<Document> {
    return this.makeRequest<Document>('POST', '/api/v1/documents', data);
  }

  async updateDocument(id: string, data: UpdateDocumentRequest): Promise<Document> {
    return this.makeRequest<Document>('PATCH', `/api/v1/documents/${id}`, data);
  }

  async deleteDocument(id: string): Promise<{ message: string }> {
    return this.makeRequest<{ message: string }>('DELETE', `/api/v1/documents/${id}`);
  }

  // File upload endpoints
  async uploadFile(file: File, documentData: CreateDocumentRequest): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_data', JSON.stringify(documentData));

    return this.makeRequest<UploadResponse>('POST', '/api/v1/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  async uploadFileVersion(documentId: string, file: File, changes: string): Promise<DocumentVersion> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('changes', changes);

    return this.makeRequest<DocumentVersion>('POST', `/api/v1/documents/${documentId}/versions`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  async getDocumentVersions(documentId: string): Promise<DocumentVersion[]> {
    return this.makeRequest<DocumentVersion[]>('GET', `/api/v1/documents/${documentId}/versions`);
  }

  async getDocumentVersion(documentId: string, version: number): Promise<DocumentVersion> {
    return this.makeRequest<DocumentVersion>('GET', `/api/v1/documents/${documentId}/versions/${version}`);
  }

  async restoreDocumentVersion(documentId: string, version: number): Promise<Document> {
    return this.makeRequest<Document>('POST', `/api/v1/documents/${documentId}/versions/${version}/restore`);
  }

  // Download endpoints
  async getDownloadUrl(documentId: string): Promise<{ download_url: string; expires_at: string }> {
    return this.makeRequest<{ download_url: string; expires_at: string }>('GET', `/api/v1/documents/${documentId}/download`);
  }

  async downloadDocument(documentId: string): Promise<Blob> {
    const response = await this.axiosInstance.get(`/api/v1/documents/${documentId}/download/direct`, {
      responseType: 'blob',
    });
    return response.data;
  }

  // Search endpoints
  async searchDocuments(searchParams: SearchDocumentsRequest): Promise<SearchResult> {
    return this.makeRequest<SearchResult>('POST', '/api/v1/search', searchParams);
  }

  async getSearchSuggestions(query: string, limit?: number): Promise<string[]> {
    const params = new URLSearchParams();
    params.append('q', query);
    if (limit) params.append('limit', limit.toString());
    
    return this.makeRequest<string[]>('GET', `/api/v1/search/suggestions?${params.toString()}`);
  }

  async getSearchFacets(query?: string): Promise<Record<string, any>> {
    const params = new URLSearchParams();
    if (query) params.append('q', query);
    
    const queryString = params.toString() ? `?${params.toString()}` : '';
    return this.makeRequest<Record<string, any>>('GET', `/api/v1/search/facets${queryString}`);
  }

  // Tag management
  async getTags(): Promise<string[]> {
    return this.makeRequest<string[]>('GET', '/api/v1/documents/tags');
  }

  async addTagToDocument(documentId: string, tag: string): Promise<Document> {
    return this.makeRequest<Document>('POST', `/api/v1/documents/${documentId}/tags`, { tag });
  }

  async removeTagFromDocument(documentId: string, tag: string): Promise<Document> {
    return this.makeRequest<Document>('DELETE', `/api/v1/documents/${documentId}/tags/${encodeURIComponent(tag)}`);
  }

  // Sharing and permissions
  async shareDocument(documentId: string, recipientEmail: string, permissions: string[]): Promise<{ message: string }> {
    return this.makeRequest<{ message: string }>('POST', `/api/v1/documents/${documentId}/share`, {
      recipient_email: recipientEmail,
      permissions,
    });
  }

  async getDocumentPermissions(documentId: string): Promise<any[]> {
    return this.makeRequest<any[]>('GET', `/api/v1/documents/${documentId}/permissions`);
  }

  async updateDocumentPermissions(documentId: string, userId: string, permissions: string[]): Promise<{ message: string }> {
    return this.makeRequest<{ message: string }>('PUT', `/api/v1/documents/${documentId}/permissions/${userId}`, {
      permissions,
    });
  }

  async revokeDocumentAccess(documentId: string, userId: string): Promise<{ message: string }> {
    return this.makeRequest<{ message: string }>('DELETE', `/api/v1/documents/${documentId}/permissions/${userId}`);
  }
}

// Default client instance
export const contentClient = new ContentServiceClient();