export interface Party {
  id: string;
  organization_id: string;
  name: string;
  email: string | null;
  phone: string | null;
  tax_id: string | null;
  notes: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PartyPayload {
  name: string;
  email?: string | null;
  phone?: string | null;
  tax_id?: string | null;
  notes?: string | null;
  is_active?: boolean;
}

export interface PageInfo {
  has_next_page: boolean;
  end_cursor: string | null;
}

export interface CursorPage<T> {
  items: T[];
  page_info: PageInfo;
}
