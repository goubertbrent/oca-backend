import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { ErrorService } from '@oca/web-shared';
import { catchError, map, switchMap, tap } from 'rxjs/operators';
import {
  createCommunity,
  createCommunityFailure,
  createCommunitySuccess,
  deleteCommunity,
  deleteCommunityFailure,
  deleteCommunitySuccess,
  loadCommunities,
  loadCommunitiesFailure,
  loadCommunitiesSuccess,
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

  getCommunities$ = createEffect(() => this.actions$.pipe(
    ofType(loadCommunities),
    switchMap(action => this.communityService.getCommunities(action.country).pipe(
      map(result => loadCommunitiesSuccess({ communities: result })),
      catchError(err => this.errorService.handleError(action, loadCommunitiesFailure, err)),
    ))));

  getCommunity$ = createEffect(() => this.actions$.pipe(
    ofType(loadCommunity),
    switchMap(action => this.communityService.getCommunity(action.id).pipe(
      map(result => loadCommunitySuccess({ community: result })),
      catchError(err => this.errorService.handleError(action, loadCommunityFailure, err)),
    ))));

  createCommunity$ = createEffect(() => this.actions$.pipe(
    ofType(createCommunity),
    switchMap(action => this.communityService.createCommunity(action.community).pipe(
      tap(community => this.router.navigateByUrl(`/communities/${community.id}`)),
      map(community => createCommunitySuccess({ community })),
      catchError(err => this.errorService.handleError(action, createCommunityFailure, err)),
    ))));

  updateCommunity$ = createEffect(() => this.actions$.pipe(
    ofType(updateCommunity),
    switchMap(action => this.communityService.updateCommunity(action.id, action.community).pipe(
      map(community => updateCommunitySuccess({ community })),
      catchError(err => this.errorService.handleError(action, updateCommunityFailure, err)),
    ))));

  deleteCommunity$ = createEffect(() => this.actions$.pipe(
    ofType(deleteCommunity),
    switchMap(action => this.communityService.deleteCommunity(action.id).pipe(
      map(community => deleteCommunitySuccess({ id: action.id })),
      catchError(err => this.errorService.handleError(action, deleteCommunityFailure, err)),
    ))));

  constructor(private actions$: Actions,
              private errorService: ErrorService,
              private router: Router,
              private communityService: CommunityService) {
  }

}
