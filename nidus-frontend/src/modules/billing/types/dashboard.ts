export interface DashboardEmitItem {
  invoice_id: string;
  clave: string | null;
  status: string;
  updated_at: string;
}

export interface DashboardFailureItem {
  invoice_id: string;
  clave: string | null;
  status: string;
  message: string | null;
  updated_at: string;
}

export interface DashboardSummary {
  open_ar: string;
  open_ar_currency: string;
  open_invoice_count: number;
  recent_emits: DashboardEmitItem[];
  hacienda_failure_count: number;
  hacienda_failures: DashboardFailureItem[];
}
