import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { ErrorService } from '@oca/web-shared';
import { catchError, map, switchMap, tap } from 'rxjs/operators';
import * as actions from './scripts.actions';
import { GetScriptsFailedAction, ScriptsActions, ScriptsActionTypes } from './scripts.actions';
import { ScriptsService } from './scripts.service';

@Injectable()
export class ScriptsEffects {

   getScripts$ = createEffect(() => this.actions$.pipe(
    ofType<actions.GetScriptsAction>(ScriptsActionTypes.GET_SCRIPTS),
    switchMap(action => this.scriptsService.getScripts().pipe(
      map(result => new actions.GetScriptsCompleteAction(result)),
      catchError(err => this.errorService.handleError(action, GetScriptsFailedAction, err)),
    ))));

   getScript$ = createEffect(() => this.actions$.pipe(
    ofType<actions.GetScriptAction>(ScriptsActionTypes.GET_SCRIPT),
    switchMap(action => this.scriptsService.getScript(action.payload).pipe(
      map(result => new actions.GetScriptCompleteAction(result)),
      catchError(err => this.errorService.handleError(action, actions.GetScriptFailedAction, err)),
    ))));

   createScript$ = createEffect(() => this.actions$.pipe(
    ofType<actions.CreateScriptAction>(ScriptsActionTypes.CREATE_SCRIPT),
    switchMap(action => this.scriptsService.createScript(action.payload).pipe(
      map(result => new actions.CreateScriptCompleteAction(result)),
      tap(result => this.router.navigate([`/admin/scripts/${result.payload.id}`])),
      catchError(err => this.errorService.handleError(action, actions.CreateScriptFailedAction, err)),
    ))));

   updateScript$ = createEffect(() => this.actions$.pipe(
    ofType<actions.UpdateScriptAction>(ScriptsActionTypes.UPDATE_SCRIPT),
    switchMap(action => this.scriptsService.updateScript(action.payload).pipe(
      map(result => new actions.UpdateScriptCompleteAction(result)),
      catchError(err => this.errorService.handleError(action, actions.UpdateScriptFailedAction, err)),
    ))));

   deleteScript$ = createEffect(() => this.actions$.pipe(
    ofType<actions.DeleteScriptAction>(ScriptsActionTypes.DELETE_SCRIPT),
    switchMap(action => this.scriptsService.deleteScript(action.payload).pipe(
      map(result => new actions.DeleteScriptCompleteAction(result)),
      tap(() => this.navigateToParentRoute()),
      catchError(err => this.errorService.handleError(action, actions.DeleteScriptFailedAction, err)),
    ))));

   runFunction$ = createEffect(() => this.actions$.pipe(
    ofType<actions.RunScriptAction>(ScriptsActionTypes.RUN_SCRIPT),
    switchMap(action => this.scriptsService.runFunction(action.payload).pipe(
      map(result => new actions.RunScriptCompleteAction(result)),
      catchError(err => this.errorService.handleError(action, actions.RunScriptFailedAction, err)),
    ))));

  constructor(private actions$: Actions<ScriptsActions>,
              private errorService: ErrorService,
              private router: Router,
              private scriptsService: ScriptsService) {
  }

  private navigateToParentRoute() {
    // https://github.com/angular/angular/issues/15004#issuecomment-412525030
    let route = this.router.routerState.root;
    while (route.firstChild) {
      route = route.firstChild;
    }
    this.router.navigate(['..'], { relativeTo: route });
  }
}
