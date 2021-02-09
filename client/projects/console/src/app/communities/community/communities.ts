import { LatLonTO } from '@oca/web-shared';

export interface SimpleApp {
  id: string;
  name: string;
}

export interface AutoConnectedService {
  service_email: string;
  removable: boolean;
}

export const enum AppFeature {
  EVENTS_SHOW_MERCHANTS = 'events_show_merchants',
  JOBS = 'jobs',
  NEWS_VIDEO = 'news_video',
  NEWS_LOCATION_FILTER = 'news_location_filter',
  NEWS_REVIEW = 'news_review',
  NEWS_REGIONAL = 'news_regional',
  LOYALTY = 'loyalty',
}

export const enum CustomizationFeature {
  HOME_ADDRESS_IN_USER_DATA,
}

export interface CreateCommunity {
  auto_connected_services: AutoConnectedService[];
  name: string;
  country: string;
  default_app: string;
  demo: boolean;
  embedded_apps: string[];
  main_service: string | null;
  signup_enabled: boolean;
  features: AppFeature[];
  customization_features: CustomizationFeature[];
}

export interface Community extends CreateCommunity {
  id: number;
  create_date: string;
}

export interface UpdateNewsImagePayload {
  file: any;
}

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

export interface MapLayerSettings {
  filters: string[];
  default_filter: string | null;
  buttons: MapButton[];
}

export interface MapLayers {
  gipod: MapLayerSettings;
  poi: MapLayerSettings;
  reports: MapLayerSettings;
  services: MapLayerSettings;
}

export interface CommunityMapSettings {
  center: LatLonTO | null;
  distance: number | null;
  layers: MapLayers;
}
