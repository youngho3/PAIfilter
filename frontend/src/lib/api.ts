/**
 * PAI API Client
 *
 * Provides typed API client with:
 * - Automatic retry logic
 * - Error handling
 * - Type-safe responses
 */

import axios, { AxiosError, AxiosInstance } from "axios";

// Configuration
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 1000;

// Types
export interface APIError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
  timestamp: string;
}

export interface VectorizeResult {
  original_text: string;
  vector_dimension: number;
  vector_preview: number[];
}

export interface InsightResult {
  insight: string;
  context_used: string[];
  model_used: string;
}

export interface ContextResult {
  status: string;
  id: string;
  message: string;
}

export interface MatchResult {
  id: string;
  score: number;
  text: string;
  metadata: Record<string, unknown>;
}

export interface SearchResult {
  matches: MatchResult[];
  query: string;
  total_results: number;
}

// API Client
class PAIApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Response interceptor for error handling and retries
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError<APIError>) => {
        const originalRequest = error.config as typeof error.config & {
          _retryCount?: number;
        };

        // Retry logic for network errors (not for 4xx errors)
        if (
          !error.response &&
          originalRequest &&
          (originalRequest._retryCount || 0) < MAX_RETRIES
        ) {
          originalRequest._retryCount = (originalRequest._retryCount || 0) + 1;
          await this.delay(RETRY_DELAY_MS * originalRequest._retryCount);
          return this.client(originalRequest);
        }

        // Transform error to consistent format
        const apiError: APIError = error.response?.data || {
          success: false,
          error: {
            code: "network_error",
            message: error.message || "Network error occurred",
          },
          timestamp: new Date().toISOString(),
        };

        return Promise.reject(apiError);
      }
    );
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Convert text to vector embedding.
   */
  async vectorize(text: string): Promise<VectorizeResult> {
    const response = await this.client.post<VectorizeResult>(
      "/api/v1/vectorize",
      { text }
    );
    return response.data;
  }

  /**
   * Save context to vector database.
   */
  async saveContext(text: string): Promise<ContextResult> {
    const response = await this.client.post<ContextResult>("/api/v1/context", {
      text,
    });
    return response.data;
  }

  /**
   * Generate AI insight with RAG.
   */
  async getInsight(text: string): Promise<InsightResult> {
    const response = await this.client.post<InsightResult>("/api/v1/insight", {
      text,
    });
    return response.data;
  }

  /**
   * Search for similar contexts.
   */
  async search(text: string, topK: number = 3): Promise<SearchResult> {
    const response = await this.client.post<SearchResult>("/api/v1/search", {
      text,
      top_k: topK,
    });
    return response.data;
  }

  /**
   * Health check.
   */
  async healthCheck(): Promise<{
    status: string;
    service: string;
    config: Record<string, boolean>;
  }> {
    const response = await this.client.get("/");
    return response.data;
  }
}

// Singleton instance
export const apiClient = new PAIApiClient();

/**
 * Extract user-friendly error message from API error.
 */
export function getErrorMessage(error: unknown): string {
  if (typeof error === "object" && error !== null && "error" in error) {
    const apiError = error as APIError;
    return apiError.error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "An unexpected error occurred";
}
