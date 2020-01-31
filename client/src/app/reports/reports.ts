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

export const INCIDENT_STATUSES = [
  { value: IncidentStatus.NEW, label: 'oca.new', icon: 'report', color: '#ff3d29', mapIcon: 'map-icon-red.svg' },
  { value: IncidentStatus.IN_PROGRESS, label: 'oca.in_progress', icon: 'timelapse', color: '#FF9900', mapIcon: 'map-icon-orange.svg' },
  { value: IncidentStatus.RESOLVED, label: 'oca.resolved', icon: 'done', color: '#00E64D', mapIcon: 'map-icon-green.svg' },
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
  year: number;
  month: number;
  data: [
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

export interface IncidentStatsPerMonth {
  year: number;
  month: number;
  data: IncidentStatistics[];
}

export interface TagFilterMapping {
  [ key: string ]: TagFilter;
}

export interface TagFilter {
  id: string;
  type: IncidentTagType;
  name: string;
}

export interface IncidentStatisticsFilter {
  years: number[];
  months: number[];
}


export interface Chart {
  chartType: string;
  dataTable: (string | number)[][];
  columnNames: string[];
  options: google.visualization.BarChartOptions;
}
