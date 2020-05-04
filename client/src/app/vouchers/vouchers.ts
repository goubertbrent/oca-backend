export const enum VoucherProviderId {
  CIRKLO = 'cirklo'
}

export interface VoucherService {
  name: string;
  service_email: string;
  providers: VoucherProviderId[];
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
