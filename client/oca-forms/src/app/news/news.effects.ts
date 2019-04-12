import { Injectable } from '@angular/core';
import { Actions, Effect, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { of } from 'rxjs';
import { catchError, filter, map, switchMap, withLatestFrom } from 'rxjs/operators';
import { NonNullLoadable } from '../shared/loadable/loadable';
import { ServiceIdentityInfo } from '../shared/rogerthat';
import { getInfo } from '../shared/shared.state';
import { NewsOptions } from './interfaces';
import {
  CreateNewsItemAction,
  CreateNewsItemCompleteAction,
  CreateNewsItemFailedAction,
  DeleteNewsItemAction,
  DeleteNewsItemCompleteAction,
  DeleteNewsItemFailedAction,
  GetNewsCityAppsAction,
  GetNewsCityAppsCompleteAction,
  GetNewsCityAppsFailedAction,
  GetNewsItemAction,
  GetNewsItemCompleteAction,
  GetNewsItemFailedAction,
  GetNewsListAction,
  GetNewsListCompleteAction,
  GetNewsListFailedAction,
  GetNewsOptionsAction,
  GetNewsOptionsCompleteAction,
  GetNewsOptionsFailedAction,
  NewsActions,
  NewsActionTypes,
  SetNewNewsItemAction,
  SetNewNewsItemCompleteAction,
  UpdateNewsItemAction,
  UpdateNewsItemCompleteAction,
  UpdateNewsItemFailedAction,
} from './news.actions';
import { NewsService } from './news.service';
import { getNewsOptions, NewsState } from './news.state';


@Injectable()
export class NewsEffects {
  @Effect() getNewsOptions$ = this.actions$.pipe(
    ofType<GetNewsOptionsAction>(NewsActionTypes.GET_NEWS_OPTIONS),
    switchMap(() => this.newsService.getNewsOptions().pipe(
      map(data => new GetNewsOptionsCompleteAction(data)),
      catchError(err => of(new GetNewsOptionsFailedAction(err))))),
  );
  @Effect() getNewsItems$ = this.actions$.pipe(
    ofType<GetNewsListAction>(NewsActionTypes.GET_NEWS_LIST),
    switchMap(action => this.newsService.getNewsList(action.payload.cursor).pipe(
      map(data => new GetNewsListCompleteAction(data)),
      catchError(err => of(new GetNewsListFailedAction(err))))),
  );

  @Effect() getNewsItem$ = this.actions$.pipe(
    ofType<GetNewsItemAction>(NewsActionTypes.GET_NEWS_ITEM),
    switchMap(action => this.newsService.getNewsItem(action.payload.id).pipe(
      map(data => new GetNewsItemCompleteAction(data)),
      catchError(err => of(new GetNewsItemFailedAction(err))))),
  );

  // TODO doens't work when going from overview to create page
  @Effect() setNewsNewsItem$ = this.actions$.pipe(
    ofType<SetNewNewsItemAction>(NewsActionTypes.SET_NEW_NEWS_ITEM),
    switchMap(() => this.store$.pipe(select(getNewsOptions), filter(loadable => loadable.success))),
    withLatestFrom(this.store$.pipe(select(getInfo), filter(loadable => loadable.success))),
    switchMap(([ newsOptions, info ]: [ NonNullLoadable<NewsOptions>, NonNullLoadable<ServiceIdentityInfo> ]) => {
      return this.newsService.getNewNewsItem(newsOptions.data.broadcast_types, info.data.default_app).pipe(
        map(data => new SetNewNewsItemCompleteAction(data)));
    }),
  );

  @Effect() createNewsItem$ = this.actions$.pipe(
    ofType<CreateNewsItemAction>(NewsActionTypes.CREATE_NEWS_ITEM),
    switchMap(action => this.newsService.createNewsItem(action.payload).pipe(
      map(data => new CreateNewsItemCompleteAction(data)),
      catchError(err => of(new CreateNewsItemFailedAction(err))))),
  );

  @Effect() updateNewsItem$ = this.actions$.pipe(
    ofType<UpdateNewsItemAction>(NewsActionTypes.UPDATE_NEWS_ITEM),
    switchMap(action => this.newsService.updateNewsItem(action.payload.id, action.payload.item).pipe(
      map(data => new UpdateNewsItemCompleteAction(data)),
      catchError(err => of(new UpdateNewsItemFailedAction(err))))),
  );

  // TODO: confirmation dialog
  @Effect() deleteNewsItem$ = this.actions$.pipe(
    ofType<DeleteNewsItemAction>(NewsActionTypes.DELETE_NEWS_ITEM),
    switchMap(action => this.newsService.deleteNewsItem(action.payload.id).pipe(
      map(() => new DeleteNewsItemCompleteAction(action.payload)),
      catchError(err => of(new DeleteNewsItemFailedAction(err))))),
  );

  @Effect() getNewsCityApps$ = this.actions$.pipe(
    ofType<GetNewsCityAppsAction>(NewsActionTypes.GET_NEWS_CITY_APPS),
    switchMap(() => this.newsService.getApps().pipe(
      map(result => new GetNewsCityAppsCompleteAction(result)),
      catchError(err => of(new GetNewsCityAppsFailedAction(err))))),
  );

  constructor(private actions$: Actions<NewsActions>,
              private store$: Store<NewsState>,
              private newsService: NewsService) {
  }

}
