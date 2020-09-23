import {
  BaseMedia,
  MediaType,
  NewsActionButton,
  NewsGroupType,
  NewsItem,
  NewsItemType,
  NewsLocation,
  NewsTargetAudience,
} from '@oca/web-shared';

export interface NewsListItem extends NewsItem {
  statistics?: NewsItemBasicStatistics;
}

export interface NewsCommunityMapping {
  [ key: number ]: NewsCommunity;
}

export interface NewsCommunity {
  id: number;
  name: string;
  total_user_count: number;
}

export interface ServiceNewsGroup {
  group_type: NewsGroupType;
  name: string;
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

export interface NewsItemList {
  result: NewsItem[];
  cursor: string | null;
  more: boolean;
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
  community_ids: number[];
  scheduled_at: T | null;
  target_audience: NewsTargetAudience | null;
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
  service_name: string;
  community_id: number;
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
  community_id: number;
  country_code: string;
  localities: Locality[];
}

export interface RssScraper {
  url: string;
  group_type: NewsGroupType;
  community_ids: number[];
}

export interface RssSettings {
  notify: boolean;
  scrapers: RssScraper[];
}
