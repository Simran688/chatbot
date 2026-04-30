export interface User {
  id: number
  email: string
  full_name: string | null
  role: 'admin' | 'user'
  is_active: boolean
  created_at: string
}

export interface Token {
  access_token: string
  token_type: string
  expires_in: number
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  full_name?: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: SourceSnippet[]
  webResults?: WebSearchResult[]
  queryType?: string
  usedWebSearch?: boolean
  timestamp: Date
}

export interface SourceSnippet {
  text: string
  document: string
  chunk_index: number
  relevance_score: number
  url?: string
}

export interface WebSearchResult {
  title: string
  url: string
  snippet: string
}

export interface QueryRequest {
  query: string
  top_k?: number
  include_sources?: boolean
}

export interface QueryResponse {
  query: string
  answer: string
  source_documents: string[]
  source_snippets: SourceSnippet[]
  query_type: string
  used_web_search: boolean
  response_time_ms?: number
  web_results?: WebSearchResult[]
}

export interface Document {
  id: number
  name: string
  original_filename: string
  source: 'upload' | 'google_drive'
  file_type: string | null
  file_size: number | null
  is_processed: number
  created_at: string
}

export interface DocumentUploadResponse {
  message: string
  document: Document
  chunks_created: number
}
