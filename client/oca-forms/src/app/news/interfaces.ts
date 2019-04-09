import { BaseButton } from '../rogerthat/interfaces';

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

export const enum MediaType {
  IMAGE = 'image',
}

export interface KeyValueLong {
  key: string;
  value: number;
}

export interface NewsItemStatisticsTime {
  timestamp: number;
  amount: number;
}

export interface NewsItemStatisticsDetails {
  age: KeyValueLong[];
  gender: KeyValueLong[];
  time: NewsItemStatisticsTime[];
  total: number;
}

export interface NewsItemStatistics {
  app_id: string;
  reached: NewsItemStatisticsDetails[];
  rogered: NewsItemStatisticsDetails[];
  action: NewsItemStatisticsDetails[];
  followed: NewsItemStatisticsDetails[];
}

export interface NewsTargetAudience {
  min_age: number;
  max_age: number;
  gender: Gender;
  connected_users_only: boolean;
}

export interface NewsFeedName {
  app_id: string;
  name: string;
}

export interface NewsSender {
  email: string;
  name: string;
  avatar_id: string;
}

export interface NewsActionButton extends BaseButton {
  flow_params?: string;
}

export enum NewsActionButtonType {
  WEBSITE,
  PHONE,
  EMAIL,
  ATTACHMENT,
  MENU_ITEM,
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

export type UINewsActionButton =
  NewsActionButtonWebsite
  | NewsActionButtonPhone
  | NewsActionButtonEmail
  | NewsActionButtonAttachment
  | NewsActionButtonMenuItem;

export interface BaseMedia {
  type: MediaType;
  content: string;
}

export interface Media extends BaseMedia {
  width: number;
  height: number;
}

export interface NewsItem {
  type: NewsItemType;
  sticky: boolean;
  sticky_until: number;
  app_ids: string[];
  rogered: boolean;
  scheduled_at: number;
  published: boolean;
  statistics: NewsItemStatistics[];
  action_count: number;
  follow_count: number;
  target_audience: NewsTargetAudience;
  role_ids: number[];
  tags: string[];
  feed_names: NewsFeedName[];
  id: number;
  sender: NewsSender;
  title: string;
  message: string;
  broadcast_type: string;
  reach: number;
  users_that_rogered: string[];
  buttons: NewsActionButton[];
  qr_code_content: string;
  qr_code_caption: string;
  version: number;
  timestamp: number;
  flags: number;
  media: Media;
}

export interface NewsBroadcastItem extends NewsItem {
  broadcast_on_twitter: boolean;
  broadcast_on_facebook: boolean;
}

export interface NewsBroadcastItemList {
  results: NewsBroadcastItem[];
  cursor: string | null;
  more: boolean;
}

export interface CreateNews {
  id: number | null;
  title: string;
  message: string;
  broadcast_type: string;
  action_button: NewsActionButton | null;
  type: NewsItemType;
  qr_code_caption: string | null;
  app_ids: string[];
  scheduled_at: number;
  broadcast_on_facebook: boolean;
  broadcast_on_twitter: boolean;
  facebook_access_token: string | null;
  target_audience: NewsTargetAudience;
  role_ids: number[];
  tags: string[];
  media: BaseMedia;
}

export interface NewsApp {
  id: string;
  type: number;
  name: string;
}

export interface NewsStats {
  news_item: NewsBroadcastItem;
  apps: NewsApp[];
}

export const enum NewsSettingsTag {
  FREE_REGIONAL_NEWS = 'free_regional_news'
}

export interface NewsOptions {
  broadcast_types: string[];
  editable_broadcast_types: string[];
  news_enabled: boolean;
  news_settings: {
    tags: NewsSettingsTag[];
  };
  regional_news_enabled: boolean;
  roles: number[];
}
