/**
 * Types et interfaces pour le système d'auto-embedding
 * Partagés entre client et serveur
 */

/**
 * Configuration d'embedding pour une table
 */
export interface EmbeddingConfig {
  enabled: boolean;
  autoGenerate: boolean;
  sourceColumns?: string[];  // Colonnes à inclure dans l'embedding (auto-detect si vide)
  provider: 'albert' | 'openai';
  triggerOn: ('insert' | 'update')[];
  batchSize?: number;  // Nombre de records à traiter en batch (default: 10)
  maxRetries?: number;  // Nombre de retry en cas d'erreur (default: 3)
}

/**
 * Requête d'embedding en attente de traitement
 */
export interface EmbeddingRequest {
  tableId: string;
  rowId: number;
  content: string;
  contentHash: string;
  priority: number;
  queuedAt: number;
  retryCount: number;
  lastError?: string;
}

/**
 * Résultat de génération d'embedding
 */
export interface EmbeddingResult {
  rowId: number;
  embedding: number[];
  dimensions: number;
  contentHash: string;
  generatedAt: number;
  provider: string;
}

/**
 * Statistiques du manager d'embedding
 */
export interface EmbeddingStats {
  queueSize: number;
  totalProcessed: number;
  totalFailed: number;
  averageTimeMs: number;
  isProcessing: boolean;
  lastProcessedAt?: number;
}

/**
 * Résultat de recherche sémantique
 */
export interface SemanticSearchResult {
  rowId: number;
  score: number;
  preview: string;
  embedding?: number[];
}

/**
 * Options pour la recherche sémantique
 */
export interface SemanticSearchOptions {
  query: string;
  limit?: number;
  threshold?: number;
  includeEmbeddings?: boolean;
}

/**
 * Status d'un embedding
 */
export enum EmbeddingStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

/**
 * Événement d'embedding (pour notifications)
 */
export interface EmbeddingEvent {
  type: 'queued' | 'processing' | 'completed' | 'failed';
  tableId: string;
  rowIds: number[];
  timestamp: number;
  error?: string;
}
