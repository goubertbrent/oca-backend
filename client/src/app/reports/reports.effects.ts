import { Injectable } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { ErrorService } from '@oca/web-shared';
import { catchError, map, switchMap, tap } from 'rxjs/operators';
import {
  GetIncidentAction,
  GetIncidentCompleteAction,
  GetIncidentFailedAction,
  GetIncidentsAction,
  GetIncidentsCompleteAction,
  GetIncidentsFailedAction,
  ReportsActions,
  ReportsActionTypes,
  UpdateIncidentAction,
  UpdateIncidentCompleteAction,
  UpdateIncidentFailedAction,
} from './reports.actions';
import { ReportsService } from './reports.service';
import { ReportsState } from './reports.state';

@Injectable({ providedIn: 'root' })
export class ReportsEffects {
   getIncidents$ = createEffect(() => this.actions$.pipe(
    ofType<GetIncidentsAction>(ReportsActionTypes.GET_INCIDENTS),
    switchMap(action => this.reportsService.getIncidents(action.payload).pipe(
      map(result => new GetIncidentsCompleteAction(result)),
      catchError(err => this.errorService.handleError(action, GetIncidentsFailedAction, err)))),
  ));

  getIncident$ = createEffect(() => this.actions$.pipe(
    ofType<GetIncidentAction>(ReportsActionTypes.GET_INCIDENT),
    switchMap(action => this.reportsService.getIncident(action.payload.id).pipe(
      map(result => new GetIncidentCompleteAction(result)),
      catchError(err => this.errorService.handleError(action, GetIncidentFailedAction, err)))),
  ));

   updateIncident$ = createEffect(() => this.actions$.pipe(
    ofType<UpdateIncidentAction>(ReportsActionTypes.UPDATE_INCIDENT),
    switchMap(action => this.reportsService.updateIncident(action.payload).pipe(
      map(result => new UpdateIncidentCompleteAction(result)),
      tap(result => this.snackbar.open(this.translate.instant('oca.incident_saved'), '', { duration: 5000 })),
      catchError(err => this.errorService.handleError(action, UpdateIncidentFailedAction, err)))),
  ));

  constructor(private actions$: Actions<ReportsActions>,
              private store: Store<ReportsState>,
              private reportsService: ReportsService,
              private snackbar: MatSnackBar,
              private translate: TranslateService,
              private errorService: ErrorService) {
  }
}
