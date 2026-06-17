export interface Profile {
  display_name: string;
  full_name: string;
  date_of_birth: string;
  emails: string[];
  phone_numbers: string[];
  addresses: Address[];
  aliases: string[];
  ssn_last4: string;
}

export interface Address {
  street: string;
  city: string;
  state: string;
  zip: string;
  current: boolean;
}

export interface Finding {
  id: number;
  user_display_name: string;
  source: string;
  site_id: string;
  site_name: string;
  status: FindingStatus;
  opt_out_url: string | null;
  manual_instructions: string | null;
  last_checked: string | null;
  submitted_at: string | null;
}

export type FindingStatus =
  | "found"
  | "not_found"
  | "submitted"
  | "pending_verification"
  | "manual_required"
  | "cleared";

export interface Breach {
  id: number;
  user_display_name: string;
  email: string;
  breach_name: string;
  breach_date: string | null;
  exposed_fields: string;
  hibp_url: string | null;
  catalogue?: HibpBreachRecord | null;
}

export interface HibpBreachRecord {
  Name: string;
  Title: string;
  Domain: string;
  BreachDate: string;
  AddedDate: string;
  ModifiedDate: string;
  PwnCount: number;
  Description: string;
  LogoPath: string;
  DataClasses: string[];
  IsVerified: boolean;
  IsFabricated: boolean;
  IsSensitive: boolean;
  IsRetired: boolean;
  IsSpamList: boolean;
  IsMalware: boolean;
}

export interface ScanProgressEvent {
  type: "progress" | "done" | "error";
  source?: string;
  site?: string;
  status?: string;
  count?: number;
  total?: number;
  message?: string;
}
