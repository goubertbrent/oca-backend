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

export interface MarkerProperties {
  'name': string;
  'icon': Icon;
};

 export interface Icon {
  'icon_fa': string;
  'icon_color': string;
}

