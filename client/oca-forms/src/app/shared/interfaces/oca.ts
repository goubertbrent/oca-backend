export interface SolutionSettings {
  name: string;
  description: string;
  opening_hours: string;
  address: string;
  phone_number: string | null;
  updates_pending: boolean;
  facebook_page: string | null;
  facebook_name: string | null;
  facebook_action: string | null;
  currency: string;
  search_enabled: boolean;
  timezone: string;
  events_visible: boolean;
  event_notifications_enabled: boolean;
  search_keywords: string;
  email_address: string;
  inbox_email_reminders: boolean;
  twitter_username: string | null;
  holidays: number[];
  holiday_out_of_office_message: string;
  iban: string | null;
  bic: string | null;
  publish_changes_users: string[];
  search_enabled_check: boolean;
  location: {
    lat: number;
    lon: number;
  } | null;
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
