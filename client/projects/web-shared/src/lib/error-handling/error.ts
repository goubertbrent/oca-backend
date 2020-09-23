import { Action, ActionCreator } from '@ngrx/store';
import { TypedAction } from '@ngrx/store/src/models';

export interface ApiError<T = any> {
  status_code: number;
  error: string;
  data: T | null;
}


export interface ErrorAction extends Action {
  error: string;
}

export type ErrorActionCreator<T extends string> = ActionCreator<T, (props: { error: string }) => { error: string } & TypedAction<T>>;
export type ErrorActionCreatorOrErrorAction<T extends string> = ErrorActionCreator<T> | (new(error: string) => ErrorAction);
