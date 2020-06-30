import { ActionReducerMap, createSelector, MetaReducer } from '@ngrx/store';
import { rogerthatReducer, RogerthatState } from '@oca/rogerthat';
import { CallStateType, ResultState } from '@oca/shared';
import { environment } from '../environments/environment';
import { GetUserInformationResult, HoplrFeed, LookupNeighbourhoodResult } from './hoplr';
import { hoplrReducer } from './hoplr-reducer';

export interface HoplrState {
  userInformation: ResultState<GetUserInformationResult>;
  loginResult: ResultState<GetUserInformationResult>;
  registerResult: ResultState<GetUserInformationResult>;
  lookupResult: ResultState<LookupNeighbourhoodResult>;
  feed: ResultState<HoplrFeed>;
}

export interface HoplrAppState {
  rogerthat: RogerthatState;
  hoplr: HoplrState;
}


export const state: ActionReducerMap<HoplrAppState> = {
  rogerthat: rogerthatReducer,
  hoplr: hoplrReducer,
} as any;


export const metaReducers: MetaReducer<HoplrAppState>[] = environment.production ? [] : [];

const hoplrState = (s: HoplrAppState) => s.hoplr;

export const isLoggingIn = createSelector(hoplrState, s => s.loginResult.state === CallStateType.LOADING);
export const isRegistering = createSelector(hoplrState, s => s.registerResult.state === CallStateType.LOADING);

export const isLookingUpNeighbourhood = createSelector(hoplrState, s => s.lookupResult.state === CallStateType.LOADING);
export const getLookupNeighbourhoodResult = createSelector(hoplrState, s => s.lookupResult.result);

export const getFeed = createSelector(hoplrState, s => s.feed.result);
export const isFeedLoading = createSelector(hoplrState, s => s.feed.state === CallStateType.LOADING);
export const getFeedPage = createSelector(hoplrState, s => s.feed.result?.page ?? 0);

export const getUserInformation = createSelector(hoplrState, s => s.userInformation.result);
export const isUserInformationLoading = createSelector(hoplrState, s => s.userInformation.state === CallStateType.LOADING);
export const getNeighbourhood = createSelector(getUserInformation, s => s?.info?.neighbourhood);
