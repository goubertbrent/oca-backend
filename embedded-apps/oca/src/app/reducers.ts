import { ActionReducerMap, MetaReducer } from '@ngrx/store';
import { environment } from '../environments/environment';
import { RogerthatActions } from './rogerthat/rogerthat.actions';
import { rogerthatReducer } from './rogerthat/rogerthat.reducer';
import { RogerthatState } from './rogerthat/rogerthat.state';

export interface AppState {
  rogerthat: RogerthatState<any, any>;
}

export const reducers: ActionReducerMap<AppState, RogerthatActions> = {
  rogerthat: rogerthatReducer,
};


export const metaReducers: MetaReducer<AppState>[] = environment.production ? [] : [];
