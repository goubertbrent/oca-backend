import { Action } from '@ngrx/store';
import { ErrorAction } from '@oca/web-shared';
import { CreateScriptPayload, RunResult, RunScript, Script } from './scripts';

export const enum ScriptsActionTypes {
  GET_SCRIPTS = '[IE] Get scripts',
  GET_SCRIPTS_COMPLETE = '[IE] Get scripts complete',
  GET_SCRIPTS_FAILED = '[IE] Get scripts failed',
  GET_SCRIPT = '[IE] Get script',
  GET_SCRIPT_COMPLETE = '[IE] Get script complete',
  GET_SCRIPT_FAILED = '[IE] Get script failed',
  CREATE_SCRIPT = '[IE] Create script',
  CREATE_SCRIPT_COMPLETE = '[IE] Create script complete',
  CREATE_SCRIPT_FAILED = '[IE] Create script failed',
  UPDATE_SCRIPT = '[IE] Update script',
  UPDATE_SCRIPT_COMPLETE = '[IE] Update script complete',
  UPDATE_SCRIPT_FAILED = '[IE] Update script failed',
  DELETE_SCRIPT = '[IE] Delete script',
  DELETE_SCRIPT_COMPLETE = '[IE] Delete script complete',
  DELETE_SCRIPT_FAILED = '[IE] Delete script failed',
  RUN_SCRIPT = '[IE] Run script',
  RUN_SCRIPT_COMPLETE = '[IE] Run script complete',
  RUN_SCRIPT_FAILED = '[IE] Run script failed',
}

export class GetScriptsAction implements Action {
  readonly type = ScriptsActionTypes.GET_SCRIPTS;
}

export class GetScriptsCompleteAction implements Action {
  readonly type = ScriptsActionTypes.GET_SCRIPTS_COMPLETE;

  constructor(public payload: Script[]) {
  }
}

export class GetScriptsFailedAction implements ErrorAction {
  readonly type = ScriptsActionTypes.GET_SCRIPTS_FAILED;

  constructor(public error: string) {
  }
}

export class GetScriptAction implements Action {
  readonly type = ScriptsActionTypes.GET_SCRIPT;

  constructor(public payload: number) {
  }
}

export class GetScriptCompleteAction implements Action {
  readonly type = ScriptsActionTypes.GET_SCRIPT_COMPLETE;

  constructor(public payload: Script) {
  }
}

export class GetScriptFailedAction implements ErrorAction {
  readonly type = ScriptsActionTypes.GET_SCRIPT_FAILED;

  constructor(public error: string) {
  }
}

export class CreateScriptAction implements Action {
  readonly type = ScriptsActionTypes.CREATE_SCRIPT;

  constructor(public payload: CreateScriptPayload) {
  }
}

export class CreateScriptCompleteAction implements Action {
  readonly type = ScriptsActionTypes.CREATE_SCRIPT_COMPLETE;

  constructor(public payload: Script) {
  }
}

export class CreateScriptFailedAction implements ErrorAction {
  readonly type = ScriptsActionTypes.CREATE_SCRIPT_FAILED;

  constructor(public error: string) {
  }
}

export class UpdateScriptAction implements Action {
  readonly type = ScriptsActionTypes.UPDATE_SCRIPT;

  constructor(public payload: Script) {
  }
}

export class UpdateScriptCompleteAction implements Action {
  readonly type = ScriptsActionTypes.UPDATE_SCRIPT_COMPLETE;

  constructor(public payload: Script) {
  }
}

export class UpdateScriptFailedAction implements ErrorAction {
  readonly type = ScriptsActionTypes.UPDATE_SCRIPT_FAILED;

  constructor(public error: string) {
  }
}

export class DeleteScriptAction implements Action {
  readonly type = ScriptsActionTypes.DELETE_SCRIPT;

  constructor(public payload: number) {
  }
}

export class DeleteScriptCompleteAction implements Action {
  readonly type = ScriptsActionTypes.DELETE_SCRIPT_COMPLETE;

  constructor(public payload: number) {
  }
}

export class DeleteScriptFailedAction implements ErrorAction {
  readonly type = ScriptsActionTypes.DELETE_SCRIPT_FAILED;

  constructor(public error: string) {
  }
}

export class RunScriptAction implements Action {
  readonly type = ScriptsActionTypes.RUN_SCRIPT;

  constructor(public payload: RunScript) {
  }
}

export class RunScriptCompleteAction implements Action {
  readonly type = ScriptsActionTypes.RUN_SCRIPT_COMPLETE;

  constructor(public payload: RunResult) {
  }
}

export class RunScriptFailedAction implements ErrorAction {
  readonly type = ScriptsActionTypes.RUN_SCRIPT_FAILED;

  constructor(public error: string) {
  }
}

export type ScriptsActions
  = GetScriptsAction
  | GetScriptsCompleteAction
  | GetScriptsFailedAction
  | GetScriptAction
  | GetScriptCompleteAction
  | GetScriptFailedAction
  | CreateScriptAction
  | CreateScriptCompleteAction
  | CreateScriptFailedAction
  | UpdateScriptAction
  | UpdateScriptCompleteAction
  | UpdateScriptFailedAction
  | DeleteScriptAction
  | DeleteScriptCompleteAction
  | DeleteScriptFailedAction
  | RunScriptAction
  | RunScriptCompleteAction
  | RunScriptFailedAction;
