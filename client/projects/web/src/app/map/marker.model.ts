import {MapSectionTO} from "@oca/web-shared";

export interface Marker {
  'type': string;
  'id': string;
  geometry: Geometry;
  properties: MarkerProperties;
}

export interface Geometry {
  'coordinates': number[];
  'type': string;
}

export interface MarkerDetails {
  name: string;
  address: Address;
  email: string;
  phone_number: string;
  description: string;
  sections: MapSectionTO[];
}

export interface SelectedMarker {
  id: string;
  properties: MarkerDetails;
  type: string;
  geometry: Geometry;
}

export interface MarkerProperties {
  id: string;
  // See MarkerDetails
  data: string;
  icon: string;
  icon_color: string;
}

export interface Icon {
  'icon_fa': string;
  'icon_color': string;
}

export interface Address {
  'street': string;
  'postal_code': string;
  'street_number': string;
}
