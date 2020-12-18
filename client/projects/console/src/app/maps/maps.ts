export const enum ReportsMapFilter {
  ALL = 'all',
  NEW = 'new',
  IN_PROGRESS = 'in_progress',
  RESOLVED = 'resolved',
}

export interface MapButton {
  action: string;
  color: string | null;
  icon: string | null;
  text: string | null;
  service: string | null;
}

export interface MapConfig {
  center: {
    lat: number;
    lon: number;
  };
  distance: number;
  max_distance: number;
  filters: string[];
  default_filter: string;
  buttons: MapButton[];
}
