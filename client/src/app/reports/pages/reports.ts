export const enum IncidentStatus {
  NEW = 'new',
  IN_PROGRESS = 'in_progress',
  RESOLVED = 'resolved',
}

export const INCIDENT_STATUSES = [
  {value: IncidentStatus.NEW, label: 'oca.new'},
  {value: IncidentStatus.IN_PROGRESS, label: 'oca.in_progress'},
  {value: IncidentStatus.RESOLVED, label: 'oca.resolved'},
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
  external_id: string | null;
  status: IncidentStatus;
  details: IncidentDetails;
}

export interface IncidentList {
  results: Incident[];
  cursor: string | null;
  more: boolean;
}
