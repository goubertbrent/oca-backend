import { stateError, stateLoading, stateSuccess } from '@oca/web-shared';
import { removeItem } from '../../shared/util';
import { Script } from './scripts';
import { ScriptsActions, ScriptsActionTypes } from './scripts.actions';
import { initialScriptsState, IScriptsState } from './scripts.state';

export function scriptsReducer(state: IScriptsState = initialScriptsState, action: ScriptsActions): IScriptsState {
  switch (action.type) {
    case ScriptsActionTypes.GET_SCRIPTS:
      return { ...state, scripts: stateLoading(initialScriptsState.scripts.result) };
    case ScriptsActionTypes.GET_SCRIPTS_COMPLETE:
      return { ...state, scripts: stateSuccess(action.payload) };
    case ScriptsActionTypes.GET_SCRIPTS_FAILED:
      return { ...state, scripts: stateError(action.error, state.scripts.result) };
    case ScriptsActionTypes.GET_SCRIPT:
      return {
        ...state,
        script: stateLoading(initialScriptsState.script.result),
        scriptRun: initialScriptsState.scriptRun,
      };
    case ScriptsActionTypes.GET_SCRIPT_COMPLETE:
      return { ...state, script: stateSuccess(action.payload) };
    case ScriptsActionTypes.GET_SCRIPT_FAILED:
      return { ...state, script: stateError(action.error, initialScriptsState.script.result) };
    case ScriptsActionTypes.CREATE_SCRIPT:
      return { ...state, script: stateLoading(initialScriptsState.script.result) };
    case ScriptsActionTypes.CREATE_SCRIPT_COMPLETE:
      return { ...state, script: stateSuccess(action.payload) };
    case ScriptsActionTypes.CREATE_SCRIPT_FAILED:
      return { ...state, script: stateError(action.error, state.script.result) };
    case ScriptsActionTypes.UPDATE_SCRIPT:
      return { ...state, script: stateLoading(action.payload) };
    case ScriptsActionTypes.UPDATE_SCRIPT_COMPLETE:
      return { ...state, script: stateSuccess(action.payload) };
    case ScriptsActionTypes.UPDATE_SCRIPT_FAILED:
      return { ...state, script: stateError(action.error, state.script.result) };
    case ScriptsActionTypes.DELETE_SCRIPT:
      return { ...state, script: stateLoading(state.script.result) };
    case ScriptsActionTypes.DELETE_SCRIPT_COMPLETE:
      return {
        ...state,
        scripts: stateSuccess(removeItem(state.scripts.result as Script[], action.payload, 'id')),
        script: initialScriptsState.script,
      };
    case ScriptsActionTypes.DELETE_SCRIPT_FAILED:
      return { ...state, script: stateError(action.error, state.script.result) };
    case ScriptsActionTypes.RUN_SCRIPT:
      return { ...state, scriptRun: stateLoading(initialScriptsState.scriptRun.result) };
    case ScriptsActionTypes.RUN_SCRIPT_COMPLETE:
      return {
        ...state,
        script: stateSuccess(action.payload.script),
        scriptRun: stateSuccess(action.payload),
      };
    case ScriptsActionTypes.RUN_SCRIPT_FAILED:
      return { ...state, scriptRun: stateError(action.error, initialScriptsState.scriptRun.result) };
    default:
      return state;
  }
}
