import { initialStateResult, PublicAppInfo, ResultState, stateError, stateLoading, stateSuccess } from '@oca/web-shared';
import { AppActions, AppActionTypes } from './app.actions';

export const appRootSelector = 'app';

export interface RootState {
  [ appRootSelector ]: AppState;
}

export interface AppState {
  appInfo: ResultState<PublicAppInfo>;
}

export const initialState: AppState = {
  appInfo: initialStateResult,
};

export const reducers = {
  [ appRootSelector ]: appReducer,
};

export function appReducer(state: AppState = initialState, action: AppActions): AppState {
  switch (action.type) {
    case AppActionTypes.GetAppInfo:
      return { ...state, appInfo: stateLoading(initialState.appInfo.result) };
    case AppActionTypes.GetAppInfoSuccess:
      return { ...state, appInfo: stateSuccess(action.payload.data) };
    case AppActionTypes.GetAppInfoFailure:
      return { ...state, appInfo: stateError(action.error, state.appInfo.result) };
  }
  return state;
}

