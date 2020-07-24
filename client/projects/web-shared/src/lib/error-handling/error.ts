import { Action } from '@ngrx/store';

export interface ApiError<T = any> {
  status_code: number;
  error: string;
  data: T | null;
}


export interface ErrorAction extends Action {
  error: string;
}
