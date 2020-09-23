import { createAction, props } from '@ngrx/store';
import { Community, CreateCommunity } from './community/communities';

export const loadCommunity = createAction(
  '[Community] Load Community',
  props<{ id: number }>(),
);

export const loadCommunitySuccess = createAction(
  '[Community] Load Community Success',
  props<{ community: Community }>(),
);

export const loadCommunityFailure = createAction(
  '[Community] Load Community Failure',
  props<{ error: string }>(),
);

export const createCommunity = createAction(
  '[Community] Create Community',
  props<{ community: CreateCommunity }>(),
);

export const createCommunitySuccess = createAction(
  '[Community] Create Community Success',
  props<{ community: Community }>(),
);

export const createCommunityFailure = createAction(
  '[Community] Create Community Failure',
  props<{ error: string }>(),
);

export const updateCommunity = createAction(
  '[Community] Update Community',
  props<{ id: number, community: CreateCommunity }>(),
);

export const updateCommunitySuccess = createAction(
  '[Community] Update Community Success',
  props<{ community: Community }>(),
);

export const updateCommunityFailure = createAction(
  '[Community] Update Community Failure',
  props<{ error: string }>(),
);
