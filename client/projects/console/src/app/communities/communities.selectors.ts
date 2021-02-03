import { createFeatureSelector, createSelector } from '@ngrx/store';
import { CallStateType } from '@oca/web-shared';
import { CommunitiesState, communityFeatureKey } from './community.reducer';

const feat = createFeatureSelector<CommunitiesState>(communityFeatureKey);

export const getCommunities = createSelector(feat, s => s.communities.result ?? []);
export const isCommunityLoading = createSelector(feat, s => s.community.state === CallStateType.LOADING);
export const getCommunity = createSelector(feat, s => s.community.result);

export const getCommunityHomeScreen = createSelector(feat, s => s.homeScreen.result);
export const isHomeScreenLoading = createSelector(feat, s => s.homeScreen.state === CallStateType.LOADING);
export const getCurrentGeoFence = createSelector(feat, s => s.geoFence.result);
export const getCommunityMapSettings = createSelector(feat, s => s.mapSettings.result);
export const isMapSettingsLoading = createSelector(feat, s => s.mapSettings.state === CallStateType.LOADING);
