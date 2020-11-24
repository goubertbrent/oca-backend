import { Injectable } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { TranslateService } from '@ngx-translate/core';
import { ErrorService } from '@oca/web-shared';
import { catchError, map, switchMap, tap } from 'rxjs/operators';
import {
  GetMapConfigAction,
  GetMapConfigCompleteAction,
  GetMapConfigFailedAction,
  SaveMapConfigAction,
  SaveMapConfigCompleteAction,
  SaveMapConfigFailedAction,
} from './maps.actions';
import { MapsService } from './maps.service';

@Injectable({ providedIn: 'root' })
export class MapsEffects {
  getMapConfig$ = createEffect(() => this.actions$.pipe(
    ofType(GetMapConfigAction),
    switchMap(action => this.mapsService.getMapConfig(action.appId).pipe(
      map(payload => GetMapConfigCompleteAction({ payload })),
      catchError(err => this.errorService.handleError(action, GetMapConfigFailedAction, err)))),
  ));

  saveMapConfig$ = createEffect(() => this.actions$.pipe(
    ofType(SaveMapConfigAction),
    switchMap(action => this.mapsService.saveMapConfig(action.appId, action.payload).pipe(
      map(payload => SaveMapConfigCompleteAction({ payload })),
      tap(result => this.snackbar.open('Settings saved', '', { duration: 5000 })),
      catchError(err => this.errorService.handleError(action, SaveMapConfigFailedAction, err)))),
  ));

  constructor(private actions$: Actions,
              private mapsService: MapsService,
              private snackbar: MatSnackBar,
              private translate: TranslateService,
              private errorService: ErrorService) {
  }
}
