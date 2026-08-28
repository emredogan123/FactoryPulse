export type UserRole =
  | 'ADMIN'
  | 'QUALITY_ENGINEER'
  | 'VIEWER'

export type PCBStatus =
  | 'QUEUED'
  | 'IN_PRODUCTION'
  | 'PASSED'
  | 'FAILED'
  | 'REWORK'

export type RiskLevel =
  | 'LOW'
  | 'MEDIUM'
  | 'HIGH'

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface User {
  id: string
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
}

export interface PCBStatusCounts {
  passed: number
  failed: number
  rework: number
  queued: number
}

export interface AnalyticsOverview {
  production_order_count: number
  pcb_count: number
  pcb_status_counts: PCBStatusCounts
  pass_rate: number
  failure_rate: number
  rework_rate: number
  process_event_count: number
  quality_measurement_count: number
  out_of_spec_measurement_count: number
}

export interface PCBUnit {
  id: string
  serial_number: string
  production_order_id: string
  material_lot_id: string | null
  shift: 'DAY' | 'NIGHT'
  status: PCBStatus
  created_at: string
  updated_at: string
}

export interface PCBRiskPrediction {
  pcb_id: string
  serial_number: string
  actual_status: PCBStatus
  issue_probability: number
  decision_threshold: number
  predicted_issue: boolean
  risk_level: RiskLevel
  model_type: string
}
export interface PCBRiskListResponse {
  total_analyzed: number
  high_risk_count: number
  medium_risk_count: number
  low_risk_count: number
  items: PCBRiskPrediction[]
}
export interface ModelPerformance {
  model_name: string
  model_type: string
  evaluated_at: string
  dataset: {
    name: string
    row_count: number
    issue_count: number
    issue_rate: number
  }
  decision_threshold: number
  feature_count: number
  metrics: {
    accuracy: number
    precision: number
    recall: number
    f1_score: number
    roc_auc: number
  }
  confusion_matrix: {
    true_negative: number
    false_positive: number
    false_negative: number
    true_positive: number
  }
  feature_importances: Array<{
    feature: string
    importance: number
  }>
}