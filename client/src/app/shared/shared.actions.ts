import { Action } from '@ngrx/store';
import { Budget } from './billing/billing';
import { ApiError } from './errors/errors';
import { BrandingSettings, GlobalConfig, SolutionSettings } from './interfaces/oca';

export const enum SharedActionTypes {
  GET_BUDGET = '[shared] Get budget',
  GET_BUDGET_COMPLETE = '[shared] Get budget complete',
  GET_BUDGET_FAILED = '[shared] Get budget failed',
  GET_SOLUTION_SETTINGS = '[shared] Get solution settings',
  GET_SOLUTION_SETTINGS_COMPLETE = '[shared] Get solution settings complete',
  GET_SOLUTION_SETTINGS_FAILED = '[shared] Get solution settings failed',
  GET_BRANDING_SETTINGS = '[shared] Get branding settings',
  GET_BRANDING_SETTINGS_COMPLETE = '[shared] Get branding settings complete',
  GET_BRANDING_SETTINGS_FAILED = '[shared] Get branding settings failed',
  UPDATE_AVATAR = '[shared] Update avatar',
  UPDATE_AVATAR_COMPLETE = '[shared] Update avatar complete',
  UPDATE_AVATAR_FAILED = '[shared] Update avatar failed',
  UPDATE_LOGO = '[shared] Update logo',
  UPDATE_LOGO_COMPLETE = '[shared] Update logo complete',
  UPDATE_LOGO_FAILED = '[shared] Update logo failed',
  GET_GLOBAL_CONFIG = '[shared] Get global config',
  GET_GLOBAL_CONFIG_COMPLETE = '[shared] Get global config complete',
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

  constructor(public error: string) {
  }
}

export class UpdateAvatarAction implements Action {
  readonly type = SharedActionTypes.UPDATE_AVATAR;

  constructor(public payload: { avatar_url: string }) {
  }
}

export class UpdateAvatarCompleteAction implements Action {
  readonly type = SharedActionTypes.UPDATE_AVATAR_COMPLETE;

  constructor(public payload: BrandingSettings) {
  }
}

export class UpdateAvatarFailedAction implements Action {
  readonly type = SharedActionTypes.UPDATE_AVATAR_FAILED;

  constructor(public error: string) {
  }
}

export class UpdateLogoAction implements Action {
  readonly type = SharedActionTypes.UPDATE_LOGO;

  constructor(public payload: { logo_url: string }) {
  }
}

export class UpdateLogoCompleteAction implements Action {
  readonly type = SharedActionTypes.UPDATE_LOGO_COMPLETE;

  constructor(public payload: BrandingSettings) {
  }
}

export class UpdateLogoFailedAction implements Action {
  readonly type = SharedActionTypes.UPDATE_LOGO_FAILED;

  constructor(public error: string) {
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
  | GetBudgetAction
  | GetBudgetCompleteAction
  | GetBudgetFailedAction
  | GetSolutionSettingsAction
  | GetSolutionSettingsCompleteAction
  | GetSolutionSettingsFailedAction
  | GetBrandingSettingsAction
  | GetBrandingSettingsCompleteAction
  | GetBrandingSettingFailedAction
  | UpdateAvatarAction
  | UpdateAvatarCompleteAction
  | UpdateAvatarFailedAction
  | UpdateLogoAction
  | UpdateLogoCompleteAction
  | UpdateLogoFailedAction
  | GetGlobalConfigAction
  | GetGlobalConfigCompleteAction;
