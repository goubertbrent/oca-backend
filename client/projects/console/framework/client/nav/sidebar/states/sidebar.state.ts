import { Route } from '../../../../../src/app/app.routes';
import { SidebarItem } from '../interfaces';

export interface ISidebarState {
  routes: Route[];
  sidebarItems: SidebarItem[];
}

export const initialSidebarState: ISidebarState = {
  routes: [],
  sidebarItems: [],
};
