export interface BaseButton {
  id: string;
  caption: string;
  action: string;
}

export interface ServiceMenuItemLink {
  url: string;
  external: boolean;
}

export interface FormVersion {
  id: number;
  version: number;
}

export interface ServiceMenuDetailItem {
  tag: string;
  coords: [ number, number, number ];
  label: string;
  iconHash: string;
  screenBranding: string | null;
  staticFlowHash: string | null;
  requiresWifi: boolean;
  runInBackground: boolean;
  action: number;
  roles: number[];
  link: ServiceMenuItemLink | null;
  fallThrough: boolean;
  form: FormVersion | null;
}

export interface ServiceMenuDetail {
  aboutLabel: string;
  callConfirmation: string | null;
  callLabel: string | null;
  items: ServiceMenuDetailItem[];
  messageLabel: string;
  shareLabel: string;
}

export interface ServiceIdentityInfo {
  name: string;
  email: string;
  avatar: string;
  admin_emails: string[];
  description: string;
  app_ids: string[];
  app_names: string[];
  default_app: string;
}

export interface App {
  id: string;
  name: string;
}

export interface AppStatistics {
  app_id: string;
  total_user_count: number;
}

export interface AppStatisticsMapping {
  [ key: string ]: AppStatistics;
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
