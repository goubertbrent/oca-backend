import { MediaItem } from '../../shared/media-selector/media';

export const enum ServiceInfoSyncProvider {
  PADDLE = 'paddle',
}

export interface SyncedName {
  provider?: ServiceInfoSyncProvider | null;
  name: string | null;
}

export interface SyncedNameValue extends SyncedName {
  provider?: ServiceInfoSyncProvider | null;
  name: string | null;
  value: string;
}

export interface ServiceAddress extends SyncedName {
  coordinates: { lat: number; lon: number } | null;
  google_maps_place_id?: string | null;
  country: string;  // BE
  locality: string;  // Nazareth
  postal_code: string;  // 9810
  street: string; // Steenweg Deinze
  street_number: string; // 154
}

export type SyncedFields = 'name' | 'description' | 'phone_numbers' | 'email_addresses' | 'addresses' | 'websites';

export interface SyncedField {
  key: SyncedFields;
  provider: ServiceInfoSyncProvider;
}

export interface ServiceInfo {
  media: MediaItem[];
  websites: SyncedNameValue[];
  name: string;
  timezone: string;
  phone_numbers: SyncedNameValue[];
  email_addresses: SyncedNameValue[];
  description: string;
  currency: string;
  addresses: ServiceAddress[];
  keywords: string[];
  main_place_type: string | null;
  place_types: string[];
  synced_fields: SyncedField[];
  visible: boolean;
}

export interface PrivacySettings {
  type: string;
  label: string;
  enabled: boolean;
}

export interface PrivacySettingsGroup {
  page: number;
  description: string;
  items: PrivacySettings[];
}
