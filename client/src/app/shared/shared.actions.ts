import { Action } from '@ngrx/store';
import { Budget } from './billing/billing';
import { ApiError } from './errors/errors';
import { BrandingSettings, GlobalConfig, SolutionSettings } from './interfaces/oca';
import { App, AppStatistics, ServiceIdentityInfo, ServiceMenuDetail } from './interfaces/rogerthat';

export const enum SharedActionTypes {
  GET_MENU = '[shared] Get menu',
  GET_MENU_COMPLETE = '[shared] Get menu complete',
  GET_MENU_FAILED = '[shared] Get menu failed',
  GET_INFO = '[shared] Get info',
  GET_INFO_COMPLETE = '[shared] Get info complete',
  GET_INFO_FAILED = '[shared] Get info failed',
  GET_APPS = '[shared] Get apps',
  GET_APPS_COMPLETE = '[shared] Get apps complete',
  GET_APPS_FAILED = '[shared] Get apps failed',
  GET_APP_STATISTICS = '[shared] Get app statistics',
  GET_APP_STATISTICS_COMPLETE = '[shared] Get app statistics complete',
  GET_APP_STATISTICS_FAILED = '[shared] Get app statistics failed',
  GET_BUDGET = '[shared] Get budget',
  GET_BUDGET_COMPLETE = '[shared] Get budget complete',
  GET_BUDGET_FAILED = '[shared] Get budget failed',
  GET_SOLUTION_SETTINGS = '[shared] Get solution settings',
  GET_SOLUTION_SETTINGS_COMPLETE = '[shared] Get solution settings complete',
  GET_SOLUTION_SETTINGS_FAILED = '[shared] Get solution settings failed',
  GET_BRANDING_SETTINGS = '[shared] Get branding settings',
  GET_BRANDING_SETTINGS_COMPLETE = '[shared] Get branding settings complete',
  GET_BRANDING_SETTINGS_FAILED = '[shared] Get branding settings failed',
  GET_GLOBAL_CONFIG= '[shared] Get global config',
  GET_GLOBAL_CONFIG_COMPLETE = '[shared] Get global config complete',
}

export class GetMenuAction implements Action {
  readonly type = SharedActionTypes.GET_MENU;
}

export class GetMenuCompleteAction implements Action {
  readonly type = SharedActionTypes.GET_MENU_COMPLETE;

  constructor(public payload: ServiceMenuDetail) {
  }
}

export class GetMenuFailedAction implements Action {
  readonly type = SharedActionTypes.GET_MENU_FAILED;

  constructor(public error: ApiError) {
  }
}

export class GetInfoAction implements Action {
  readonly type = SharedActionTypes.GET_INFO;
}

export class GetInfoCompleteAction implements Action {
  readonly type = SharedActionTypes.GET_INFO_COMPLETE;

  constructor(public payload: ServiceIdentityInfo) {
  }
}

export class GetInfoFailedAction implements Action {
  readonly type = SharedActionTypes.GET_INFO_FAILED;

  constructor(public error: ApiError) {
  }
}

export class GetAppsAction implements Action {
  readonly type = SharedActionTypes.GET_APPS;
}

export class GetAppsCompleteAction implements Action {
  readonly type = SharedActionTypes.GET_APPS_COMPLETE;

  constructor(public payload: App[]) {
  }
}

export class GetAppsFailedAction implements Action {
  readonly type = SharedActionTypes.GET_APPS_FAILED;

  constructor(public error: ApiError) {
  }
}

export class GetAppStatisticsAction implements Action {
  readonly type = SharedActionTypes.GET_APP_STATISTICS;
}

export class GetAppStatisticsCompleteAction implements Action {
  readonly type = SharedActionTypes.GET_APP_STATISTICS_COMPLETE;

  constructor(public payload: AppStatistics[]) {
  }
}

export class GetAppStatisticsFailedAction implements Action {
  readonly type = SharedActionTypes.GET_APP_STATISTICS_FAILED;

  constructor(public error: ApiError) {
  }
}

export class GetBudgetAction implements Action {
  readonly type = SharedActionTypes.GET_BUDGET;
}

export class GetBudgetCompleteAction implements Action {
  readonly type = SharedActionTypes.GET_BUDGET_COMPLETE;

  constructor(public payload: Budget) {
  }
}

export class GetBudgetFailedAction implements Action {
  readonly type = SharedActionTypes.GET_BUDGET_FAILED;

  constructor(public error: ApiError) {
  }
}

export class GetSolutionSettingsAction implements Action {
  readonly type = SharedActionTypes.GET_SOLUTION_SETTINGS;
}

export class GetSolutionSettingsCompleteAction implements Action {
  readonly type = SharedActionTypes.GET_SOLUTION_SETTINGS_COMPLETE;

  constructor(public payload: SolutionSettings) {
  }
}

export class GetSolutionSettingsFailedAction implements Action {
  readonly type = SharedActionTypes.GET_SOLUTION_SETTINGS_FAILED;

  constructor(public error: ApiError) {
  }
}

export class GetBrandingSettingsAction implements Action {
  readonly type = SharedActionTypes.GET_BRANDING_SETTINGS;
}

export class GetBrandingSettingsCompleteAction implements Action {
  readonly type = SharedActionTypes.GET_BRANDING_SETTINGS_COMPLETE;

  constructor(public payload: BrandingSettings) {
  }
}

export class GetBrandingSettingFailedAction implements Action {
  readonly type = SharedActionTypes.GET_BRANDING_SETTINGS_FAILED;

  constructor(public error: ApiError) {
  }
}

export class GetGlobalConfigAction implements Action {
  readonly type = SharedActionTypes.GET_GLOBAL_CONFIG;
}

export class GetGlobalConfigCompleteAction implements Action {
  readonly type = SharedActionTypes.GET_GLOBAL_CONFIG_COMPLETE;

  constructor(public payload: GlobalConfig) {
  }
}

export type SharedActions =
  GetMenuAction
  | GetMenuCompleteAction
  | GetMenuFailedAction
  | GetInfoAction
  | GetInfoCompleteAction
  | GetInfoFailedAction
  | GetAppsAction
  | GetAppsCompleteAction
  | GetAppsFailedAction
  | GetAppStatisticsAction
  | GetAppStatisticsCompleteAction
  | GetAppStatisticsFailedAction
  | GetBudgetAction
  | GetBudgetCompleteAction
  | GetBudgetFailedAction
  | GetSolutionSettingsAction
  | GetSolutionSettingsCompleteAction
  | GetSolutionSettingsFailedAction
  | GetBrandingSettingsAction
  | GetBrandingSettingsCompleteAction
  | GetBrandingSettingFailedAction
  | GetGlobalConfigAction
  | GetGlobalConfigCompleteAction;
