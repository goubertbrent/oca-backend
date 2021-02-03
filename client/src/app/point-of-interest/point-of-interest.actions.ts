import { createAction, props } from '@ngrx/store';
import { CreatePointOfInterest, PointOfInterest, PointOfInterestList, POIStatus } from './point-of-interest';

export const loadPointOfInterests = createAction(
  '[PointOfInterest] Load PointOfInterests',
  props<{ cursor: string | null; status: POIStatus | null; query: string | null; }>(),
);

export const loadPointOfInterestsSuccess = createAction(
  '[PointOfInterest] Load PointOfInterests Success',
  props<{ data: PointOfInterestList }>(),
);

export const loadPointOfInterestsFailure = createAction(
  '[PointOfInterest] Load PointOfInterests Failure',
  props<{ error: string }>(),
);

export const getPointOfInterest = createAction(
  '[PointOfInterest] Get PointOfInterests',
  props<{ id: number }>(),
);

export const getPointOfInterestSuccess = createAction(
  '[PointOfInterest] Get PointOfInterest Success',
  props<{ poi: PointOfInterest }>(),
);

export const getPointOfInterestFailure = createAction(
  '[PointOfInterest] Get PointOfInterest Failure',
  props<{ error: string }>(),
);

export const createPointOfInterest = createAction(
  '[PointOfInterest] Create PointOfInterests',
  props<{ data: CreatePointOfInterest }>(),
);

export const createPointOfInterestSuccess = createAction(
  '[PointOfInterest] Create PointOfInterest Success',
  props<{ poi: PointOfInterest }>(),
);

export const createPointOfInterestFailure = createAction(
  '[PointOfInterest] Create PointOfInterest Failure',
  props<{ error: string }>(),
);

export const updatePointOfInterest = createAction(
  '[PointOfInterest] Update PointOfInterests',
  props<{ id: number; data: CreatePointOfInterest }>(),
);

export const updatePointOfInterestSuccess = createAction(
  '[PointOfInterest] Update PointOfInterest Success',
  props<{ poi: PointOfInterest }>(),
);

export const updatePointOfInterestFailure = createAction(
  '[PointOfInterest] Update PointOfInterest Failure',
  props<{ error: string }>(),
);

export const deletePointOfInterest = createAction(
  '[PointOfInterest] Delete PointOfInterests',
  props<{ id: number }>(),
);

export const deletePointOfInterestSuccess = createAction(
  '[PointOfInterest] Delete PointOfInterest Success',
  props<{ id: number }>(),
);

export const deletePointOfInterestFailure = createAction(
  '[PointOfInterest] Delete PointOfInterest Failure',
  props<{ error: string }>(),
);
