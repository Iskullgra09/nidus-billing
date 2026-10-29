export interface CatalogItem {
  id: string;
  organization_id: string;
  sku: string | null;
  name: string;
  description: string | null;
  unit: string;
  unit_price: string;
  tax_rate: string | null;
  cabys_code: string | null;
  is_service: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ItemPayload {
  name: string;
  sku?: string | null;
  description?: string | null;
  unit?: string;
  unit_price?: string | number;
  tax_rate?: string | number | null;
  cabys_code?: string | null;
  is_service?: boolean;
  is_active?: boolean;
}
