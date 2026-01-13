import axios, { AxiosInstance, AxiosError } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        const message = error.response?.data?.message || error.message;
        console.error('API Error:', message);
        return Promise.reject(error);
      }
    );
  }

  async uploadPdf(file: File): Promise<{ job_id: string }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }

  async getJobStatus(jobId: string): Promise<{ status: string; progress: number }> {
    const response = await this.client.get(`/jobs/${jobId}`);
    return response.data;
  }

  async getLibrary(): Promise<{ items: any[] }> {
    const response = await this.client.get('/library');
    return response.data;
  }

  async searchLibrary(query: string): Promise<{ items: any[] }> {
    const response = await this.client.get('/library/search', {
      params: { q: query },
    });
    return response.data;
  }

  async getAudio(audioId: string): Promise<Blob> {
    const response = await this.client.get(`/audio/${audioId}`, {
      responseType: 'blob',
    });
    return response.data;
  }

  async deleteAudio(audioId: string): Promise<void> {
    await this.client.delete(`/audio/${audioId}`);
  }
}

export const apiClient = new ApiClient();
