import { createAction, props } from '@ngrx/store';
import { CommunityGeoFence } from '@oca/web-shared';
import { Community, CommunityMapSettings, CreateCommunity } from './community/communities';
import { HomeScreen } from './homescreen/models';
import { NewsGroup, NewsSettings, NewsSettingsWithGroups } from './news/news';

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

export const getGeoFence = createAction(
  '[Community] Get GeoFence',
  props<{ communityId: number }>(),
);

export const getGeoFenceSuccess = createAction(
  '[Community] Get GeoFence success',
  props<{ data: CommunityGeoFence }>(),
);

export const getGeoFenceFailure = createAction(
  '[Community] Get GeoFence Failure',
  props<{ error: string }>(),
);

export const updateGeoFence = createAction(
  '[Community] Update GeoFence',
  props<{ communityId: number; data: CommunityGeoFence }>(),
);

export const updateGeoFenceSuccess = createAction(
  '[Community] Update GeoFence success',
  props<{ data: CommunityGeoFence }>(),
);

export const updateGeoFenceFailure = createAction(
  '[Community] Update GeoFence Failure',
  props<{ error: string }>(),
);

export const getMapSettings = createAction(
  '[Community] Get MapSettings',
  props<{ communityId: number }>(),
);

export const getMapSettingsSuccess = createAction(
  '[Community] Get MapSettings success',
  props<{ data: CommunityMapSettings }>(),
);

export const getMapSettingsFailure = createAction(
  '[Community] Get MapSettings Failure',
  props<{ error: string }>(),
);

export const updateMapSettings = createAction(
  '[Community] Update MapSettings',
  props<{ communityId: number; data: CommunityMapSettings }>(),
);

export const updateMapSettingsSuccess = createAction(
  '[Community] Update MapSettings success',
  props<{ data: CommunityMapSettings }>(),
);

export const updateMapSettingsFailure = createAction(
  '[Community] Update MapSettings Failure',
  props<{ error: string }>(),
);

export const loadCommunityNewsSettings = createAction(
  '[Community] Load CommunityNewsSettings',
  props<{ communityId: number }>(),
);

export const loadCommunityNewsSettingsSuccess = createAction(
  '[Community] Load CommunityNewsSettings success',
  props<{ data: NewsSettingsWithGroups}>(),
);

export const loadCommunityNewsSettingsFailure = createAction(
  '[Community] Load CommunityNewsSettings Failure',
  props<{ error: string }>(),
);
