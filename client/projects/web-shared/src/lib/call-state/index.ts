import { Action, select, Selector, Store } from '@ngrx/store';
import { map, take } from 'rxjs/operators';

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

export function stateError<ErrType, ResultType>(error: ErrType, result: ResultType | null): ResultStateError<ResultType | null, ErrType> {
  return {
    result,
    state: CallStateType.ERROR,
    error,
  };
}

export interface ResultStateInitial {
  readonly result: null;
  readonly state: CallStateType.INITIAL;
}

export interface ResultStateLoading<ResultType> {
  readonly result: ResultType | null;
  readonly state: CallStateType.LOADING;
}

export interface ResultStateSuccess<ResultType> {
  readonly result: ResultType;
  readonly state: CallStateType.SUCCESS;
}

export interface ResultStateError<ResultType, ErrorType> {
  readonly result: ResultType | null;
  readonly state: CallStateType.ERROR;
  readonly error: ErrorType;
}

export type ResultState<ResultType, ErrorType = string> =
  ResultStateInitial
  | ResultStateLoading<ResultType | null>
  | ResultStateSuccess<ResultType>
  | ResultStateError<ResultType | null, ErrorType>;


export function isStatus<T extends ResultState<any, any>>(status: CallStateType) {
  return map((value: T) => value.state === status);
}


/**
 * Dispatches `action` based on the value of the result returned by `selector`
 * Used for dispatching actions to fetch data that should only be fetched once when loading
 * a part of the dashboard.
 */
export function maybeDispatchAction<T>(store: Store<T>,
                                       selector: Selector<T, ResultState<any>>,
                                       action: Action) {
  store.pipe(select(selector), take(1)).subscribe(state => {
    if ([CallStateType.INITIAL, CallStateType.ERROR].includes(state.state)) {
      store.dispatch(action);
    }
  });
}
