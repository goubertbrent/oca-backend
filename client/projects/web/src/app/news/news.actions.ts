import { Action } from '@ngrx/store';
import { ErrorAction, NewsItem } from '@oca/web-shared';
import { NewsStatisticsActionType } from './news.service';

export enum NewsActionTypes {
  GetNewsItem = '[News] Get news item',
  GetNewsItemSuccess = '[News] Get news item Success',
  GetNewsItemFailure = '[News] Get news item Failure',
  SaveNewsItemStatistic = '[News] Save news item statistic',
}

export class GetNewsItem implements Action {
  readonly type = NewsActionTypes.GetNewsItem;

  constructor(public payload: { id: number; appUrlName: string; }) {
  }
}

export class GetNewsItemSuccess implements Action {
  readonly type = NewsActionTypes.GetNewsItemSuccess;

  constructor(public payload: { data: NewsItem }) {
  }
}

export class GetNewsItemFailure implements ErrorAction {
  readonly type = NewsActionTypes.GetNewsItemFailure;

  constructor(public error: string) {
  }
}

export class SaveNewsItemStatistic implements Action {
  readonly type = NewsActionTypes.SaveNewsItemStatistic;

  constructor(public payload: { id: number; appUrlName: string; action: NewsStatisticsActionType }) {
  }
}


export type NewsActions = GetNewsItem | GetNewsItemSuccess | GetNewsItemFailure | SaveNewsItemStatistic;

