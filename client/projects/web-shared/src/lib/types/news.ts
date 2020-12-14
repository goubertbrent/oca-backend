import { BaseButton } from './messaging';

export enum NewsItemType {
  NORMAL = 1,
  QR_CODE = 2,
}

export const enum Gender {
  MALE_OR_FEMALE,
  MALE,
  FEMALE,
  CUSTOM,
}

export enum MediaType {
  IMAGE = 'image',
  YOUTUBE_VIDEO = 'video_youtube',
}

export interface NewsSender {
  email: string;
  name: string;
  avatar_id: string;
  avatar_url: string;
}

export interface NewsTargetAudience {
  min_age: number;
  max_age: number;
  gender: Gender;
  connected_users_only: boolean;
}

export interface NewsActionButton extends BaseButton {
  flow_params?: string | null;
}

export interface BaseMedia {
  type: MediaType;
  content: string;
}

export interface Media extends BaseMedia {
  width: number;
  height: number;
}

export interface NewsGeoAddress {
  /**
   * Circle radius in meters
   */
  distance: number;
  latitude: number;
  longitude: number;
}

export interface NewsAddress {
  level: 'STREET';
  country_code: string;
  city: string;
  zip_code: string;
  street_name: string;
}

export interface NewsLocation {
  match_required: boolean;
  geo_addresses: NewsGeoAddress[];
  addresses: NewsAddress[];
}

export const enum NewsGroupType {
  PROMOTIONS = 'promotions',
  CITY = 'city',
  EVENTS = 'events',
  TRAFFIC = 'traffic',
  PUBLIC_SERVICE_ANNOUNCEMENTS = 'public_service_announcements',
  PRESS = 'press',
  POLLS = 'polls',
}

export const NEWS_GROUP_TYPES = [
  { type: NewsGroupType.CITY, label: 'City' },
  { type: NewsGroupType.EVENTS, label: 'Events' },
  { type: NewsGroupType.POLLS, label: 'Polls' },
  { type: NewsGroupType.PRESS, label: 'Press' },
  { type: NewsGroupType.PROMOTIONS, label: 'Promotions' },
  { type: NewsGroupType.TRAFFIC, label: 'Traffic' },
  { type: NewsGroupType.PUBLIC_SERVICE_ANNOUNCEMENTS, label: 'Public service announcements' },
];

export interface NewsItem {
  type: NewsItemType;
  sticky: boolean;
  sticky_until: number;
  community_ids: number[];
  scheduled_at: number;
  published: boolean;
  target_audience: NewsTargetAudience | null;
  tags: string[];
  id: number;
  sender: NewsSender;
  title: string;
  message: string;
  buttons: NewsActionButton[];
  qr_code_content: string | null;
  qr_code_caption: string | null;
  version: number;
  timestamp: number;
  flags: number;
  media: Media | null;
  group_type: NewsGroupType;
  locations: NewsLocation | null;
  group_visible_until: number | null;
  share_url: string | null;
}
