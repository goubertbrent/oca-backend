import { WeekDayTextTO } from 'rogerthat-plugin';

export interface CirkloVoucher {
  id: string;
  cityId: string;
  originalAmount: number;
  expired: boolean;
  expirationDate: string;
  amount: number;
}

export interface CirkloCity {
  city_id: string;
  logo_url: string;
}

export interface AddVoucherResponse {
  voucher: CirkloVoucher;
  city: CirkloCity;
}

export interface CirkloVouchersList {
  results: CirkloVoucher[];
  cities: {
    [ key: string ]: {
      logo_url: string;
    };
  }
  main_city_id: string;
}

export interface VoucherTransaction {
  id: string;
}

export interface VoucherTransactionsList {
  results: VoucherTransaction[];
}

export interface MerchantOpeningHours {
  open_now: boolean;
  title: string;
  subtitle: string | null;
  weekday_text: WeekDayTextTO[];
}

export interface MerchantAddress {
  coordinates: {
    lat: number;
    lon: number;
  };
  country: string;
  locality: string;
  postal_code: string;
  street: string;
  street_number: string;
  place_id: string | null;
  name: string;
}

export interface CirkloMerchant {
  id: string;
  name: string;
  address: MerchantAddress | null;
  websites: { name: string | null; value: string; }[];
  phone_numbers: { name: string | null; value: string; }[];
  email_addresses: { name: string | null; value: string; }[];
  opening_hours: MerchantOpeningHours | null;
}

export interface CirkloMerchantsList {
  results: CirkloMerchant[];
  cursor: string | null;
  more: boolean;
}
