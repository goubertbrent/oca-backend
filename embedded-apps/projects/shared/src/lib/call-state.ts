import { map } from 'rxjs/operators';

export const enum CallStateType {
  INITIAL,
  LOADING,
  SUCCESS,
  ERROR
}

export const initialStateResult: ResultStateInitial = {
  result: null,
  state: CallStateType.INITIAL,
};

export function stateLoading<T>(result: T | null): ResultStateLoading<T | null> {
  return {
    result,
    state: CallStateType.LOADING,
  };
}

export function stateSuccess<T>(result: T): ResultStateSuccess<T> {
  return {
    result,
    state: CallStateType.SUCCESS,
  };
}

export function stateError<ErrorType, ResultType>(error: ErrorType, result: ResultType | null): ResultStateError<ResultType | null, ErrorType> {
  return {
    result,
    state: CallStateType.ERROR,
    error,
  };
}

export interface ResultStateInitial {
  result: null;
  state: CallStateType.INITIAL;
}

export interface ResultStateLoading<ResultType> {
  result: ResultType | null;
  state: CallStateType.LOADING;
}

export interface ResultStateSuccess<ResultType> {
  result: ResultType;
  state: CallStateType.SUCCESS;
}

export interface ResultStateError<ResultType, ErrorType> {
  result: ResultType | null;
  state: CallStateType.ERROR;
  error: ErrorType;
}

export type ResultState<ResultType, ErrorType = string> =
  ResultStateInitial
  | ResultStateLoading<ResultType | null>
  | ResultStateSuccess<ResultType>
  | ResultStateError<ResultType | null, ErrorType>;


export function isStatus<T extends ResultState<any, any>>(status: CallStateType) {
  return map((value: T) => value.state === status);
}

export const EMPTY_ARRAY: any[] = [];

export function resultOrEmptyArray<ResultType extends Array<any>, ErrorType>(result: ResultState<ResultType, ErrorType>): ResultType {
  if (result.state === CallStateType.SUCCESS) {
    return result.result;
  } else {
    return EMPTY_ARRAY as ResultType;
  }
}
