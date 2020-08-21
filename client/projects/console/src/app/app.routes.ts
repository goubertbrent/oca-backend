import { Data, Route as AngularRoute } from '@angular/router';

export interface RouteMetadata {
  title: string;
  description: string;
  keywords: string;

  [ key: string ]: string;
}

export interface RouteDataWithId extends Data {
  id?: string;
  description?: string;
  /**
   * Icon for sidebar item
   */
  icon?: string;
  /**
   * Label for sidebar item and/or page title
   */
  label?: string;
}
export type RouteData = Data | RouteDataWithId;

export interface Route extends AngularRoute {
  data?: RouteData;
}
