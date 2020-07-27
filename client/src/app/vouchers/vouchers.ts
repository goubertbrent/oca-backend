export const enum VoucherProviderId {
  CIRKLO = 'cirklo'
}

export interface VoucherService {
  name: string;
  service_email: string;
  providers: VoucherProvider[];
  creation_time: string;
}

export interface VoucherProvider {
  provider: VoucherProviderId;
  enabled: boolean;
  can_enable: boolean;
  enable_date: string | null;
}

export interface VouchersServiceList {
  cursor: string | null;
  more: boolean;
  total: number;
  results: VoucherService[];
}

export interface ExportVoucherServices {
  url: string;
  filename: string;
}

export interface CirkloSettings {
  city_id: string | null;
  logo_url: string | null;
}
