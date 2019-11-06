import { Injectable } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { Actions, Effect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { catchError, map, switchMap } from 'rxjs/operators';
import { ErrorService } from '../shared/errors/error.service';
import {
  GetIncidentAction, GetIncidentCompleteAction, GetIncidentFailedAction,
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
  SaveMapConfigFailedAction, UpdateIncidentAction, UpdateIncidentCompleteAction, UpdateIncidentFailedAction,
} from './reports.actions';
import { ReportsService } from './reports.service';
import { ReportsState } from './reports.state';

@Injectable({ providedIn: 'root' })
export class ReportsEffects {
  // TODO: error handling (dialog?)(
  @Effect() getIncidents$ = this.actions$.pipe(
    ofType<GetIncidentsAction>(ReportsActionTypes.GET_INCIDENTS),
    switchMap(() => this.reportsService.getIncidents().pipe(
      map(result => new GetIncidentsCompleteAction(result)),
      catchError(err => this.errorService.toAction(GetIncidentsFailedAction, err)))),
  );

  @Effect() getIncident$ = this.actions$.pipe(
    ofType<GetIncidentAction>(ReportsActionTypes.GET_INCIDENT),
    switchMap(action => this.reportsService.getIncident(action.payload.id).pipe(
      map(result => new GetIncidentCompleteAction(result)),
      catchError(err => this.errorService.toAction(GetIncidentFailedAction, err)))),
  );

  @Effect() updateIncident$ = this.actions$.pipe(
    ofType<UpdateIncidentAction>(ReportsActionTypes.UPDATE_INCIDENT),
    switchMap(action => this.reportsService.updateIncident(action.payload).pipe(
      map(result => new UpdateIncidentCompleteAction(result)),
      catchError(err => this.errorService.toAction(UpdateIncidentFailedAction, err)))),
  );

  @Effect() getMapConfig$ = this.actions$.pipe(
    ofType<GetMapConfigAction>(ReportsActionTypes.GET_MAP_CONFIG),
    switchMap(() => this.reportsService.getMapConfig().pipe(
      map(result => new GetMapConfigCompleteAction(result)),
      catchError(err => this.errorService.toAction(GetMapConfigFailedAction, err)))),
  );

  @Effect() saveMapConfig$ = this.actions$.pipe(
    ofType<SaveMapConfigAction>(ReportsActionTypes.SAVE_MAP_CONFIG),
    switchMap(action => this.reportsService.saveMapConfig(action.payload).pipe(
      map(result => new SaveMapConfigCompleteAction(result)),
      catchError(err => this.errorService.toAction(SaveMapConfigFailedAction, err)))),
  );

  constructor(private actions$: Actions<ReportsActions>,
              private store: Store<ReportsState>,
              private reportsService: ReportsService,
              private errorService: ErrorService,
              private snackbar: MatSnackBar,
              private translate: TranslateService,
              private router: Router) {
  }
}
