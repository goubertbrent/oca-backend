export interface Project {
  action_count: number;
  city_id: number;
  budget: {
    amount: number;
    currency: string;
  };
  description: string;
  end_date: string;
  id: number;
  start_date: string;
  title: string;
}

export interface ProjectDetails extends Project {
  statistics: {
    total: number;
    personal: {
      total: number;
      last_entry_date: string;
    }
  };
}

export interface DayTime {
  /**
   * A number from 0–6, corresponding to the days of the week, starting on Sunday.
   * For example, 2 means Tuesday.
   */
  day: number;
  /**
   * `time` may contain a time of day in 24-hour hhmm format.
   * Values are in the range 0000–2359.
   * The time will be reported in the place’s time zone.
   */
  time: string;
}

export interface OpeningHourPeriod {
  /**
   * `open` contains a pair of day and time objects describing when the place opens:
   */
  open: DayTime;
  /**
   * `close` may contain a pair of day and time objects describing when the place closes.
   * Note: If a place is always open, the close section will be missing from the response.
   * Clients can rely on always-open being represented as an open period containing day with value 0 and time with value 0000, and no close.
   */
  close: DayTime;
}

export interface OpeningHours {
  /**
   * A boolean value indicating if the place is open at the current time.
   */
  open_now: boolean;
  open_until: string;
  periods: OpeningHourPeriod[];
  weekday_text: {
    day: string;
    hours: string[];
  }[];
}

export interface GeoPoint {
  lat: number;
  lon: number;
}

export interface AppMerchant {
  city_id: number;
  formatted_address: string;
  formatted_phone_number: string | null;
  id: number;
  location: GeoPoint;
  name: string;
  opening_hours: OpeningHours | null;
  place_id: string;
  place_url: string | null;
  website: string | null;
  photos: { url: string }[];
}

export interface AppMerchantList {
  results: AppMerchant[];
  cursor: string | null;
  more: boolean;
}


export interface AddParticipationData {
  qr_content: string;
  project_id: number;
  email: string;
  app_id: string;
}

export interface City {
  id: number;
  name: string;
  info: string;
  avatar_url: string;
}


export interface UserSettings {
  tour_date: Date | null;
}
