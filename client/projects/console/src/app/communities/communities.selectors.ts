import { createFeatureSelector, createSelector } from '@ngrx/store';
import { CallStateType } from '@oca/web-shared';
import { CommunitiesState, communityFeatureKey } from './community.reducer';

const feat = createFeatureSelector<CommunitiesState>(communityFeatureKey);

export const isCommunityLoading = createSelector(feat, s => s.community.state === CallStateType.LOADING);
export const getCommunity = createSelector(feat, s => s.community.result);
