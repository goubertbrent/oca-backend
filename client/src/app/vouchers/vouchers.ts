export interface VoucherService {
  id: string;
  name: string;
  email: string;
  address: string;
  creation_date: string;
  merchant_registered: boolean;
  whitelist_date: string | null;
  denied: boolean;
  search_data: string[];
}

export interface VouchersServiceList {
  cursor: string | null;
  more: boolean;
  total: number;
  results: VoucherService[];
}

export interface CirkloSettings {
  city_id: string | null;
  logo_url: string | null;
  signup_logo_url: string | null;
  signup_name_nl: string | null;
  signup_name_fr: string | null;
  signup_mail_id_accepted: string | null;
  signup_mail_id_denied: string | null;
}
