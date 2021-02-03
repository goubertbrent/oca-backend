import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
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
  getHomeScreen,
  getHomeScreenFailure,
  getHomeScreenSuccess,
  loadCommunity,
  loadCommunityFailure,
  loadCommunitySuccess,
  publishHomeScreen,
  publishHomeScreenFailure,
  publishHomeScreenSuccess,
  testHomeScreen,
  testHomeScreenFailure,
  testHomeScreenSuccess,
  updateCommunity,
  updateCommunityFailure,
  updateCommunitySuccess,
  updateHomeScreen,
  updateHomeScreenFailure,
  updateHomeScreenSuccess,
  getGeoFence,
  getGeoFenceSuccess,
  updateGeoFence,
  updateGeoFenceSuccess,
  updateGeoFenceFailure,
  getGeoFenceFailure,
  getMapSettingsSuccess,
  updateMapSettings,
  getMapSettingsFailure,
  getMapSettings,
  updateMapSettingsSuccess,
  updateMapSettingsFailure,
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

  getHomeScreen$ = createEffect(() => this.actions$.pipe(
    ofType(getHomeScreen),
    switchMap(action => this.communityService.getHomeScreen(action.communityId, action.homeScreenId).pipe(
      map(homeScreen => getHomeScreenSuccess({ communityId: action.communityId, homeScreenId: action.homeScreenId, homeScreen })),
      catchError(err => this.errorService.handleError(action, getHomeScreenFailure, err)),
    ))));

  updateHomeScreen$ = createEffect(() => this.actions$.pipe(
    ofType(updateHomeScreen),
    switchMap(action => this.communityService.updateHomeScreen(action.communityId, action.homeScreenId, action.homeScreen).pipe(
      map(homeScreen => updateHomeScreenSuccess({ communityId: action.communityId, homeScreenId: action.homeScreenId, homeScreen })),
      tap(() => this.matSnackbar.open('Home screen updated', undefined, { duration: 1000 })),
      catchError(err => this.errorService.handleError(action, updateHomeScreenFailure, err)),
    ))));

  publishHomeScreen$ = createEffect(() => this.actions$.pipe(
    ofType(publishHomeScreen),
    switchMap(action => this.communityService.publishHomeScreen(action.communityId, action.homeScreenId).pipe(
      map(() => publishHomeScreenSuccess({ communityId: action.communityId, homeScreenId: action.homeScreenId})),
      tap(() => this.matSnackbar.open('Home screen published', undefined, { duration: 5000 })),
      catchError(err => this.errorService.handleError(action, publishHomeScreenFailure, err)),
    ))));

  testHomeScreen$ = createEffect(() => this.actions$.pipe(
    ofType(testHomeScreen),
    switchMap(action => this.communityService.testHomeScreen(action.communityId, action.homeScreenId, action.testUser).pipe(
      map(() => testHomeScreenSuccess()),
      tap(() => this.matSnackbar.open('Test home screen updated', undefined, { duration: 5000 })),
      catchError(err => this.errorService.handleError(action, testHomeScreenFailure, err)),
    ))));

  getGeoFence$ = createEffect(() => this.actions$.pipe(
    ofType(getGeoFence),
    switchMap(action => this.communityService.getGeoFence(action.communityId).pipe(
      map(data => getGeoFenceSuccess({data})),
      catchError(err => this.errorService.handleError(action, getGeoFenceFailure, err)),
    ))));

  updateGeoFence$ = createEffect(() => this.actions$.pipe(
    ofType(updateGeoFence),
    switchMap(action => this.communityService.updateGeoFence(action.communityId, action.data).pipe(
      map(data => updateGeoFenceSuccess({data})),
      tap(() => this.matSnackbar.open('Geofence updated', undefined, { duration: 5000 })),
      catchError(err => this.errorService.handleError(action, updateGeoFenceFailure, err)),
    ))));

  getMapSettings$ = createEffect(() => this.actions$.pipe(
    ofType(getMapSettings),
    switchMap(action => this.communityService.getMapSettings(action.communityId).pipe(
      map(data => getMapSettingsSuccess({data})),
      catchError(err => this.errorService.handleError(action, getMapSettingsFailure, err)),
    ))));

  updateMapSettings$ = createEffect(() => this.actions$.pipe(
    ofType(updateMapSettings),
    switchMap(action => this.communityService.updateMapSettings(action.communityId, action.data).pipe(
      map(data => updateMapSettingsSuccess({data})),
      tap(() => this.matSnackbar.open('Map settings updated', undefined, { duration: 5000 })),
      catchError(err => this.errorService.handleError(action, updateMapSettingsFailure, err)),
    ))));

  constructor(private actions$: Actions,
              private errorService: ErrorService,
              private matSnackbar: MatSnackBar,
              private router: Router,
              private communityService: CommunityService) {
  }

}
