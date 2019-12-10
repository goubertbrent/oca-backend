import { initialStateResult, ResultState } from '../../shared/util';
import { RunResult, Script } from './scripts';

export interface IScriptsState {
  scripts: ResultState<Script[]>;
  script: ResultState<Script>;
  scriptRun: ResultState<RunResult>;
}

export const initialScriptsState: IScriptsState = {
  scripts: initialStateResult,
  script: initialStateResult,
  scriptRun: initialStateResult,
};
