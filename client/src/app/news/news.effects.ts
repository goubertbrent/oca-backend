import { DatePipe } from '@angular/common';
import { Injectable } from '@angular/core';
import { MatDialog, MatDialogConfig } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { of } from 'rxjs';
import { catchError, first, map, startWith, switchMap, tap } from 'rxjs/operators';
import { SimpleDialogComponent, SimpleDialogData } from '../shared/dialog/simple-dialog.component';
import { ErrorService } from '../shared/errors/error.service';
import { transformErrorResponse } from '../shared/errors/errors';
import {
  CopyNewsItemAction,
  CreateNewsItemAction,
  CreateNewsItemCompleteAction,
  CreateNewsItemFailedAction,
  DeleteNewsItemAction,
  DeleteNewsItemCancelledAction,
  DeleteNewsItemCompleteAction,
  DeleteNewsItemFailedAction,
  GetLocationsAction,
  GetLocationsCompleteAction,
  GetLocationsFailedAction,
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
import { getLocations, NewsState } from './news.state';


@Injectable()
export class NewsEffects {
   getNewsOptions$ = createEffect(() => this.actions$.pipe(
    ofType<GetNewsOptionsAction>(NewsActionTypes.GET_NEWS_OPTIONS),
    switchMap(() => this.newsService.getNewsOptions().pipe(
      map(data => new GetNewsOptionsCompleteAction(data)),
      catchError(err => of(new GetNewsOptionsFailedAction(transformErrorResponse(err)))))),
  ));
   getNewsItems$ = createEffect(() => this.actions$.pipe(
    ofType<GetNewsListAction>(NewsActionTypes.GET_NEWS_LIST),
    switchMap(action => this.newsService.getNewsList(action.payload.cursor).pipe(
      map(data => new GetNewsListCompleteAction(data)),
      catchError(err => of(new GetNewsListFailedAction(transformErrorResponse(err)))))),
  ));

   getNewsItem$ = createEffect(() => this.actions$.pipe(
    ofType<GetNewsItemAction>(NewsActionTypes.GET_NEWS_ITEM),
    switchMap(action => this.newsService.getNewsItem(action.payload.id).pipe(
      map(data => new GetNewsItemCompleteAction(data)),
      catchError(err => of(new GetNewsItemFailedAction(transformErrorResponse(err)))))),
  ));

   createNewsItem$ = createEffect(() => this.actions$.pipe(
    ofType<CreateNewsItemAction>(NewsActionTypes.CREATE_NEWS_ITEM),
    switchMap(action => this.newsService.createNewsItem(action.payload).pipe(
      map(data => new CreateNewsItemCompleteAction(data)),
      tap(data => {
        if (data.payload) {
          this.router.navigate([ 'news', 'list']);
          if (data.payload.published) {
            this.snackBar.open(this.translate.instant('oca.news_item_published'), this.translate.instant('oca.ok'), { duration: 5000 });
          } else {
            const datetime = this.datePipe.transform(new Date(data.payload.scheduled_at * 1000), 'medium');
            this.snackBar.open(this.translate.instant('oca.news_item_scheduled_for_datetime', {datetime}),
              this.translate.instant('oca.ok'), { duration: 5000 });
          }
        } else {
          const config: MatDialogConfig<SimpleDialogData> = {
            data: {
              title: '',
              message: this.translate.instant('oca.news_review_all_sent_to_review'),
              ok: this.translate.instant('oca.ok'),
            },
          };
          this.matDialog.open(SimpleDialogComponent, config).afterClosed().subscribe(() => this.router.navigate([ 'news' , 'list']));
        }
      }),
      catchError(err => of(new CreateNewsItemFailedAction(transformErrorResponse(err)))))),
  ));

   afterFailed$ = createEffect(() => this.actions$.pipe(
    ofType<CreateNewsItemFailedAction | UpdateNewsItemFailedAction>(NewsActionTypes.CREATE_NEWS_ITEM_FAILED,
      NewsActionTypes.UPDATE_NEWS_ITEM_FAILED),
    tap(action => {
      this.matDialog.open(SimpleDialogComponent, {
        data: {
          ok: this.translate.instant('oca.ok'),
          message: this.errorService.getErrorMessage(action.error),
          title: this.translate.instant('oca.Error'),
        } as SimpleDialogData,
      });
    }),
  ), { dispatch: false });

   updateNewsItem$ = createEffect(() => this.actions$.pipe(
    ofType<UpdateNewsItemAction>(NewsActionTypes.UPDATE_NEWS_ITEM),
    switchMap(action => this.newsService.updateNewsItem(action.payload.id, action.payload.item).pipe(
      map(data => new UpdateNewsItemCompleteAction(data)),
      tap(() => this.snackBar.open(this.translate.instant('oca.news_item_saved'), this.translate.instant('oca.ok'), { duration: 5000 })),
      catchError(err => of(new UpdateNewsItemFailedAction(transformErrorResponse(err)))))),
  ));

   deleteNewsItem$ = createEffect(() => this.actions$.pipe(
    ofType<DeleteNewsItemAction>(NewsActionTypes.DELETE_NEWS_ITEM),
    switchMap(action => this.matDialog.open(SimpleDialogComponent, {
      data: {
        ok: this.translate.instant('oca.Yes'),
        message: this.translate.instant('oca.confirm_delete_news', { news_title: action.payload.title || action.payload.qr_code_caption }),
        title: this.translate.instant('oca.confirm_deletion'),
        cancel: this.translate.instant('oca.No'),
      },
    } as MatDialogConfig<SimpleDialogData>).afterClosed().pipe(
      switchMap(result => {
        if (result.submitted) {
          return this.newsService.deleteNewsItem(action.payload.id).pipe(
            map(() => new DeleteNewsItemCompleteAction(action.payload)),
            catchError(err => of(new DeleteNewsItemFailedAction(transformErrorResponse(err)))));
        } else {
          return of(new DeleteNewsItemCancelledAction());
        }
      }),
    ))));

   copyNewsItem$ = createEffect(() => this.actions$.pipe(
    ofType<CopyNewsItemAction>(NewsActionTypes.COPY_NEWS_ITEM),
    tap(action => {
      const copy = this.newsService.copyNewsItem(action.payload);
      localStorage.setItem('news.item', JSON.stringify(copy));
      this.router.navigate(['news', 'create']);
    })), { dispatch: false });


   getLocations$ = createEffect(() => this.actions$.pipe(
    ofType<GetLocationsAction>(NewsActionTypes.GET_LOCATIONS),
    switchMap(action => this.store.pipe(
      select(getLocations),
      first(),
      map(locations => ({ action, locations }))),
    ),
    switchMap(({ action, locations }) => {
      if (locations.data && action.payload.appId === locations.data.app_id) {
        return of(new GetLocationsCompleteAction(locations.data));
      }
      return this.newsService.getLocations(action.payload.appId).pipe(
        map(data => new GetLocationsCompleteAction(data)),
        catchError(err => of(new GetLocationsFailedAction(transformErrorResponse(err)))));
    }),
  ));

  constructor(private actions$: Actions<NewsActions>,
              private router: Router,
              private matDialog: MatDialog,
              private snackBar: MatSnackBar,
              private translate: TranslateService,
              private errorService: ErrorService,
              private store: Store<NewsState>,
              private newsService: NewsService,
              private datePipe: DatePipe) {
  }

}
