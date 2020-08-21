import { ToolbarItem } from '../interfaces/toolbar.interfaces';

export interface IToolbarState {
  items: ToolbarItem[];
}

export const initialToolbarState: IToolbarState = {
  items: [],
};
