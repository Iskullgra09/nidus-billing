import { PageInfo } from "./party";

export type PaymentCondition = "contado" | "credito";
export type InvoiceStatus = "draft" | "issued" | "partial" | "paid" | "void";
export type PaymentMethod = "cash" | "transfer" | "card" | "other";
export type InvoiceCurrency = "CRC" | "USD";
export type HaciendaStatus =
  | "pending"
  | "submitted"
  | "accepted"
  | "rejected"
  | "error";

export interface InvoiceLine {
  id: string;
  invoice_id: string;
  line_number: number;
  item_id: string | null;
  description: string;
  sku: string | null;
  unit: string;
  quantity: string;
  unit_price: string;
  tax_rate: string | null;
  tax_code: string | null;
  cabys_code: string | null;
  line_subtotal: string;
  line_tax: string;
  line_total: string;
}

export interface InvoiceFiscal {
  id: string;
  organization_id: string;
  invoice_id: string;
  document_type: string;
  status: HaciendaStatus | "processing";
  clave: string | null;
  consecutive: string | null;
  supply_situation: string;
  signed_at: string | null;
  submitted_at: string | null;
  mh_response_at: string | null;
  mh_status_raw: string | null;
  mh_message: string | null;
  mock_mode: boolean;
  created_at: string;
  updated_at: string;
}

export interface InvoicePayment {
  id: string;
  invoice_id: string;
  amount: string;
  paid_at: string;
  method: PaymentMethod;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export type InvoiceEmailStatus = "sent" | "failed" | "mocked";

export interface InvoiceEmailDelivery {
  id: string;
  organization_id: string;
  invoice_id: string;
  to_email: string;
  subject: string;
  status: InvoiceEmailStatus;
  error_message: string | null;
  sent_at: string | null;
  actor_user_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface InvoiceSendEmailPayload {
  to_email?: string | null;
  subject?: string | null;
  message?: string | null;
}

export interface InvoiceListItem {
  id: string;
  organization_id: string;
  customer_id: string;
  customer_name: string | null;
  payment_condition: PaymentCondition;
  status: InvoiceStatus;
  currency: string;
  document_number: string | null;
  reference_number: string | null;
  issued_at: string | null;
  due_date: string | null;
  subtotal: string;
  tax_total: string;
  total: string;
  amount_paid: string;
  balance_due: string;
  is_overdue: boolean;
  created_at: string;
  updated_at: string;
}

export interface Invoice extends InvoiceListItem {
  notes: string | null;
  lines: InvoiceLine[];
  payments: InvoicePayment[];
}

export interface InvoicePaymentPayload {
  amount: string;
  method?: PaymentMethod;
  paid_at?: string | null;
  notes?: string | null;
}

export interface InvoiceLinePayload {
  item_id?: string | null;
  description: string;
  sku?: string | null;
  unit?: string;
  quantity: string;
  unit_price: string;
  tax_rate?: string | null;
  tax_code?: string | null;
  cabys_code?: string | null;
}

export interface InvoicePayload {
  customer_id: string;
  payment_condition: PaymentCondition;
  due_date?: string | null;
  notes?: string | null;
  reference_number?: string | null;
  currency?: string;
  lines: InvoiceLinePayload[];
}

export interface CursorPage<T> {
  items: T[];
  page_info: PageInfo;
}
