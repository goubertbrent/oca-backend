import { Injectable } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Actions, Effect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { catchError, map, switchMap, tap } from 'rxjs/operators';
import { ErrorService } from '../shared/errors/error.service';
import { GetGlobalConfigAction } from '../shared/shared.actions';
import {
  GetIncidentAction,
  GetIncidentCompleteAction,
  GetIncidentsAction,
  GetIncidentsCompleteAction,
  GetIncidentsFailedAction,
  GetMapConfigAction,
  GetMapConfigCompleteAction,
  GetMapConfigFailedAction,
  ReportsActions,
  ReportsActionTypes,
  SaveMapConfigAction,
  SaveMapConfigCompleteAction,
  SaveMapConfigFailedAction,
  UpdateIncidentAction,
  UpdateIncidentCompleteAction,
  UpdateIncidentFailedAction,
} from './reports.actions';
import { ReportsService } from './reports.service';
import { ReportsState } from './reports.state';

@Injectable({ providedIn: 'root' })
export class ReportsEffects {
  @Effect() getIncidents$ = this.actions$.pipe(
    ofType<GetIncidentsAction>(ReportsActionTypes.GET_INCIDENTS),
    switchMap(action => this.reportsService.getIncidents(action.payload).pipe(
      map(result => new GetIncidentsCompleteAction(result)),
      catchError(err => this.errorService.handleError(action, GetIncidentsFailedAction, err)))),
  );

  @Effect() getIncident$ = this.actions$.pipe(
    ofType<GetIncidentAction>(ReportsActionTypes.GET_INCIDENT),
    switchMap(action => this.reportsService.getIncident(action.payload.id).pipe(
      map(result => new GetIncidentCompleteAction(result)),
      catchError(err => this.errorService.handleError(action, SaveMapConfigFailedAction, err)))),
  );

  @Effect() updateIncident$ = this.actions$.pipe(
    ofType<UpdateIncidentAction>(ReportsActionTypes.UPDATE_INCIDENT),
    switchMap(action => this.reportsService.updateIncident(action.payload).pipe(
      map(result => new UpdateIncidentCompleteAction(result)),
      tap(result => this.snackbar.open(this.translate.instant('oca.incident_saved'), '', { duration: 5000 })),
      catchError(err => this.errorService.handleError(action, UpdateIncidentFailedAction, err)))),
  );

  @Effect() getMapConfig$ = this.actions$.pipe(
    ofType<GetMapConfigAction>(ReportsActionTypes.GET_MAP_CONFIG),
    switchMap(action => this.reportsService.getMapConfig().pipe(
      map(result => new GetMapConfigCompleteAction(result)),
      catchError(err => this.errorService.handleError(action, GetMapConfigFailedAction, err)))),
  );

  @Effect() saveMapConfig$ = this.actions$.pipe(
    ofType<SaveMapConfigAction>(ReportsActionTypes.SAVE_MAP_CONFIG),
    switchMap(action => this.reportsService.saveMapConfig(action.payload).pipe(
      map(result => new SaveMapConfigCompleteAction(result)),
      tap(result => this.snackbar.open(this.translate.instant('oca.settings_saved'), '', { duration: 5000 })),
      catchError(err => this.errorService.handleError(action, SaveMapConfigFailedAction, err)))),
  );

  constructor(private actions$: Actions<ReportsActions>,
              private store: Store<ReportsState>,
              private reportsService: ReportsService,
              private snackbar: MatSnackBar,
              private translate: TranslateService,
              private errorService: ErrorService) {
    this.store.dispatch(new GetGlobalConfigAction());
  }
}
