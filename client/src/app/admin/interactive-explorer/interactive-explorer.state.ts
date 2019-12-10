import { createFeatureSelector, createSelector } from '@ngrx/store';
import { CallStateType } from '../../shared/util';
import { IScriptsState } from './scripts.state';

export const getScriptsState = createFeatureSelector<IScriptsState>('ie');

export const getScripts = createSelector(getScriptsState, s => s.scripts.result || []);
export const getScript = createSelector(getScriptsState, s => s.script.result);
export const scriptRun = createSelector(getScriptsState, s => s.scriptRun.result);
export const isScriptLoading = createSelector(getScriptsState, s => s.script.state === CallStateType.LOADING);
export const isScriptRunning = createSelector(getScriptsState, s => s.scriptRun.state === CallStateType.LOADING);
