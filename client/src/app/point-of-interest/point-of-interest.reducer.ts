import { createReducer, on } from '@ngrx/store';
import { initialStateResult, ResultState, stateError, stateLoading, stateSuccess } from '@oca/web-shared';
import { insertItem, removeItem, updateItem } from '../shared/util';
import { PointOfInterest, PointOfInterestList, POIStatus } from './point-of-interest';
import * as Actions from './point-of-interest.actions';

export const pointOfInterestFeatureKey = 'pointOfInterest';

export interface State {
  poiList: ResultState<PointOfInterestList>;
  currentPOI: ResultState<PointOfInterest>;
  poiFilter: {
    status: POIStatus | null;
    query: string | null;
  };
}

export const initialState: State = {
  poiList: initialStateResult,
  currentPOI: initialStateResult,
  poiFilter: {
    status: null,
    query: null,
  },
};


export const pointOfInterestReducer = createReducer(
  initialState,
  on(Actions.loadPointOfInterests, (state, action) => ({
    ...state,
    poiList: stateLoading(action.cursor ? state.poiList.result : initialState.poiList.result),
    poiFilter: { query: action.query, status: action.status },
  })),
  on(Actions.loadPointOfInterestsSuccess, (state, action) => ({
    ...state,
    poiList: stateSuccess(state.poiList.result?.results ? {
      ...action.data,
      results: [...state.poiList.result.results, ...action.data.results],
    } : action.data),
  })),
  on(Actions.loadPointOfInterestsFailure, (state, action) => ({ ...state, poiList: stateError(action.error, state.poiList.result) })),
  on(Actions.getPointOfInterest, state => ({ ...state, currentPOI: stateLoading(state.currentPOI.result) })),
  on(Actions.getPointOfInterestSuccess, Actions.updatePointOfInterestSuccess, (state, action) => ({
    ...state,
    currentPOI: stateSuccess(action.poi),
    poiList: state.poiList.result ? stateSuccess({
      ...state.poiList.result,
      results: updateItem(state.poiList.result.results, action.poi, 'id'),
    }) : state.poiList,
  })),
  on(Actions.getPointOfInterestFailure, (s, action) => ({ ...s, currentPOI: stateError(action.error, s.currentPOI.result) })),
  on(Actions.createPointOfInterest, state => ({ ...state, currentPOI: stateLoading(state.currentPOI.result) })),
  on(Actions.createPointOfInterestSuccess, (state, action) => ({
    ...state,
    currentPOI: stateSuccess(action.poi),
    pointOfInterests: state.poiList.result ? stateSuccess({
      ...state.poiList.result,
      results: insertItem(state.poiList.result.results, action.poi, 0),
    }) : state.poiList,
  })),
  on(Actions.createPointOfInterestFailure, (s, action) => ({ ...s, currentPOI: stateError(action.error, s.currentPOI.result) })),
  on(Actions.updatePointOfInterest, state => ({ ...state, currentPOI: stateLoading(state.currentPOI.result) })),
  on(Actions.updatePointOfInterestFailure, (s, action) => ({ ...s, currentPOI: stateError(action.error, s.currentPOI.result) })),
  on(Actions.deletePointOfInterest, state => ({ ...state, currentPOI: stateLoading(state.currentPOI.result) })),
  on(Actions.deletePointOfInterestSuccess, (state, action) => ({
    ...state,
    currentPOI: initialState.currentPOI,
    poiList: state.poiList.result ?
      stateSuccess({ ...state.poiList.result, results: removeItem(state.poiList.result.results, action.id, 'id') }) :
      state.poiList,
  })),
  on(Actions.deletePointOfInterestFailure, (state, action) => ({
    ...state,
    currentPOI: stateError(action.error, state.currentPOI.result),
  })),
);

