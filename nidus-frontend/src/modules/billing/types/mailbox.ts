export interface InboundMailbox {
  organization_id: string;
  local_part: string;
  domain: string;
  address: string;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}
