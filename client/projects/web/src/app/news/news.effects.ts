import { Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { ErrorService } from '@oca/web-shared';
import { catchError, debounceTime, map, switchMap } from 'rxjs/operators';
import { GetNewsItem, GetNewsItemFailure, GetNewsItemSuccess, NewsActionTypes, SaveNewsItemStatistic } from './news.actions';
import { NewsService } from './news.service';


@Injectable()
export class NewsEffects {

  getNewsItem$ = createEffect(() => this.actions$.pipe(
    ofType<GetNewsItem>(NewsActionTypes.GetNewsItem),
    switchMap(action => this.service.getNewsItem(action.payload.appUrlName, action.payload.id).pipe(
      map(data => new GetNewsItemSuccess({ data })),
      catchError(err => this.errorService.handleError(action, GetNewsItemFailure, err)),
    )),
  ));

  saveStats$ = createEffect(() => this.actions$.pipe(
    ofType<SaveNewsItemStatistic>(NewsActionTypes.SaveNewsItemStatistic),
    debounceTime(500),
    switchMap(action => this.service.saveNewsStatistic(action.payload.appUrlName, action.payload.id, action.payload.action)),
  ), {dispatch: false});

  constructor(private actions$: Actions,
              private errorService: ErrorService,
              private service: NewsService) {
  }

}
