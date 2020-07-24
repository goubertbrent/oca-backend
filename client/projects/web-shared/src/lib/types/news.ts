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

export interface NewsItemTimeValue {
  time: string;
  value: number;
}

export interface NewsItemTimeStatistics {
  id: number;
  reached: NewsItemTimeValue[];
  action: NewsItemTimeValue[];
}

export interface KeyValueLong {
  key: string;
  value: number;
}

export type UINewsActionButton =
  NewsActionButtonWebsite
  | NewsActionButtonPhone
  | NewsActionButtonEmail
  | NewsActionButtonAttachment
  | NewsActionButtonMenuItem
  | NewsActionButtonOpen;

export interface NewsItemBasicStatistic {
  total: number;
  gender: KeyValueLong[];
  age: KeyValueLong[];
}

export interface NewsItemBasicStatistics {
  id: number;
  reached: NewsItemBasicStatistic;
  action: NewsItemBasicStatistic;
}

export interface NewsTargetAudience {
  min_age: number;
  max_age: number;
  gender: Gender;
  connected_users_only: boolean;
}

export interface NewsSender {
  email: string;
  name: string;
  avatar_id: string;
  avatar_url: string;
}

export interface NewsActionButton extends BaseButton {
  flow_params?: string | null;
}

export enum NewsActionButtonType {
  WEBSITE,
  PHONE,
  EMAIL,
  ATTACHMENT,
  MENU_ITEM,
  OPEN,
}

export interface BaseNewsButton {
  label: string;
  button: NewsActionButton;
}

export interface NewsActionButtonWebsite extends BaseNewsButton {
  type: NewsActionButtonType.WEBSITE;
}

export interface NewsActionButtonPhone extends BaseNewsButton {
  phone: string;
  type: NewsActionButtonType.PHONE;
}

export interface NewsActionButtonEmail extends BaseNewsButton {
  email: string;
  type: NewsActionButtonType.EMAIL;
}

export interface NewsActionButtonAttachment extends BaseNewsButton {
  type: NewsActionButtonType.ATTACHMENT;
}

export interface NewsActionButtonMenuItem extends BaseNewsButton {
  type: NewsActionButtonType.MENU_ITEM;
}

export interface NewsActionButtonOpen extends BaseNewsButton {
  type: NewsActionButtonType.OPEN;
}

export interface BaseMedia {
  type: MediaType;
  content: string;
}

export interface Media extends BaseMedia {
  width: number;
  height: number;
}

export interface NewsItemList {
  result: NewsItem[];
  cursor: string | null;
  more: boolean;
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
  PRESS = 'press',
  POLLS = 'polls',
}

export interface ServiceNewsGroup {
  group_type: NewsGroupType;
  name: string;
}

export interface CreateNews<T = Date> {
  id: number | null;
  title: string;
  message: string;
  action_button: NewsActionButton | null;
  type: NewsItemType;
  qr_code_caption: string | null;
  app_ids: string[];
  scheduled_at: T | null;
  target_audience: NewsTargetAudience | null;
  role_ids: number[];
  media: BaseMedia | null;
  group_type: NewsGroupType;
  locations: NewsLocation | null;
  group_visible_until: T | null;
}

export interface NewsStats {
  news_item: NewsItem;
  statistics: NewsItemBasicStatistics;
}

export const enum NewsSettingsTag {
  FREE_REGIONAL_NEWS = 'free_regional_news'
}

export interface NewsOptions {
  tags: NewsSettingsTag[];
  regional: {
    enabled: boolean;
    map_url?: string | null;
  };
  groups: ServiceNewsGroup[];
  media_types: MediaType[];
  location_filter_enabled: boolean;
  action_buttons: UINewsActionButton[];
}

export interface Street {
  name: string;
  id: number;
}

export interface LocationBounds {
  northeast: { lat: number, lon: number };
  southwest: { lat: number, lon: number };
}

export interface Locality {
  postal_code: string;
  name: string;
  bounds: LocationBounds;
  location: { lat: number, lon: number };
  streets: Street[];
}

export interface CityAppLocations {
  app_id: string;
  country_code: string;
  localities: Locality[];
}

export interface NewsItem {
  type: NewsItemType;
  sticky: boolean;
  sticky_until: number;
  app_ids: string[];
  scheduled_at: number;
  published: boolean;
  target_audience: NewsTargetAudience | null;
  role_ids: number[];
  tags: string[];
  id: number;
  sender: NewsSender;
  title: string;
  message: string;
  /**
   * @deprecated use group_type instead
   */
  broadcast_type: string;
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
