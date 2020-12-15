import { ActionReducerMap, createFeatureSelector, createSelector, MetaReducer } from '@ngrx/store';
import { rogerthatReducer, RogerthatState } from '@oca/rogerthat';
import { CallStateType, ResultState } from '@oca/shared';
import { environment } from '../environments/environment';
import {
  GetStreetsResult,
  supportedIcons,
  TrashActivity,
  TrashCollection,
  TrashHouseNumber,
  UITrashCollection,
  unknownIcon,
} from './trash';
import { trashReducer } from './trash-reducer';

export interface TrashUserDataValue {
  address: string;
  collections?: TrashCollection[];
  notifications?: string[];
  notification_types?: TrashActivity[];
}

export interface TrashUserData {
  trash?: TrashUserDataValue;
}

export interface TrashServiceData {
  settings?: {
    app_name?: string;
    name?: string;
    address?: string;
    address_url?: string;
    avatar_url?: string;
    logo_url?: string;
  };
}

export interface TrashState {
  streets: ResultState<GetStreetsResult>;
  houseNumbers: ResultState<TrashHouseNumber[]>;
  setAddress: ResultState<null>;
  setNotifications: ResultState<null>;
}

export interface TrashAppState {
  rogerthat: RogerthatState<TrashUserData>;
  trash: TrashState;
}


export const state: ActionReducerMap<TrashAppState> = {
  rogerthat: rogerthatReducer,
  trash: trashReducer,
} as any;


export const metaReducers: MetaReducer<TrashAppState>[] = environment.production ? [] : [];

const getState = (s: TrashAppState) => s.trash;

export const getStreets = createSelector(getState, s => s.streets.result);
export const areStreetsLoading = createSelector(getState, s => s.streets.state === CallStateType.LOADING);
export const getHouseNumbers = createSelector(getState, s => s.houseNumbers.result ?? []);
export const areHouseNumbersLoading = createSelector(getState, s => s.houseNumbers.state === CallStateType.LOADING);

export const isSavingAddress = createSelector(getState, s => s.setAddress.state === CallStateType.LOADING);
export const isSavingNotifications = createSelector(getState, s => s.setNotifications.state === CallStateType.LOADING);

const getRogerthatState = createFeatureSelector<RogerthatState<TrashUserData, TrashServiceData>>('rogerthat');
export const getLogoUrl = createSelector(getRogerthatState, s => s.serviceData.settings?.logo_url);

export const getTrashUserdata = createSelector(getRogerthatState, s => s.userData.trash);
export const getCurrentAddress = createSelector(getTrashUserdata, s => s?.address);
export const getNotifications = createSelector(getTrashUserdata, s => s?.notifications ?? []);
export const canSetNotifications = createSelector(getTrashUserdata, s => !!s?.address);
export const getNotificationTypes = createSelector(getTrashUserdata, s => s?.notification_types ?? []);

export const getCollections = createSelector(getTrashUserdata, s => {
  const collections = s?.collections ?? [];
  const collectionMap = new Map<number, UITrashCollection>();
  const today = new Date();
  const today0 = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  for (const collection of collections) {
    const date = getDate(collection.epoch);
    // skip dates in the past
    if (date >= today0) {
      const epoch = date.getTime();
      const uiCollection = collectionMap.get(epoch) ?? { date, epoch, activities: [] };
      let icon = collection.activity.icon;
      if (!supportedIcons.includes(icon)) {
        icon = unknownIcon;
      }
      uiCollection.activities.push({ name: collection.activity.name, iconUrl: `/assets/images/${icon}.png` });
      collectionMap.set(epoch, uiCollection);
    }
  }
  return Array.from(collectionMap.values()).sort((first, second) => first.epoch - second.epoch);
});

function getDate(epoch: number): Date {
  const date = new Date(epoch * 1000);
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

