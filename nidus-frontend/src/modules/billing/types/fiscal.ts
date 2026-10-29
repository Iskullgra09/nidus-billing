export type IdentificationType =
  | "fisica"
  | "juridica"
  | "dimex"
  | "nite"
  | "extranjero";

export type HaciendaEnvironment = "sandbox" | "production";

export interface FiscalProfile {
  id: string;
  organization_id: string;
  legal_name: string;
  trade_name: string | null;
  identification_type: IdentificationType;
  identification_number: string;
  economic_activity_code: string | null;
  branch_code: string | null;
  province: string | null;
  canton: string | null;
  district: string | null;
  other_signs: string | null;
  phone: string | null;
  email: string | null;
  country_code: string;
  created_at: string;
  updated_at: string;
}

export interface FiscalProfilePayload {
  legal_name: string;
  trade_name?: string | null;
  identification_type: IdentificationType;
  identification_number: string;
  economic_activity_code?: string | null;
  branch_code?: string | null;
  province?: string | null;
  canton?: string | null;
  district?: string | null;
  other_signs?: string | null;
  phone?: string | null;
  email?: string | null;
  country_code?: string;
}

export interface HaciendaCredentialStatus {
  configured: boolean;
  environment: HaciendaEnvironment;
  username: string | null;
  has_p12: boolean;
  has_p12_password: boolean;
  has_pin: boolean;
  has_oauth_client_secret: boolean;
  oauth_client_id: string | null;
  updated_at: string | null;
}
