import { Injectable } from '@angular/core';
import { Actions, Effect, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { of } from 'rxjs';
import { catchError, map, switchMap } from 'rxjs/operators';
import { GetMenuAction, GetMenuCompleteAction, GetMenuFailedAction, SharedActions, SharedActionTypes } from './shared.actions';
import { SharedService } from './shared.service';
import { getServiceMenu, SharedState } from './shared.state';

@Injectable({ providedIn: 'root' })
export class SharedEffects {
  @Effect() getForms$ = this.actions$.pipe(
    ofType<GetMenuAction>(SharedActionTypes.GET_MENU),
    switchMap(() => this.store.pipe(select(getServiceMenu))),
    switchMap(menu => {
      if (menu.success && menu.data) {
        return of(new GetMenuCompleteAction(menu.data));
      }
      return this.sharedService.getMenu().pipe(
        map(forms => new GetMenuCompleteAction(forms)),
        catchError(err => of(new GetMenuFailedAction(err))));
    }),
  );

  constructor(private actions$: Actions<SharedActions>,
              private store: Store<SharedState>,
              private sharedService: SharedService) {
  }
}
