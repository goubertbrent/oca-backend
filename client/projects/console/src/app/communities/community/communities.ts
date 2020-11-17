export interface SimpleApp {
  id: string;
  name: string;
}

export interface AutoConnectedService {
  service_email: string;
  removable: boolean;
}

export const enum AppFeature {
  JOBS = 'jobs',
  NEWS_VIDEO = 'news_video',
  NEWS_LOCATION_FILTER = 'news_location_filter',
  NEWS_REVIEW = 'news_review',
  NEWS_REGIONAL = 'news_regional',
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
