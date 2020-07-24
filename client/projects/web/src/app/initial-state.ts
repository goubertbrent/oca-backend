import { Action, MemoizedSelector, select, Store } from '@ngrx/store';
import { take } from 'rxjs/operators';
import { RootState } from './app.reducer';

// Defined in index.html
declare var oca: undefined | {
  mainLanguage: string;
  translations: {
    // key: language
    [ key: string ]: {
      // key: translation key
      [ key: string ]: string;
    };
  };
  initialState: RootState;
};

export function getInitialState(): typeof oca | undefined {
  return typeof oca === 'undefined' ? undefined : oca;
}

/**
 * If equalFn returns true, this indicates that the action should not be dispatched because the expected item is already in the state
 */
export function maybeDispatch<T>(store: Store<RootState>,
                                 selector: MemoizedSelector<object, T>,
                                 equalFn: (element: T) => boolean,
                                 action: Action) {
  store.pipe(select(selector), take(1)).subscribe(result => {
    if (!equalFn(result)) {
      store.dispatch(action);
    }
  });
}
