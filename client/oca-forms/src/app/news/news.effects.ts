import { Injectable } from '@angular/core';
import { Actions, Effect, ofType } from '@ngrx/effects';
import { of } from 'rxjs';
import { catchError, map, switchMap } from 'rxjs/operators';
import {
  CreateNewsItemAction,
  CreateNewsItemCompleteAction,
  CreateNewsItemFailedAction,
  DeleteNewsItemAction,
  DeleteNewsItemCompleteAction,
  DeleteNewsItemFailedAction,
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
  UpdateNewsItemAction,
  UpdateNewsItemCompleteAction,
  UpdateNewsItemFailedAction,
} from './news.actions';
import { NewsService } from './news.service';


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

  @Effect() deleteNewsItem$ = this.actions$.pipe(
    ofType<DeleteNewsItemAction>(NewsActionTypes.DELETE_NEWS_ITEM),
    switchMap(action => this.newsService.deleteNewsItem(action.payload.id).pipe(
      map(() => new DeleteNewsItemCompleteAction(action.payload)),
      catchError(err => of(new DeleteNewsItemFailedAction(err))))),
  );

  constructor(private actions$: Actions<NewsActions>,
              private newsService: NewsService) {
  }

}
