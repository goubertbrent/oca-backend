export interface EventAnnouncement {
  image_url?: string;
  color_theme?: string;
  title?: string;
  description?: string;
}

export interface EventAnnouncementList {
  items: EventAnnouncement[];
  title?: string;
  title_theme?: string;
}

export enum CalendarType {
  SINGLE = 'single',
  MULTIPLE = 'multiple',
  PERIODIC = 'periodic',
  PERMANENT = 'permanent',
}

export interface EventDateDate {
  date: string;
}

export interface EventDateTime {
  datetime: string;
}

export type EventDate = EventDateDate | EventDateTime;

export interface EventPeriod {
  start: EventDate;
  end: EventDate;
}

export const enum OpeningHourDay {
  SUNDAY,
  MONDAY,
  TUESDAY,
  WEDNESDAY,
  THURSDAY,
  FRIDAY,
  SATURDAY
}

export interface EventOpeningPeriod {
  open: string;
  close: string | null;
  day: OpeningHourDay;
}

export const enum EventMediaType {
  IMAGE = 'image',
}

export interface EventMedia {
  url: string;
  thumbnail_url: string;
  type: EventMediaType;
  copyright: string | null;
}

export interface OcaEvent {
  id: number;
  title: string;
  place: string;
  description: string;
  url: string | null;
  calendar_type: CalendarType;
  start_date: string;
  end_date: string;
  periods: EventPeriod[];
  opening_hours: EventOpeningPeriod[];
  media: EventMedia[];
  external_link: string;
  calendar_id: string;
  organizer: string;
  service_user_email: string;
}

export interface OcaEventList {
  cursor: string | null;
  events: OcaEvent[];
  has_more: boolean;
}

export interface EventListItem {
  id: number;
  calendarSummary: string;
  title: string;
  place: string;
  icon: string;
  startDate: Date;
  imageUrl: string | null;
}

export interface GetEventsParams {
  cursor?: string | null;
  query?: string | null;
  startDate: string;
  endDate: string;
  period?: EventFilterPeriod;
}

export interface AddToCalendarParams {
  id: number;
  service_user_email: string;
  date: string;
}

export const enum EventFilterPeriod {
  TODAY,
  TOMORROW,
  THIS_WEEKEND,
  NEXT_7,
  NEXT_30,
  RANGE,
}
