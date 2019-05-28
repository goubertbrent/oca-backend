export interface CreateProject {
  action_count: number;
  budget: {
    amount: number;
    currency: string;
  };
  description: string;
  end_date: string | Date | null;
  start_date: string | Date | null;
  title: string;
}

export interface Project extends CreateProject {
  city_id: string;
  id: number;
}

export interface ProjectStatistics {
  project_id: number;
  total: number;
  results: {
    id: number;
    total: number;
    name: string;
  }[];
  cursor: string | null;
  more: boolean;
}

export interface CitySettings {
  id: string;
  info: string;
}
