export interface PublicAppInfo {
  app_id: string;
  name: string;
  url_name: string;
  logo_url: string;
  cover_url: string;
}

export interface App {
  id: string;
  name: string;
}

export interface AppStatistics {
  app_id: string;
  total_user_count: number;
}

export interface AppStatisticsMapping {
  [ key: string ]: AppStatistics;
}
