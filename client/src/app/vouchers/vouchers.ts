export const enum VoucherProviderId {
  CIRKLO = 'cirklo'
}

export interface VoucherService {
  name: string;
  service_email: string;
  providers: VoucherProviderId[];
  disabled_providers: VoucherProviderId[];
  creation_time: string;
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
