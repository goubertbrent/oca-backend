export interface CreateProject {
  action_count: number;
  budget: {
    amount: number;
    currency: string;
  };
  description: string;
  end_date: string | Date;
  start_date: string | Date;
  title: string;
}

export interface Project extends CreateProject {
  city_id: string;
  id: number;
}

export interface MerchantStatistics {
  id: number;
  total: number;
  formatted_address: string;
  location: {
    lat: number;
    lon: number;
  };
  name: string;
}

export interface ProjectStatistics {
  project_id: number;
  total: number;
  results: MerchantStatistics[];
  cursor: string | null;
  more: boolean;
}

export interface CitySettings {
  id: string;
  info: string;
}
