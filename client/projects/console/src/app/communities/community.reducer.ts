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
  getHomeScreen,
  getHomeScreenFailure,
  getHomeScreenSuccess,
  loadCommunity,
  loadCommunityFailure,
  loadCommunitySuccess,
  updateCommunity,
  updateCommunityFailure,
  updateCommunitySuccess, updateHomeScreen, updateHomeScreenFailure, updateHomeScreenSuccess,
} from './community.actions';
import { Community } from './community/communities';
import { HomeScreen } from './homescreen/models';


export const communityFeatureKey = 'community';

export interface CommunitiesState {
  communities: ResultState<Community[]>;
  community: ResultState<Community>;
  homeScreen: ResultState<HomeScreen>;
}

export const initialState: CommunitiesState = {
  communities: initialStateResult,
  community: initialStateResult,
  homeScreen: initialStateResult,
};

export const communitiesReducer = createReducer(
  initialState,
  on(loadCommunities, (state) => ({ ...state, communities: stateLoading(initialState.communities.result) })),
  on(loadCommunitiesSuccess, (state, { communities }) => ({ ...state, communities: stateSuccess(communities) })),
  on(loadCommunitiesFailure, (state, { error }) => ({ ...state, communities: stateError(error, state.communities.result) })),
  on(loadCommunity, (state) => ({ ...state, community: stateLoading(initialState.community.result) })),
  on(loadCommunitySuccess, (state, { community }) => ({ ...state, community: stateSuccess(community) })),
  on(loadCommunityFailure, (state, { error }) => ({ ...state, community: stateError(error, state.community.result) })),
  on(createCommunity, state => ({ ...state, community: stateLoading(initialState.community.result) })),
  on(createCommunitySuccess, (state, { community }) => ({ ...state, community: stateSuccess(community) })),
  on(createCommunityFailure, (state, { error }) => ({ ...state, community: stateError(error, initialState.community.result) })),
  on(updateCommunity, (state, { community }) => ({ ...state, community: stateLoading({ ...state.community.result!!, ...community }) })),
  on(updateCommunitySuccess, (state, { community }) => ({ ...state, community: stateSuccess(community) })),
  on(updateCommunityFailure, (state, { error }) => ({ ...state, community: stateError(error, state.community.result) })),
  on(deleteCommunitySuccess, (state, { id }) => ({
    ...state,
    communities: state.communities.result ? stateSuccess(removeItem(state.communities.result, id, 'id')) : state.communities,
  })),
  on(getHomeScreen, state => ({ ...state, homeScreen: stateLoading(state.homeScreen.result) })),
  on(getHomeScreenSuccess, (state, { homeScreen }) => ({ ...state, homeScreen: stateSuccess(homeScreen) })),
  on(getHomeScreenFailure, (state, { error }) => ({ ...state, homeScreen: stateError(error, state.homeScreen.result) })),
  on(updateHomeScreen, (state, {homeScreen}) => ({ ...state, homeScreen: stateLoading(homeScreen) })),
  on(updateHomeScreenSuccess, (state, { homeScreen }) => ({ ...state, homeScreen: stateSuccess(homeScreen) })),
  on(updateHomeScreenFailure, (state, { error }) => ({ ...state, homeScreen: stateError(error, state.homeScreen.result) })),
);
