import { createAction, props } from '@ngrx/store';
import { Community, CreateCommunity } from './community/communities';
import { HomeScreen } from './homescreen/models';

export const loadCommunities = createAction(
  '[Community] Load Communities',
  props<{ country: string | null }>(),
);

export const loadCommunitiesSuccess = createAction(
  '[Community] Load Communities Success',
  props<{ communities: Community[] }>(),
);

export const loadCommunitiesFailure = createAction(
  '[Community] Load Communities Failure',
  props<{ error: string }>(),
);

export const loadCommunity = createAction(
  '[Community] Load Community',
  props<{ id: number }>(),
);

export const loadCommunitySuccess = createAction(
  '[Community] Load Community Success',
  props<{ community: Community }>(),
);

export const loadCommunityFailure = createAction(
  '[Community] Load Community Failure',
  props<{ error: string }>(),
);

export const createCommunity = createAction(
  '[Community] Create Community',
  props<{ community: CreateCommunity }>(),
);

export const createCommunitySuccess = createAction(
  '[Community] Create Community Success',
  props<{ community: Community }>(),
);

export const createCommunityFailure = createAction(
  '[Community] Create Community Failure',
  props<{ error: string }>(),
);

export const updateCommunity = createAction(
  '[Community] Update Community',
  props<{ id: number, community: CreateCommunity }>(),
);

export const updateCommunitySuccess = createAction(
  '[Community] Update Community Success',
  props<{ community: Community }>(),
);

export const updateCommunityFailure = createAction(
  '[Community] Update Community Failure',
  props<{ error: string }>(),
);

export const deleteCommunity = createAction(
  '[Community] Delete Community',
  props<{ id: number }>(),
);

export const deleteCommunitySuccess = createAction(
  '[Community] Delete Community Success',
  props<{ id: number }>(),
);

export const deleteCommunityFailure = createAction(
  '[Community] Delete Community Failure',
  props<{ error: string }>(),
);

export const getHomeScreen = createAction(
  '[Community] Get HomeScreen',
  props<{ communityId: number; homeScreenId: string }>(),
);

export const getHomeScreenSuccess = createAction(
  '[Community] Get HomeScreen success',
  props<{ communityId: number; homeScreenId: string; homeScreen: HomeScreen }>(),
);

export const getHomeScreenFailure = createAction(
  '[Community] Get HomeScreen Failure',
  props<{ error: string }>(),
);

export const updateHomeScreen = createAction(
  '[Community] Update HomeScreen',
  props<{ communityId: number; homeScreenId: string; homeScreen: HomeScreen}>(),
);

export const updateHomeScreenSuccess = createAction(
  '[Community] Update HomeScreen success',
  props<{ communityId: number; homeScreenId: string; homeScreen: HomeScreen }>(),
);

export const updateHomeScreenFailure = createAction(
  '[Community] Update HomeScreen Failure',
  props<{ error: string }>(),
);

export const publishHomeScreen = createAction(
  '[Community] Publish HomeScreen',
  props<{ communityId: number; homeScreenId: string;}>(),
);

export const publishHomeScreenSuccess = createAction(
  '[Community] Publish HomeScreen success',
  props<{ communityId: number; homeScreenId: string;}>(),
);

export const publishHomeScreenFailure = createAction(
  '[Community] Publish HomeScreen Failure',
  props<{ error: string }>(),
);

export const testHomeScreen = createAction(
  '[Community] Test HomeScreen',
  props<{ communityId: number; homeScreenId: string; testUser: string}>(),
);

export const testHomeScreenSuccess = createAction(
  '[Community] Test HomeScreen success',
);

export const testHomeScreenFailure = createAction(
  '[Community] Test HomeScreen Failure',
  props<{ error: string }>(),
);
