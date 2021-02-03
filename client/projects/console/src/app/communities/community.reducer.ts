import { createReducer, on } from '@ngrx/store';
import { CommunityGeoFence, initialStateResult, ResultState, stateError, stateLoading, stateSuccess } from '@oca/web-shared';
import { removeItem } from '../ngrx';
import {
  createCommunity,
  createCommunityFailure,
  createCommunitySuccess,
  deleteCommunitySuccess,
  getGeoFence,
  getGeoFenceFailure,
  getGeoFenceSuccess,
  getHomeScreen,
  getHomeScreenFailure,
  getHomeScreenSuccess,
  getMapSettings,
  getMapSettingsFailure,
  getMapSettingsSuccess,
  loadCommunities,
  loadCommunitiesFailure,
  loadCommunitiesSuccess,
  loadCommunity,
  loadCommunityFailure,
  loadCommunitySuccess,
  updateCommunity,
  updateCommunityFailure,
  updateCommunitySuccess,
  updateGeoFence,
  updateGeoFenceFailure,
  updateGeoFenceSuccess,
  updateHomeScreen,
  updateHomeScreenFailure,
  updateHomeScreenSuccess,
  updateMapSettings,
  updateMapSettingsFailure,
  updateMapSettingsSuccess,
} from './community.actions';
import { Community, CommunityMapSettings } from './community/communities';
import { HomeScreen } from './homescreen/models';


export const communityFeatureKey = 'community';

export interface CommunitiesState {
  communities: ResultState<Community[]>;
  community: ResultState<Community>;
  homeScreen: ResultState<HomeScreen>;
  geoFence: ResultState<CommunityGeoFence>;
  mapSettings: ResultState<CommunityMapSettings>;
}

export const initialState: CommunitiesState = {
  communities: initialStateResult,
  community: initialStateResult,
  homeScreen: initialStateResult,
  geoFence: initialStateResult,
  mapSettings: initialStateResult,
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
  on(updateHomeScreen, (state, { homeScreen }) => ({ ...state, homeScreen: stateLoading(homeScreen) })),
  on(updateHomeScreenSuccess, (state, { homeScreen }) => ({ ...state, homeScreen: stateSuccess(homeScreen) })),
  on(updateHomeScreenFailure, (state, { error }) => ({ ...state, homeScreen: stateError(error, state.homeScreen.result) })),
  on(getGeoFence, (state) => ({ ...state, geoFence: stateLoading(state.geoFence.result) })),
  on(getGeoFenceSuccess, (state, { data }) => ({ ...state, geoFence: stateSuccess(data) })),
  on(getGeoFenceFailure, (state, { error }) => ({ ...state, geoFence: stateError(error, state.geoFence.result) })),
  on(updateGeoFence, (state, action) => ({ ...state, geoFence: stateLoading(action.data) })),
  on(updateGeoFenceSuccess, (state, { data }) => ({ ...state, geoFence: stateSuccess(data) })),
  on(updateGeoFenceFailure, (state, { error }) => ({ ...state, geoFence: stateError(error, state.geoFence.result) })),
  on(getMapSettings, (state) => ({ ...state, mapSettings: stateLoading(state.mapSettings.result) })),
  on(getMapSettingsSuccess, (state, { data }) => ({ ...state, mapSettings: stateSuccess(data) })),
  on(getMapSettingsFailure, (state, { error }) => ({ ...state, mapSettings: stateError(error, state.mapSettings.result) })),
  on(updateMapSettings, (state, action) => ({ ...state, mapSettings: stateLoading(action.data) })),
  on(updateMapSettingsSuccess, (state, { data }) => ({ ...state, mapSettings: stateSuccess(data) })),
  on(updateMapSettingsFailure, (state, { error }) => ({ ...state, mapSettings: stateError(error, state.mapSettings.result) })),
);
