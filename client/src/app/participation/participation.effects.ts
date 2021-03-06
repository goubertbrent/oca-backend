import { Injectable } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { of } from 'rxjs';
import { catchError, filter, first, map, switchMap, tap } from 'rxjs/operators';
import { transformErrorResponse } from '../shared/errors/errors';
import { filterNull } from '../shared/util';
import {
  CreateProjectAction,
  CreateProjectCompleteAction,
  CreateProjectFailedAction,
  GetMoreProjectStatisticsAction,
  GetProjectAction,
  GetProjectCompleteAction,
  GetProjectFailedAction,
  GetProjectsAction,
  GetProjectsCompleteAction,
  GetProjectsFailedAction,
  GetProjectStatisticsAction,
  GetProjectStatisticsCompleteAction,
  GetProjectStatisticsFailedAction,
  GetSettingsAction,
  GetSettingsCompleteAction,
  GetSettingsFailedAction,
  ParticipationActions,
  ParticipationActionTypes,
  SaveProjectAction,
  SaveProjectCompleteAction,
  SaveProjectFailedAction,
  UpdateSettingsAction,
  UpdateSettingsCompleteAction,
  UpdateSettingsFailedAction,
} from './participation.actions';
import { ParticipationService } from './participation.service';
import { getProjectStatistics, ParticipationState } from './participation.state';

@Injectable({ providedIn: 'root' })
export class ParticipationEffects {
   getProjects$ = createEffect(() => this.actions$.pipe(
    ofType<GetProjectsAction>(ParticipationActionTypes.GET_PROJECTS),
    switchMap(() => this.participationService.getProjects().pipe(
      map(projects => new GetProjectsCompleteAction(projects)),
      catchError(err => of(new GetProjectsFailedAction(transformErrorResponse(err)))))),
  ));

   getProject$ = createEffect(() => this.actions$.pipe(
    ofType<GetProjectAction>(ParticipationActionTypes.GET_PROJECT),
    switchMap(action => this.participationService.getProject(action.payload.id).pipe(
      map(project => new GetProjectCompleteAction(project)),
      catchError(err => of(new GetProjectFailedAction(transformErrorResponse(err)))))),
  ));

   getProjectStatistics$ = createEffect(() => this.actions$.pipe(
    ofType<GetProjectStatisticsAction>(ParticipationActionTypes.GET_PROJECT_STATISTICS),
    switchMap(action => this.participationService.getProjectStatistics(action.payload.id, null).pipe(
      map(data => new GetProjectStatisticsCompleteAction(data)),
      catchError(err => of(new GetProjectStatisticsFailedAction(transformErrorResponse(err)))))),
  ));

  // Automatically fetch merchant stats until we have everything
   afterGetStatisticsComplete$ = createEffect(() => this.actions$.pipe(
    ofType<GetProjectStatisticsCompleteAction>(ParticipationActionTypes.GET_PROJECT_STATISTICS_COMPLETE),
    filter(action => action.payload.more),
    map(() => new GetMoreProjectStatisticsAction()),
  ));

   getMoreProjectStatistics$ = createEffect(() => this.actions$.pipe(
    ofType<GetMoreProjectStatisticsAction>(ParticipationActionTypes.GET_MORE_PROJECT_STATISTICS),
    switchMap(() => this.store.pipe(select(getProjectStatistics), map(s => s.data), filterNull(), first())),
    switchMap(stats => this.participationService.getProjectStatistics(stats.project_id, stats.cursor).pipe(
      map(data => new GetProjectStatisticsCompleteAction(data)),
      catchError(err => of(new GetProjectStatisticsFailedAction(transformErrorResponse(err)))))),
  ));

   saveProject$ = createEffect(() => this.actions$.pipe(
    ofType<SaveProjectAction>(ParticipationActionTypes.SAVE_PROJECT),
    tap(() => this.snackbar.open(this.translate.instant('oca.saving_project'), undefined, { duration: 5000 })),
    switchMap(action => this.participationService.saveProject(action.payload.id, action.payload).pipe(
      tap(() => this.snackbar.open(this.translate.instant('oca.project_saved'), this.translate.instant('oca.ok'), { duration: 3000 })),
      map(data => new SaveProjectCompleteAction(data)),
      catchError(err => of(new SaveProjectFailedAction(transformErrorResponse(err)))))),
  ));

   createProject$ = createEffect(() => this.actions$.pipe(
    ofType<CreateProjectAction>(ParticipationActionTypes.CREATE_PROJECT),
    tap(() => this.snackbar.open(this.translate.instant('oca.creating_project'), undefined, { duration: 5000 })),
    switchMap(action => this.participationService.createProject(action.payload).pipe(
      tap(project => {
        this.snackbar.open(this.translate.instant('oca.project_saved'), this.translate.instant('oca.ok'), { duration: 3000 });
        this.router.navigate([ 'participation', 'projects', project.id ]);
      }),
      map(data => new CreateProjectCompleteAction(data)),
      catchError(err => of(new CreateProjectFailedAction(transformErrorResponse(err)))))),
  ));

   getSettings$ = createEffect(() => this.actions$.pipe(
    ofType<GetSettingsAction>(ParticipationActionTypes.GET_SETTINGS),
    switchMap(() => this.participationService.getSettings().pipe(
      map(data => new GetSettingsCompleteAction(data)),
      catchError(err => of(new GetSettingsFailedAction(transformErrorResponse(err)))))),
  ));

   updateSettings$ = createEffect(() => this.actions$.pipe(
    ofType<UpdateSettingsAction>(ParticipationActionTypes.UPDATE_SETTINGS),
    switchMap(action => this.participationService.saveSettings(action.payload).pipe(
      map(data => new UpdateSettingsCompleteAction(data)),
      catchError(err => of(new UpdateSettingsFailedAction(transformErrorResponse(err)))))),
  ));

  constructor(private actions$: Actions<ParticipationActions>,
              private store: Store<ParticipationState>,
              private participationService: ParticipationService,
              private snackbar: MatSnackBar,
              private translate: TranslateService,
              private router: Router) {
  }
}
