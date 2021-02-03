import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { ErrorService } from '@oca/web-shared';
import { catchError, map, switchMap, tap } from 'rxjs/operators';
import * as PoiActions from './point-of-interest.actions';
import { PointOfInterestService } from './point-of-interest.service';


@Injectable()
export class PointOfInterestEffects {

  listPointOfInterests$ = createEffect(() => {
    return this.actions$.pipe(
      ofType(PoiActions.loadPointOfInterests),
      switchMap(action => this.poiService.listPointOfInterest(action.cursor, action.query, action.status).pipe(
        map(data => PoiActions.loadPointOfInterestsSuccess({ data })),
        catchError(error => this.errorService.handleError(action, PoiActions.loadPointOfInterestsFailure, error, {format: 'dialog'}))),
      ),
    );
  });

  getPointOfInterests$ = createEffect(() => {
    return this.actions$.pipe(
      ofType(PoiActions.getPointOfInterest),
      switchMap(action => this.poiService.getPointOfInterest(action.id).pipe(
        map(poi => PoiActions.getPointOfInterestSuccess({ poi })),
        catchError(error => this.errorService.handleError(action, PoiActions.getPointOfInterestFailure, error, {format: 'dialog'}))),
      ),
    );
  });

  createPointOfInterest$ = createEffect(() => {
    return this.actions$.pipe(
      ofType(PoiActions.createPointOfInterest),
      switchMap(action => this.poiService.createPointOfInterest(action.data).pipe(
        map(poi => PoiActions.createPointOfInterestSuccess({ poi })),
        catchError(error => this.errorService.handleError(action, PoiActions.createPointOfInterestFailure, error, {format: 'dialog'}))),
      ),
    );
  });

  updatePointOfInterests$ = createEffect(() => {
    return this.actions$.pipe(
      ofType(PoiActions.updatePointOfInterest),
      switchMap(action => this.poiService.updatePointOfInterest(action.id, action.data).pipe(
        map(poi => PoiActions.updatePointOfInterestSuccess({ poi })),
        catchError(error => this.errorService.handleError(action, PoiActions.updatePointOfInterestFailure, error, {format: 'dialog'}))),
      ),
    );
  });

  deletePointOfInterests$ = createEffect(() => {
    return this.actions$.pipe(
      ofType(PoiActions.deletePointOfInterest),
      switchMap(action => this.poiService.deletePointOfInterest(action.id).pipe(
        map(() => PoiActions.deletePointOfInterestSuccess({ id: action.id })),
        tap(() => this.router.navigateByUrl('/point-of-interest')),
        catchError(error => this.errorService.handleError(action, PoiActions.deletePointOfInterestFailure, error, { format: 'dialog' }))),
      ),
    );
  });

  constructor(private actions$: Actions,
              private errorService: ErrorService,
              private router: Router,
              private poiService: PointOfInterestService) {
  }

}
