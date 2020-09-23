import { createReducer, on } from '@ngrx/store';
import { initialStateResult, ResultState, stateError, stateLoading, stateSuccess } from '@oca/web-shared';
import {
  createCommunity,
  createCommunityFailure,
  createCommunitySuccess,
  loadCommunity,
  loadCommunityFailure,
  loadCommunitySuccess,
  updateCommunity,
  updateCommunityFailure,
  updateCommunitySuccess,
} from './community.actions';
import { Community } from './community/communities';


export const communityFeatureKey = 'community';

export interface CommunitiesState {
  community: ResultState<Community>;
}

export const initialState: CommunitiesState = {
  community: initialStateResult,
};

export const communitiesReducer = createReducer(
  initialState,
  on(loadCommunity, (state) => ({ ...state, community: stateLoading(initialState.community.result) })),
  on(loadCommunitySuccess, (state, { community }) => ({ ...state, community: stateSuccess(community) })),
  on(loadCommunityFailure, (state, { error }) => ({ ...state, community: stateError(error, state.community.result) })),
  on(createCommunity, (state, _) => ({ ...state, community: stateLoading(initialState.community.result) })),
  on(createCommunitySuccess, (state, { community }) => ({ ...state, community: stateSuccess(community) })),
  on(createCommunityFailure, (state, { error }) => ({ ...state, community: stateError(error, initialState.community.result) })),
  on(updateCommunity, (state, { community }) => ({ ...state, community: stateLoading({ ...state.community.result!!, ...community }) })),
  on(updateCommunitySuccess, (state, { community }) => ({ ...state, community: stateSuccess(community) })),
  on(updateCommunityFailure, (state, { error }) => ({ ...state, community: stateError(error, state.community.result) })),
);
