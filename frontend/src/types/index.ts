export interface Author {
  name: string;
  affiliation?: string;
  position: number;
}

export interface Summary {
  summary_en?: string;
  summary_cn?: string;
  innovation_points?: string;
  limitations?: string;
  model_used?: string;
}

export interface Paper {
  id: number;
  pmid: string;
  pmcid?: string;
  doi?: string;
  title: string;
  abstract?: string;
  journal?: string;
  issn?: string;
  year?: number;
  keywords?: string;
  mesh_terms?: string;
  authors: Author[];
  impact_factor?: number;
  sci_partition?: string;
  summary?: Summary;
  has_fulltext: boolean;
  created_at?: string;
}

export interface SearchResponse {
  search_id: number;
  query: string;
  total: number;
  papers: Paper[];
}

export interface SearchHistoryItem {
  id: number;
  query: string;
  min_year?: number;
  max_year?: number;
  min_impact_factor?: number;
  result_count: number;
  created_at: string;
}

export interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface ChatStreamEvent {
  content: string;
  done: boolean;
  session_id: number;
}

export interface SummarizeResult {
  paper_id: number;
  summary_en: string;
  summary_cn: string;
  innovation_points: string;
  limitations: string;
  model_used: string;
}

export interface FulltextResponse {
  available: boolean;
  source?: string;
  content_type?: string;
  content?: string;
  oa_url?: string;
}

export interface AppConfig {
  ncbi_email: string;
  ncbi_api_key_set: boolean;
  easyscholar_key_set: boolean;
  llm_base_url: string;
  llm_model: string;
  llm_api_key_set: boolean;
  unpaywall_email: string;
}

export interface ZoteroAccount {
  id: number;
  name: string;
  library_id: string;
  library_type: string;
  api_key_set: boolean;
}

export interface ZoteroCollection {
  key: string;
  name: string;
  parent: string | null;
}
