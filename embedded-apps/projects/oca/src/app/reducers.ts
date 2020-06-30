import { ActionReducerMap, MetaReducer } from '@ngrx/store';
import { RogerthatActions, rogerthatReducer, RogerthatState } from '@oca/rogerthat';
import { environment } from '../environments/environment';

export interface AppState {
  rogerthat: RogerthatState<any, any>;
}

export const reducers: ActionReducerMap<AppState, RogerthatActions> = {
  rogerthat: rogerthatReducer,
};


export const metaReducers: MetaReducer<AppState>[] = environment.production ? [] : [];
