export interface CommunityLocation {
  locality: string;
  postal_code: string;
}

export interface GeoFenceGeometry {
  center: {
    lat: number;
    lon: number;
  };
  max_distance: number;
}

export interface CommunityGeoFence {
  country: string;
  defaults: CommunityLocation | null;
  geometry: GeoFenceGeometry | null;
}
