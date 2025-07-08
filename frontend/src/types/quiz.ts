export interface Quiz {
  id: number
  title: string
  description?: string
  difficulty_level: 'easy' | 'medium' | 'hard'
  question_types: string[]
  total_questions: number
  question_count: number
  status: 'draft' | 'published' | 'archived'
  is_public: boolean
  share_token?: string
  view_count: number
  download_count: number
  created_at: string
  updated_at: string
  published_at?: string
  user_id: number
  source_file_id?: number
  ai_model_used?: string
  generation_time?: number
  questions?: Question[]
  source_text?: string
  generation_parameters?: Record<string, any>
  source_file?: FileInfo
}

export interface Question {
  id: number
  question_text: string
  question_type: 'multiple_choice' | 'true_false' | 'short_answer' | 'essay'
  difficulty_level: 'easy' | 'medium' | 'hard'
  options?: string[]
  correct_answer?: string
  explanation?: string
  topic?: string
  keywords?: string[]
  bloom_taxonomy_level?: string
  confidence_score?: number
  order_index: number
  is_active: boolean
  created_at: string
  quiz_id: number
  source_sentence?: string
}

export interface QuestionType {
  value: string
  label: string
  description: string
}

export interface DifficultyLevel {
  value: string
  label: string
  description: string
}

export interface CreateQuizRequest {
  title: string
  description?: string
  source_text?: string
  source_file_id?: number
  difficulty_level: 'easy' | 'medium' | 'hard'
  question_types: string[]
  total_questions: number
}

export interface UpdateQuizRequest {
  title?: string
  description?: string
  difficulty_level?: 'easy' | 'medium' | 'hard'
  question_types?: string[]
  status?: 'draft' | 'published' | 'archived'
  is_public?: boolean
}

export interface GenerateQuestionsRequest {
  text: string
  num_questions: number
  question_types: string[]
  difficulty_level: 'easy' | 'medium' | 'hard'
}

export interface GeneratedQuestion {
  question_text: string
  question_type: string
  options?: string[]
  correct_answer?: string
  explanation?: string
  difficulty_level: string
  topic?: string
  keywords?: string[]
  confidence_score?: number
  source_sentence?: string
  bloom_taxonomy_level?: string
}

export interface FileInfo {
  id: number
  filename: string
  original_filename: string
  file_size: number
  file_size_human: string
  mime_type?: string
  file_extension: string
  extraction_status: 'pending' | 'success' | 'failed'
  page_count?: number
  word_count?: number
  character_count?: number
  is_processed: boolean
  is_safe: boolean
  virus_scan_status: 'pending' | 'clean' | 'infected'
  download_count: number
  created_at: string
  last_accessed?: string
  user_id: number
  can_extract_text: boolean
  exists_on_disk: boolean
  extracted_text?: string
  extraction_error?: string
}
