import { Injectable } from '@angular/core';
import { createEffect, ofType } from '@ngrx/effects';
import { delay, map } from 'rxjs/operators';
import { GetUserInformationResult } from '../hoplr';
import {
  GetFeedAction,
  GetFeedSuccessAction,
  GetUserInformationAction,
  GetUserInformationSuccessAction,
  HoplrActionTypes,
  LoginAction,
  LoginSuccessAction,
  LogoutSuccessAction,
  LookupNeighbourhoodAction,
  LookupNeighbourhoodSuccessAction,
  RegisterAction,
  RegisterSuccessAction,
} from '../hoplr.actions';
import { HoplrEffects } from '../hoplr.effects';
import { HOPLR_FEED } from './feed-data';

function randint(min: number, max: number): number {
  return Math.round(Math.random() * (max - min)) + min;
}
const MEDIA_BASE_URL = 'https://devhoplrstorage.blob.core.windows.net';

const USER_INFO: GetUserInformationResult = {
  registered: true,
  info: {
    neighbourhood: { Id: 320, Title: 'Roeselare Centrum', NeighbourhoodType: 0 },
    user: { Id: 1234, FirstName: 'Lucas', LastName: 'Vanhalst', ProfileName: 'Lucas Vanhalst' },
  },
};

@Injectable()
export class HoplrTestEffects extends HoplrEffects {

  lookupNeighbourhood$ = createEffect(() => this.actions$.pipe(
    ofType<LookupNeighbourhoodAction>(HoplrActionTypes.LOOKUP_NEIGHBOURHOOD),
    delay(randint(100, 400)),
    map(() => new LookupNeighbourhoodSuccessAction({
      location: {
        lat: 50.948371,
        lon: 3.126013,
        fullAddress: 'Hendrik Consciencestraat 23/6, 8800 Roeselare',
      },
      result: {
        success: true,
        neighbourhood: {
          Id: 320,
          Title: 'Roeselare Centrum',
          PolygonEncoded: 'ugx~Hufg_@rPfn@pOnNj`@yd@_YsjA',
          NeighbourhoodType: 0,
          Place: {
            Id: 99999,
            Name: 'Roeselare',
            CityId: 1252,
            CityName: 'Roeselare',
            RegionId: 23,
            RegionName: 'West-Vlaanderen',
            CountryId: 3,
            CountryName: 'België',
          },
        },
      },
    })),
  ));

  getUserInfo$ = createEffect(() => this.actions$.pipe(
    ofType<GetUserInformationAction>(HoplrActionTypes.GET_USER_INFORMATION),
    delay(randint(100, 400)),
    map(() => new GetUserInformationSuccessAction(USER_INFO)),
  ));

  register$ = createEffect(() => this.actions$.pipe(
    ofType<RegisterAction>(HoplrActionTypes.REGISTER),
    delay(randint(100, 400)),
    map(action => new RegisterSuccessAction(USER_INFO)),
  ));

  login$ = createEffect(() => this.actions$.pipe(
    ofType<LoginAction>(HoplrActionTypes.LOGIN),
    delay(randint(100, 400)),
    map(action => new LoginSuccessAction(USER_INFO)),
  ));

  logout$ = createEffect(() => this.actions$.pipe(
    ofType<LogoutSuccessAction>(HoplrActionTypes.LOGOUT),
    delay(randint(100, 400)),
    map(action => new LogoutSuccessAction()),
  ));

  getFeed$ = createEffect(() => this.actions$.pipe(
    ofType<GetFeedAction>(HoplrActionTypes.GET_FEED),
    delay(randint(100, 400)),
    map(action => {
      const page = action.payload.page ?? 1;
      const perPage = 10;
      const start = (page - 1) * perPage;
      const end = page * perPage;
      const results = this.hoplrService.convertItems(MEDIA_BASE_URL, HOPLR_FEED.slice(start, end));
      return new GetFeedSuccessAction({
        page,
        more: results.length > 0,
        baseUrl: 'https://stagingwebwww.hoplr.com',
        mediaBaseUrl: MEDIA_BASE_URL,
        results,
      });
    }),
  ));
}
