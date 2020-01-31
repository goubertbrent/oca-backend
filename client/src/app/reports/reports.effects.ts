import { Injectable } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Actions, Effect, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { catchError, map, switchMap, tap, withLatestFrom } from 'rxjs/operators';
import { ErrorService } from '../shared/errors/error.service';
import {
  GetIncidentAction,
  GetIncidentCompleteAction,
  GetIncidentsAction,
  GetIncidentsCompleteAction,
  GetIncidentsFailedAction,
  GetIncidentStatisticsAction,
  GetIncidentStatisticsCompleteAction,
  GetIncidentStatisticsFailedAction,
  GetMapConfigAction,
  GetMapConfigCompleteAction,
  GetMapConfigFailedAction,
  ListIncidentStatisticsAction,
  ListIncidentStatisticsCompleteAction,
  ListIncidentStatisticsFailedAction,
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
import { getAllIncidentStatistics, ReportsState } from './reports.state';

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

  @Effect() listStatistics$ = this.actions$.pipe(
    ofType<ListIncidentStatisticsAction>(ReportsActionTypes.LIST_INCIDENT_STATISTICS),
    switchMap(action => this.reportsService.listStatistics().pipe(
      map(result => new ListIncidentStatisticsCompleteAction(result)),
      catchError(err => this.errorService.handleError(action, ListIncidentStatisticsFailedAction, err, 5000)))),
  );

  @Effect() getStatistics$ = this.actions$.pipe(
    ofType<GetIncidentStatisticsAction>(ReportsActionTypes.GET_INCIDENT_STATISTICS),
    withLatestFrom(this.store.pipe(select(getAllIncidentStatistics))),
    switchMap(([action, allStats]) => {
      const currentDate = new Date();
      const toFetch: Date[] = action.payload.dates.map(d => new Date(d)).filter(d => d < currentDate);
      const availableStats = new Map<number, number[]>();
      for (const { year, month } of allStats) {
        const currentStats = availableStats.get(year) || [];
        availableStats.set(year, [...currentStats, month]);
      }
      const missingStats: string[] = [];
      for (const date of toFetch) {
        const months = availableStats.get(date.getFullYear());
        // January = 0 in js
        const month = date.getMonth() + 1;
        if (!months || !months.includes(month)) {
          missingStats.push(`${date.getFullYear()}-${date.getMonth() + 1}`);
        }
      }
      return this.reportsService.getStatistics(missingStats).pipe(
        map(result => new GetIncidentStatisticsCompleteAction(result)),
        catchError(err => this.errorService.handleError(action, GetIncidentStatisticsFailedAction, err, 5000)));
    }),
  );

  constructor(private actions$: Actions<ReportsActions>,
              private store: Store<ReportsState>,
              private reportsService: ReportsService,
              private snackbar: MatSnackBar,
              private translate: TranslateService,
              private errorService: ErrorService) {
  }
}
