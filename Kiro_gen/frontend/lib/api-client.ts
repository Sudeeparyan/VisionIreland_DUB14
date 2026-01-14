import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

export interface JobStatus {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  result?: any;
  error?: string;
  createdAt: string;
  updatedAt: string;
}

export interface AudioLibraryItem {
  id: string;
  title: string;
  characters: string[];
  scenes: string[];
  duration: number;
  uploadedAt: string;
  fileSize: number;
  audioUrl: string;
  localPath?: string;
  metadata?: {
    originalFilename: string;
    processingTime: number;
    modelUsed: string;
    voiceProfiles: Record<string, string>;
  };
}

export interface UploadResponse {
  job_id: string;
  message: string;
  estimatedProcessingTime: number;
}

export interface LibraryResponse {
  items: AudioLibraryItem[];
  total: number;
  page: number;
  limit: number;
}

export interface SearchResponse {
  items: AudioLibraryItem[];
  total: number;
  query: string;
  suggestions?: string[];
}

class ApiClient {
  private client: AxiosInstance;
  private requestQueue: Map<string, AbortController> = new Map();

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for adding auth and tracking
    this.client.interceptors.request.use(
      (config) => {
        // Add request ID for tracking
        const requestId = this.generateRequestId();
        config.metadata = { requestId, startTime: Date.now() };

        // Add authorization if available
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        return config;
      },
      (error) => {
        console.error('Request interceptor error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling and logging
    this.client.interceptors.response.use(
      (response) => {
        const requestId = response.config.metadata?.requestId;
        const duration = Date.now() - (response.config.metadata?.startTime || 0);

        console.log(`API Request ${requestId} completed in ${duration}ms`);

        return response;
      },
      (error: AxiosError) => {
        const requestId = error.config?.metadata?.requestId;
        const duration = Date.now() - (error.config?.metadata?.startTime || 0);

        console.error(`API Request ${requestId} failed after ${duration}ms:`, error.message);

        // Transform error for better user experience
        const transformedError = this.transformError(error);
        return Promise.reject(transformedError);
      }
    );
  }

  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private getAuthToken(): string | null {
    // In a real app, this would get the token from localStorage or a secure store
    return localStorage.getItem('auth_token');
  }

  private transformError(error: AxiosError): Error {
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const data = error.response.data as any;

      switch (status) {
        case 400:
          return new Error(data?.message || 'Invalid request. Please check your input.');
        case 401:
          return new Error('Authentication required. Please log in.');
        case 403:
          return new Error('Access denied. You do not have permission for this action.');
        case 404:
          return new Error('Resource not found. The requested item may have been deleted.');
        case 413:
          return new Error('File too large. Please select a smaller file.');
        case 429:
          return new Error('Too many requests. Please wait a moment and try again.');
        case 500:
          return new Error('Server error. Please try again later.');
        case 503:
          return new Error('Service temporarily unavailable. Please try again later.');
        default:
          return new Error(data?.message || `Server error (${status}). Please try again.`);
      }
    } else if (error.request) {
      // Network error
      return new Error('Network error. Please check your internet connection and try again.');
    } else {
      // Request setup error
      return new Error('Request failed. Please try again.');
    }
  }

  private createCancelableRequest<T>(
    requestFn: (config: AxiosRequestConfig) => Promise<T>,
    requestId?: string
  ): { promise: Promise<T>; cancel: () => void } {
    const id = requestId || this.generateRequestId();
    const controller = new AbortController();

    this.requestQueue.set(id, controller);

    const promise = requestFn({ signal: controller.signal })
      .finally(() => {
        this.requestQueue.delete(id);
      });

    const cancel = () => {
      controller.abort();
      this.requestQueue.delete(id);
    };

    return { promise, cancel };
  }

  async uploadPdf(
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('filename', file.name);
    formData.append('filesize', file.size.toString());

    const { promise } = this.createCancelableRequest(
      (config) => this.client.post('/upload', formData, {
        ...config,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total && onProgress) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(progress);
          }
        },
        timeout: 120000, // 2 minutes for file upload
      })
    );

    const response = await promise;
    return response.data;
  }

  async getJobStatus(jobId: string): Promise<JobStatus> {
    const { promise } = this.createCancelableRequest(
      (config) => this.client.get(`/jobs/${jobId}`, config)
    );

    const response = await promise;
    return response.data;
  }

  async pollJobStatus(
    jobId: string,
    onUpdate?: (status: JobStatus) => void,
    intervalMs: number = 2000
  ): Promise<JobStatus> {
    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const status = await this.getJobStatus(jobId);
          onUpdate?.(status);

          if (status.status === 'completed' || status.status === 'failed') {
            resolve(status);
          } else {
            setTimeout(poll, intervalMs);
          }
        } catch (error) {
          reject(error);
        }
      };

      poll();
    });
  }

  async getLibrary(
    options: { page?: number; limit?: number; sortBy?: 'title' | 'uploadedAt' | 'duration'; sortOrder?: 'asc' | 'desc' } = {}
  ): Promise<LibraryResponse> {
    const { page = 1, limit = 20, sortBy = 'uploadedAt', sortOrder = 'desc' } = options;
    const { promise } = this.createCancelableRequest(
      (config) => this.client.get('/library', {
        ...config,
        params: { page, limit, sortBy, sortOrder }
      })
    );

    const response = await promise;

    // Transform backend response to frontend format
    const backendItems = response.data.items || [];
    const items: AudioLibraryItem[] = backendItems.map((item: any) => ({
      id: item.id,
      title: item.title || 'Untitled',
      characters: item.characters || [],
      scenes: item.scenes || [],
      duration: item.duration || 0,
      uploadedAt: item.upload_date || new Date().toISOString(),
      fileSize: item.file_size || 0,
      // Convert relative URL to absolute URL
      audioUrl: item.audio_url ? `${API_BASE_URL}${item.audio_url.replace('/api', '')}` : `${API_BASE_URL}/audio/${item.id}`,
      localPath: item.local_path,
      metadata: item.metadata,
    }));

    return {
      items,
      total: response.data.pagination?.total || items.length,
      page: response.data.pagination?.offset ? Math.floor(response.data.pagination.offset / limit) + 1 : page,
      limit,
    };
  }

  async searchLibrary(
    query: string,
    filters?: {
      characters?: string[];
      scenes?: string[];
      minDuration?: number;
      maxDuration?: number;
      uploadedAfter?: string;
      uploadedBefore?: string;
    }
  ): Promise<SearchResponse> {
    const { promise } = this.createCancelableRequest(
      (config) => this.client.get('/library/search', {
        ...config,
        params: { q: query, ...filters }
      })
    );

    const response = await promise;

    // Transform backend response to frontend format
    const backendItems = response.data.items || [];
    const items: AudioLibraryItem[] = backendItems.map((item: any) => ({
      id: item.id,
      title: item.title || 'Untitled',
      characters: item.characters || [],
      scenes: item.scenes || [],
      duration: item.duration || 0,
      uploadedAt: item.upload_date || new Date().toISOString(),
      fileSize: item.file_size || 0,
      audioUrl: item.audio_url ? `${API_BASE_URL}${item.audio_url.replace('/api', '')}` : `${API_BASE_URL}/audio/${item.id}`,
      localPath: item.local_path,
      metadata: item.metadata,
    }));

    return {
      items,
      total: response.data.pagination?.total || items.length,
      query,
      suggestions: [],
    };
  }

  async getAudio(
    audioId: string,
    onProgress?: (progress: number) => void
  ): Promise<Blob> {
    const { promise } = this.createCancelableRequest(
      (config) => this.client.get(`/audio/${audioId}`, {
        ...config,
        responseType: 'blob',
        onDownloadProgress: (progressEvent) => {
          if (progressEvent.total && onProgress) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(progress);
          }
        },
        timeout: 60000, // 1 minute for audio download
      })
    );

    const response = await promise;
    return response.data;
  }

  async getAudioStream(audioId: string): Promise<string> {
    // Return a streaming URL for the audio
    const token = this.getAuthToken();
    const params = token ? `?token=${encodeURIComponent(token)}` : '';
    return `${API_BASE_URL}/audio/${audioId}/stream${params}`;
  }

  async deleteAudio(audioId: string): Promise<void> {
    const { promise } = this.createCancelableRequest(
      (config) => this.client.delete(`/audio/${audioId}`, config)
    );

    await promise;
  }

  async bulkDeleteAudio(audioIds: string[]): Promise<void> {
    const { promise } = this.createCancelableRequest(
      (config) => this.client.post('/audio/bulk-delete', { ids: audioIds }, config)
    );

    await promise;
  }

  async getAudioMetadata(audioId: string): Promise<AudioLibraryItem> {
    const { promise } = this.createCancelableRequest(
      (config) => this.client.get(`/audio/${audioId}/metadata`, config)
    );

    const response = await promise;
    return response.data;
  }

  async updateAudioMetadata(
    audioId: string,
    metadata: Partial<Pick<AudioLibraryItem, 'title' | 'characters' | 'scenes'>>
  ): Promise<AudioLibraryItem> {
    const { promise } = this.createCancelableRequest(
      (config) => this.client.patch(`/audio/${audioId}/metadata`, metadata, config)
    );

    const response = await promise;
    return response.data;
  }

  async getSystemHealth(): Promise<{
    status: 'healthy' | 'degraded' | 'unhealthy';
    services: {
      bedrock: 'up' | 'down' | 'degraded';
      polly: 'up' | 'down' | 'degraded';
      s3: 'up' | 'down' | 'degraded';
      database: 'up' | 'down' | 'degraded';
    };
    version: string;
    uptime: number;
  }> {
    const { promise } = this.createCancelableRequest(
      (config) => this.client.get('/health', { ...config, timeout: 5000 })
    );

    const response = await promise;
    return response.data;
  }

  async getUsageStats(): Promise<{
    totalUploads: number;
    totalProcessingTime: number;
    averageProcessingTime: number;
    totalAudioGenerated: number;
    costEstimate: {
      bedrock: number;
      polly: number;
      s3: number;
      total: number;
    };
  }> {
    const { promise } = this.createCancelableRequest(
      (config) => this.client.get('/stats/usage', config)
    );

    const response = await promise;
    return response.data;
  }

  // Cancel all pending requests
  cancelAllRequests(): void {
    this.requestQueue.forEach((controller) => {
      controller.abort();
    });
    this.requestQueue.clear();
  }

  // Cancel specific request
  cancelRequest(requestId: string): void {
    const controller = this.requestQueue.get(requestId);
    if (controller) {
      controller.abort();
      this.requestQueue.delete(requestId);
    }
  }

  // Get pending request count
  getPendingRequestCount(): number {
    return this.requestQueue.size;
  }
}

export const apiClient = new ApiClient();

// Export types for use in components
export type { ApiResponse, JobStatus, AudioLibraryItem, UploadResponse, LibraryResponse, SearchResponse };
