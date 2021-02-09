import { WeekDay } from '@angular/common';

export interface SolutionSettings {
  updates_pending: boolean;
  facebook_page: string | null;
  facebook_name: string | null;
  facebook_action: string | null;
  events_visible: boolean;
  inbox_email_reminders: boolean;
  twitter_username: string | null;
  iban: string | null;
  bic: string | null;
  publish_changes_users: string[];
}

export interface BrandingSettings {
  color_scheme: 'light' | 'dark';
  background_color: string;
  text_color: string;
  menu_item_color: string;
  show_identity_name: boolean;
  show_avatar: boolean;
  logo_url: string | null;
  avatar_url: string | null;
}

export type PlaceType = [string, string];  // value, label

export interface AvailablePlaceType {
  label: string;
  value: string;
}

export interface AvailableOtherPlaceType extends AvailablePlaceType {
  disabled: boolean;
}

export interface GlobalConfig {
  is_shop_user: boolean;
}

export interface OpeningHour {
  day: WeekDay;
  time: string;
}

export interface OpeningPeriod {
  open: OpeningHour;
  close: OpeningHour | null;
  description?: string | null;
  description_color?: string | null;
}

export interface OpeningHourException {
  start_date: string;
  end_date: string;
  description: string | null;
  description_color?: string | null;
  periods: OpeningPeriod[];
}

export const enum OpeningHourType {
  TEXTUAL = 'textual',
  STRUCTURED = 'structured',
  NOT_RELEVANT = 'not_relevant',
}

export interface BaseOpeningHours {
  type: OpeningHourType;
  text: string | null;
  periods: OpeningPeriod[];
  exceptional_opening_hours: OpeningHourException[];
}

export interface ServiceOpeningHours extends BaseOpeningHours {
  id: string;
  title: string | null;
}

export interface Country {
  name: string;
  code: string;
}

