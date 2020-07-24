import { createFeatureSelector, createSelector } from '@ngrx/store';
import { CallStateType } from '@oca/web-shared';
import { newsFeatureKey, State } from './reducers';

export const selectNewsState = createFeatureSelector<State>(newsFeatureKey);

export const isCurrentNewsItemLoading = createSelector(selectNewsState, s => s.currentNewsItem.state === CallStateType.LOADING);
export const getCurrentNewsItem = createSelector(selectNewsState, s => s.currentNewsItem.result);
export const getCurrentNewsItemError = createSelector(selectNewsState, s =>
  s.currentNewsItem.state === CallStateType.ERROR ? s.currentNewsItem.error : null);
