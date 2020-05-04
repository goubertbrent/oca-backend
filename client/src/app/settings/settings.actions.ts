import { Action } from '@ngrx/store';
import { OpeningHours, PlaceType } from '../shared/interfaces/oca';
import { Country, ServiceInfo } from './service-info/service-info';

export const enum SettingsActionTypes {
  GET_OPENING_HOURS = '[settings] Get opening hours',
  GET_OPENING_HOURS_COMPLETE = '[settings] Get opening hours complete',
  GET_OPENING_HOURS_FAILED = '[settings] Get opening hours failed',
  SAVE_OPENING_HOURS = '[settings] Save opening hours',
  SAVE_OPENING_HOURS_COMPLETE = '[settings] Save opening hours complete',
  SAVE_OPENING_HOURS_FAILED = '[settings] Save opening hours failed',
  GET_SERVICE_INFO = '[settings] Get service info',
  GET_SERVICE_INFO_COMPLETE = '[settings] Get service info complete',
  GET_SERVICE_INFO_FAILED = '[settings] Get service info failed',
  UPDATE_SERVICE_INFO = '[settings] Update service info',
  UPDATE_SERVICE_INFO_COMPLETE = '[settings] Update service info complete',
  UPDATE_SERVICE_INFO_FAILED = '[settings] Update service info failed',
  GET_AVAILABLE_PLACE_TYPES = '[settings] Get available place types',
  GET_AVAILABLE_PLACE_TYPES_COMPLETE = '[settings] Get available place types complete',
  GET_AVAILABLE_PLACE_TYPES_FAILED = '[settings] Get available place types failed',
  GET_COUNTRIES = '[settings] Get countries',
  GET_COUNTRIES_COMPLETE = '[settings] Get countries complete',
  GET_COUNTRIES_FAILED = '[settings] Get countries failed',
}

export class GetOpeningHoursAction implements Action {
  readonly type = SettingsActionTypes.GET_OPENING_HOURS;
}

export class GetOpeningHoursCompleteAction implements Action {
  readonly type = SettingsActionTypes.GET_OPENING_HOURS_COMPLETE;

  constructor(public payload: OpeningHours) {
  }
}

export class GetOpeningHoursFailedAction implements Action {
  readonly type = SettingsActionTypes.GET_OPENING_HOURS_FAILED;

  constructor(public error: string) {
  }
}

export class SaveOpeningHoursAction implements Action {
  readonly type = SettingsActionTypes.SAVE_OPENING_HOURS;

  constructor(public payload: OpeningHours) {
  }
}

export class SaveOpeningHoursCompleteAction implements Action {
  readonly type = SettingsActionTypes.SAVE_OPENING_HOURS_COMPLETE;

  constructor(public payload: OpeningHours) {
  }
}

export class SaveOpeningHoursFailedAction implements Action {
  readonly type = SettingsActionTypes.SAVE_OPENING_HOURS_FAILED;

  constructor(public error: string) {
  }
}

export class GetServiceInfoAction implements Action {
  readonly type = SettingsActionTypes.GET_SERVICE_INFO;
}

export class GetServiceInfoCompleteAction implements Action {
  readonly type = SettingsActionTypes.GET_SERVICE_INFO_COMPLETE;

  constructor(public payload: ServiceInfo) {
  }
}

export class GetServiceInfoFailedAction implements Action {
  readonly type = SettingsActionTypes.GET_SERVICE_INFO_FAILED;

  constructor(public error: string) {
  }
}

export class UpdateServiceInfoAction implements Action {
  readonly type = SettingsActionTypes.UPDATE_SERVICE_INFO;

  constructor(public payload: ServiceInfo) {
  }
}

export class UpdateServiceInfoCompleteAction implements Action {
  readonly type = SettingsActionTypes.UPDATE_SERVICE_INFO_COMPLETE;

  constructor(public payload: ServiceInfo) {
  }
}

export class UpdateServiceInfoFailedAction implements Action {
  readonly type = SettingsActionTypes.UPDATE_SERVICE_INFO_FAILED;

  constructor(public error: string) {
  }
}

export class GetAvailablePlaceTypesAction implements Action {
  readonly type = SettingsActionTypes.GET_AVAILABLE_PLACE_TYPES;
}

export class GetAvailablePlaceTypesCompleteAction implements Action {
  readonly type = SettingsActionTypes.GET_AVAILABLE_PLACE_TYPES_COMPLETE;

  constructor(public payload: PlaceType[]) {
  }
}

export class GetAvailablePlaceTypesFailedAction implements Action {
  readonly type = SettingsActionTypes.GET_AVAILABLE_PLACE_TYPES_FAILED;

  constructor(public error: string) {
  }
}

export class GetCountriesAction implements Action {
  readonly type = SettingsActionTypes.GET_COUNTRIES;
}

export class GetCountriesCompleteAction implements Action {
  readonly type = SettingsActionTypes.GET_COUNTRIES_COMPLETE;

  constructor(public payload: Country[]) {
  }
}

export class GetCountriesFailedAction implements Action {
  readonly type = SettingsActionTypes.GET_COUNTRIES_FAILED;

  constructor(public error: string) {
  }
}

export type SettingsActions =
  GetOpeningHoursAction
  | GetOpeningHoursCompleteAction
  | GetOpeningHoursFailedAction
  | SaveOpeningHoursAction
  | SaveOpeningHoursCompleteAction
  | SaveOpeningHoursFailedAction
  | GetServiceInfoAction
  | GetServiceInfoCompleteAction
  | GetServiceInfoFailedAction
  | UpdateServiceInfoAction
  | UpdateServiceInfoCompleteAction
  | UpdateServiceInfoFailedAction
  | GetAvailablePlaceTypesAction
  | GetAvailablePlaceTypesCompleteAction
  | GetAvailablePlaceTypesFailedAction
  | GetCountriesAction
  | GetCountriesCompleteAction
  | GetCountriesFailedAction;
