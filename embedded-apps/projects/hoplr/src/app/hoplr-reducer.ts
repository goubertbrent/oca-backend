import { initialStateResult, stateError, stateLoading, stateSuccess } from '@oca/shared';
import { HoplrActions, HoplrActionTypes } from './hoplr.actions';
import { HoplrState } from './state';

export const initialHoplrState: HoplrState = {
  userInformation: initialStateResult,
  loginResult: initialStateResult,
  registerResult: initialStateResult,
  lookupResult: initialStateResult,
  feed: initialStateResult,
};

export function hoplrReducer(state = initialHoplrState, action: HoplrActions): HoplrState {
  switch (action.type) {
    case HoplrActionTypes.GET_USER_INFORMATION:
      return { ...state, userInformation: stateLoading(initialHoplrState.userInformation.result) };
    case HoplrActionTypes.GET_USER_INFORMATION_SUCCESS:
      return { ...state, userInformation: stateSuccess(action.payload) };
    case HoplrActionTypes.GET_USER_INFORMATION_FAILED:
      return { ...state, userInformation: stateError(action.error, initialHoplrState.userInformation.result) };
    case HoplrActionTypes.LOGIN:
      return { ...state, loginResult: stateLoading(initialHoplrState.loginResult.result) };
    case HoplrActionTypes.LOGIN_SUCCESS:
      return {
        ...state,
        loginResult: stateSuccess(action.payload),
        userInformation: stateSuccess(action.payload),
      };
    case HoplrActionTypes.LOGIN_FAILED:
      return { ...state, loginResult: stateError(action.error, initialHoplrState.loginResult.result) };
    case HoplrActionTypes.REGISTER:
      return { ...state, registerResult: stateLoading(initialHoplrState.registerResult.result) };
    case HoplrActionTypes.REGISTER_SUCCESS:
      return {
        ...state,
        registerResult: stateSuccess(action.payload),
        userInformation: stateSuccess(action.payload),
      };
    case HoplrActionTypes.REGISTER_FAILED:
      return { ...state, registerResult: stateError(action.error, initialHoplrState.registerResult.result) };
    case HoplrActionTypes.LOOKUP_NEIGHBOURHOOD:
      return { ...state, lookupResult: stateLoading(initialHoplrState.lookupResult.result) };
    case HoplrActionTypes.LOOKUP_NEIGHBOURHOOD_SUCCESS:
      return { ...state, lookupResult: stateSuccess(action.payload) };
    case HoplrActionTypes.LOOKUP_NEIGHBOURHOOD_FAILED:
      return { ...state, lookupResult: stateError(action.error, initialHoplrState.lookupResult.result) };
    case HoplrActionTypes.GET_FEED:
      return { ...state, feed: stateLoading(action.payload.page ? state.feed.result : initialHoplrState.feed.result) };
    case HoplrActionTypes.GET_FEED_SUCCESS:
      return {
        ...state,
        feed: stateSuccess(state.feed.result
          ? { ...action.payload, results: [...state.feed.result.results, ...action.payload.results] }
          : { ...action.payload, results: action.payload.results },
        ),
      };
    case HoplrActionTypes.GET_FEED_FAILED:
      return { ...state, feed: stateError(action.error, state.feed.result) };
    case HoplrActionTypes.LOGOUT_SUCCESS:
      return initialHoplrState;
  }
  return state;
}
