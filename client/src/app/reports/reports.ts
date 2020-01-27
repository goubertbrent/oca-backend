export const enum ReportsMapFilter {
  ALL = 'all',
  NEW = 'new',
  IN_PROGRESS = 'in_progress',
  RESOLVED = 'resolved',
}

export const enum IncidentStatus {
  NEW = 'new',
  IN_PROGRESS = 'in_progress',
  RESOLVED = 'resolved',
}

export const INCIDENT_STATUSES: { value: IncidentStatus; label: string }[] = [
  { value: IncidentStatus.NEW, label: 'oca.new' },
  { value: IncidentStatus.IN_PROGRESS, label: 'oca.in_progress' },
  { value: IncidentStatus.RESOLVED, label: 'oca.resolved' },
];

export interface IncidentStatusDate {
  date: string;
  status: IncidentStatus;
}

export interface IncidentDetails {
  title: string;
  description: string;
  geo_location: { lat: number; lon: number; };
}

export interface Incident {
  id: string;
  user_id: string;
  user_consent: boolean;
  report_date: string;
  status_dates: IncidentStatusDate[];
  visible: boolean;
  integration: string;
  source: string;
  external_id: string;
  status: IncidentStatus;
  details: IncidentDetails;
}

export interface IncidentList {
  results: Incident[];
  cursor: string | null;
  more: boolean;
}

export interface IdName {
  id: string;
  name: string;
}

export const enum IncidentTagType {
  CATEGORY = 'category',
  SUBCATEGORY = 'subcategory',
}

export interface IncidentStatisticsList {
  results: {
    year: number;
    months: number[];
  }[];
  categories: IdName[];
  subcategories: IdName[];
}

export interface RawIncidentStatistics {
  statistics: [
    string,  // Incident id
    IncidentStatus[],
    string[],  // tags
    [number, number] | [], // optional location
  ][];
}

export interface IncidentStatistics {
  incidentId: string;
  statuses: IncidentStatus[];
  tags: string[];
  location: {
    lat: number;
    lon: number;
  } | null;
}

export interface TagFilterMapping {
  [ key: string ]: TagFilter;
}

export interface TagFilter {
  id: string;
  type: IncidentTagType;
  name: string;
}
