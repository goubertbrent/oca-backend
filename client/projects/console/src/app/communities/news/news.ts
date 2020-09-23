export interface UpdateNewsImagePayload {
  file: any;
}

export interface NewsGroupTile {
  background_image_url: string;
  promo_image_url: string;
  title: string;
  subtitle: string;
}

export interface NewsGroup {
  group_id: string;
  name: string;
  send_notifications: boolean;
  default_notifications_enabled: boolean;
  group_type: string;
  tile: NewsGroupTile;
}

export const enum NewsStreamTypes {
  CITY = 'city',
  COMMUNITY = 'community',
}

export interface NewsSettings {
  stream_type: NewsStreamTypes;
}

export interface NewsSettingsWithGroups extends NewsSettings {
  groups: NewsGroup[];
}

export const NEWS_STREAM_TYPES = [
  { value: NewsStreamTypes.CITY, label: 'rcc.news_stream_type_city' },
  { value: NewsStreamTypes.COMMUNITY, label: 'rcc.news_stream_type_community' },
];
