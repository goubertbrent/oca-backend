import { ActionReducerMap, MetaReducer } from '@ngrx/store';
import { RogerthatActions, rogerthatReducer, RogerthatState } from '@oca/rogerthat';
import { environment } from '../environments/environment';
import { QMaticActions } from './q-matic/q-matic-actions';
import { qmaticReducer } from './q-matic/q-matic-reducer';
import { Q_MATIC_FEATURE, QMaticState } from './q-matic/q-matic.state';

export interface QMState {
  rogerthat: RogerthatState<any, any>;
  [Q_MATIC_FEATURE]: QMaticState;
}

export const reducers: ActionReducerMap<QMState, RogerthatActions & QMaticActions> = {
  rogerthat: rogerthatReducer,
  [Q_MATIC_FEATURE]: qmaticReducer,
};


export const metaReducers: MetaReducer<QMState>[] = environment.production ? [] : [];
