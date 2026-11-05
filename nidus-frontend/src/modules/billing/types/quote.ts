import { PageInfo } from "./party";
import type { InvoiceCurrency, InvoiceLinePayload } from "./invoice";

export type QuoteStatus =
  | "draft"
  | "sent"
  | "accepted"
  | "rejected"
  | "converted";

export interface QuoteLine {
  id: string;
  quote_id: string;
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

export interface QuoteListItem {
  id: string;
  organization_id: string;
  customer_id: string;
  customer_name: string | null;
  status: QuoteStatus;
  currency: string;
  exchange_rate?: string | null;
  exchange_rate_date?: string | null;
  reference_number: string | null;
  valid_until: string | null;
  subtotal: string;
  tax_total: string;
  total: string;
  converted_invoice_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Quote extends QuoteListItem {
  notes: string | null;
  lines: QuoteLine[];
}

export interface QuotePayload {
  customer_id: string;
  notes?: string | null;
  reference_number?: string | null;
  valid_until?: string | null;
  currency?: InvoiceCurrency;
  exchange_rate?: string | null;
  exchange_rate_date?: string | null;
  lines: InvoiceLinePayload[];
}

export interface CursorPage<T> {
  items: T[];
  page_info: PageInfo;
}
