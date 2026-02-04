export type WorkflowEvent = {
  type: string;
  phase?: string;
  message?: string;
  data?: Record<string, unknown>;
  timestamp?: string;
  status?: string;
};

export type QuestionOption = {
  id: string;
  label: string;
  description?: string | null;
};

export type StructuredQuestion = {
  text: string;
  question_type?: string;
  options?: QuestionOption[] | null;
  allows_multiple?: boolean;
  allows_other?: boolean;
  rationale?: string | null;
};

export type HitlPrompt = {
  status: string;
  type?: string | null;
  current_phase?: string | null;
  progress_message?: string | null;
  questions?: StructuredQuestion[] | null;
  rationale?: string | null;
  summary?: string | null;
  path?: string | null;
  key_assumptions?: string[] | null;
  content?: string | null;
  highlights?: string[] | null;
  report?: string | null;
  passed?: boolean | null;
  skill_content?: string | null;
  intended_taxonomy_path?: string | null;
  draft_path?: string | null;
  final_path?: string | null;
  promoted?: boolean | null;
  saved_path?: string | null;
  validation_passed?: boolean | null;
  validation_status?: string | null;
  validation_score?: number | null;
  error?: string | null;
  question?: string | null;
  research_performed?: unknown[] | null;
  current_understanding?: string | null;
  readiness_score?: number | null;
  questions_asked?: unknown[] | null;
  structure_issues?: string[] | null;
  structure_warnings?: string[] | null;
  suggested_fixes?: Record<string, unknown>[] | null;
  current_skill_name?: string | null;
  current_description?: string | null;
};

export type CreateJobResponse = {
  job_id?: string;
  status?: string;
  error?: string;
};
