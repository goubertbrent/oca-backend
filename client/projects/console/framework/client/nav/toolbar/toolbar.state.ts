import { createFeatureSelector, createSelector } from '@ngrx/store';
import { ToolbarItem } from './toolbar.interfaces';

export interface IToolbarState {
  items: ToolbarItem[];
}

export const initialToolbarState: IToolbarState = {
  items: [],
};

export const selectToolbarState = createFeatureSelector<IToolbarState>('toolbar');
export const getToolbarItems = createSelector(selectToolbarState, s => s.items);
