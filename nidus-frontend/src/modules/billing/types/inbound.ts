import { PageInfo } from "./party";

export type InboundStatus =
  | "pending"
  | "submitted"
  | "processing"
  | "accepted"
  | "rejected"
  | "error";

export type InboundIngestChannel = "manual_upload" | "hacienda_sync" | "email";

export interface InboundDocument {
  id: string;
  organization_id: string;
  supplier_id: string | null;
  supplier_name: string | null;
  clave: string;
  consecutive: string | null;
  document_type: string;
  status: InboundStatus;
  ingest_channel: InboundIngestChannel;
  emitter_identification_type: string | null;
  emitter_identification_number: string | null;
  emitter_name: string | null;
  emitter_email: string | null;
  issued_at: string | null;
  currency: string;
  exchange_rate: string | null;
  subtotal: string;
  tax_total: string;
  total: string;
  mensaje_tipo: string | null;
  mensaje_detalle: string | null;
  mensaje_submitted_at: string | null;
  mh_response_at: string | null;
  mh_status_raw: string | null;
  mh_message: string | null;
  mock_mode: boolean;
  notes: string | null;
  received_at: string;
  created_at: string;
  updated_at: string;
}

export interface InboundCreatePayload {
  xml: string;
  supplier_id?: string | null;
  notes?: string | null;
}

export interface InboundLinkPayload {
  supplier_id?: string | null;
  notes?: string | null;
}

export interface CursorPage<T> {
  items: T[];
  page_info: PageInfo;
}
