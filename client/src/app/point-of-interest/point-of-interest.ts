import { LatLonTO } from '@oca/web-shared';
import { BaseOpeningHours } from '../shared/interfaces/oca';
import { MediaItem } from '../shared/media-selector/media';

export type CreatePointOfInterest = Omit<PointOfInterest, 'id' | 'status'>;

export interface POILocation {
  coordinates: LatLonTO;
  google_maps_place_id: string | null;
  country: string;
  locality: string | null;
  postal_code: string | null;
  street: string | null;
  street_number: string | null;
}

export const enum POIStatus {
  // Not visible because incomplete (e.g. missing place type or location)
  INCOMPLETE = 0,
  // Visible on map
  VISIBLE = 1,
  // Not visible on map
  INVISIBLE = 2,
}

export interface PointOfInterest {
  id: number;
  title: string;
  description: string | null;
  location: POILocation;
  main_place_type: string;
  place_types: string[];
  opening_hours: BaseOpeningHours;
  media: MediaItem[];
  visible: boolean;
  readonly status: POIStatus;
}

export interface PointOfInterestList {
  cursor: string | null;
  more: boolean;
  results: PointOfInterest[];
}
