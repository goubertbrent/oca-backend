import { BaseMedia } from '../../news/interfaces';

export interface MapServiceMediaItem {
  role_ids: string[];
  item: BaseMedia;
}

export const enum ServiceInfoSyncProvider {
  PADDLE = 'paddle',
}


export interface SyncedNameValue {
  provider?: ServiceInfoSyncProvider | null;
  name: string | null;
  value: string;
}

export interface ServiceAddress extends SyncedNameValue {
  coordinates: { lat: number; lon: number } | null;
  google_maps_place_id?: string | null;
}

export type SyncedFields = 'name' | 'description' | 'phone_numbers' | 'email_addresses' | 'addresses' | 'websites';

export interface SyncedField {
  key: SyncedFields;
  provider: ServiceInfoSyncProvider;
}

export interface ServiceInfo {
  cover_media: MapServiceMediaItem[];
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
