import { createReducer, on } from '@ngrx/store';
import { initialStateResult, ResultState, stateError, stateLoading, stateSuccess } from '@oca/web-shared';
import { removeItem } from '../ngrx';
import {
  createCommunity,
  createCommunityFailure,
  createCommunitySuccess,
  deleteCommunitySuccess,
  loadCommunities,
  loadCommunitiesFailure,
  loadCommunitiesSuccess,
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
  communities: ResultState<Community[]>;
  community: ResultState<Community>;
}

export const initialState: CommunitiesState = {
  communities: initialStateResult,
  community: initialStateResult,
};

export const communitiesReducer = createReducer(
  initialState,
  on(loadCommunities, (state) => ({ ...state, communities: stateLoading(initialState.communities.result) })),
  on(loadCommunitiesSuccess, (state, { communities }) => ({ ...state, communities: stateSuccess(communities) })),
  on(loadCommunitiesFailure, (state, { error }) => ({ ...state, communities: stateError(error, state.communities.result) })),
  on(loadCommunity, (state) => ({ ...state, community: stateLoading(initialState.community.result) })),
  on(loadCommunitySuccess, (state, { community }) => ({ ...state, community: stateSuccess(community) })),
  on(loadCommunityFailure, (state, { error }) => ({ ...state, community: stateError(error, state.community.result) })),
  on(createCommunity, (state, _) => ({ ...state, community: stateLoading(initialState.community.result) })),
  on(createCommunitySuccess, (state, { community }) => ({ ...state, community: stateSuccess(community) })),
  on(createCommunityFailure, (state, { error }) => ({ ...state, community: stateError(error, initialState.community.result) })),
  on(updateCommunity, (state, { community }) => ({ ...state, community: stateLoading({ ...state.community.result!!, ...community }) })),
  on(updateCommunitySuccess, (state, { community }) => ({ ...state, community: stateSuccess(community) })),
  on(updateCommunityFailure, (state, { error }) => ({ ...state, community: stateError(error, state.community.result) })),
  on(deleteCommunitySuccess, (state, { id }) => ({
    ...state,
    communities: state.communities.result ? stateSuccess(removeItem(state.communities.result, id, 'id')) : state.communities,
  })),
);
