import { Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { ErrorService } from '@oca/web-shared';
import { catchError, map, switchMap } from 'rxjs/operators';
import {
  createCommunity,
  createCommunityFailure,
  createCommunitySuccess,
  loadCommunity,
  loadCommunityFailure,
  loadCommunitySuccess,
  updateCommunity,
  updateCommunityFailure,
  updateCommunitySuccess,
} from './community.actions';
import { CommunityService } from './community.service';


@Injectable()
export class CommunitiesEffects {

  getCommunity$ = createEffect(() => this.actions$.pipe(
    ofType(loadCommunity),
    switchMap(action => this.communityService.getCommunity(action.id).pipe(
      map(result => loadCommunitySuccess({ community: result })),
      catchError(err => this.errorService.handleError(action, loadCommunityFailure, err)),
    ))));

  createCommunity$ = createEffect(() => this.actions$.pipe(
    ofType(createCommunity),
    switchMap(action => this.communityService.createCommunity(action.community).pipe(
      map(community => createCommunitySuccess({ community })),
      catchError(err => this.errorService.handleError(action, createCommunityFailure, err)),
    ))));

  updateCommunity$ = createEffect(() => this.actions$.pipe(
    ofType(updateCommunity),
    switchMap(action => this.communityService.updateCommunity(action.id, action.community).pipe(
      map(community => updateCommunitySuccess({ community })),
      catchError(err => this.errorService.handleError(action, updateCommunityFailure, err)),
    ))));

  constructor(private actions$: Actions,
              private errorService: ErrorService,
              private communityService: CommunityService) {
  }

}
