import { HttpErrorResponse } from '@angular/common/http';
import { Action } from '@ngrx/store';
import { CreateNews, NewsBroadcastItem, NewsBroadcastItemList, NewsOptions, NewsStats } from './interfaces';

export enum NewsActionTypes {
  GET_NEWS_OPTIONS = '[news] Get news options',
  GET_NEWS_OPTIONS_COMPLETE = '[news] Get news options complete',
  GET_NEWS_OPTIONS_FAILED = '[news] Get news options failed',
  GET_NEWS_LIST = '[news] Get news list',
  GET_NEWS_LIST_COMPLETE = '[news] Get news list complete',
  GET_NEWS_LIST_FAILED = '[news] Get news list failed',
  GET_NEWS_ITEM = '[news] Get news item',
  GET_NEWS_ITEM_COMPLETE = '[news] Get news item complete',
  GET_NEWS_ITEM_FAILED = '[news] Get news item failed',
  CREATE_NEWS_ITEM = '[news] Create news item',
  CREATE_NEWS_ITEM_COMPLETE = '[news] Create news item complete',
  CREATE_NEWS_ITEM_FAILED = '[news] Create news item failed',
  UPDATE_NEWS_ITEM = '[news] Update news item',
  UPDATE_NEWS_ITEM_COMPLETE = '[news] Update news item complete',
  UPDATE_NEWS_ITEM_FAILED = '[news] Update news item failed',
  DELETE_NEWS_ITEM = '[news] Delete news item',
  DELETE_NEWS_ITEM_COMPLETE = '[news] Delete news item complete',
  DELETE_NEWS_ITEM_FAILED = '[news] Delete news item failed',
}

export class GetNewsOptionsAction implements Action {
  readonly type = NewsActionTypes.GET_NEWS_OPTIONS;
}

export class GetNewsOptionsCompleteAction implements Action {
  readonly type = NewsActionTypes.GET_NEWS_OPTIONS_COMPLETE;

  constructor(public payload: NewsOptions) {
  }
}

export class GetNewsOptionsFailedAction implements Action {
  readonly type = NewsActionTypes.GET_NEWS_OPTIONS_FAILED;

  constructor(public payload: HttpErrorResponse) {
  }
}


export class GetNewsListAction implements Action {
  readonly type = NewsActionTypes.GET_NEWS_LIST;

  constructor(public payload: { cursor: string | null }) {
  }
}

export class GetNewsListCompleteAction implements Action {
  readonly type = NewsActionTypes.GET_NEWS_LIST_COMPLETE;

  constructor(public payload: NewsBroadcastItemList) {
  }

}

export class GetNewsListFailedAction implements Action {
  readonly type = NewsActionTypes.GET_NEWS_LIST_FAILED;

  constructor(public payload: HttpErrorResponse) {
  }
}

export class GetNewsItemAction implements Action {
  readonly type = NewsActionTypes.GET_NEWS_ITEM;

  constructor(public payload: { id: number }) {
  }
}

export class GetNewsItemCompleteAction implements Action {
  readonly type = NewsActionTypes.GET_NEWS_ITEM_COMPLETE;

  constructor(public payload: NewsStats) {
  }

}

export class GetNewsItemFailedAction implements Action {
  readonly type = NewsActionTypes.GET_NEWS_ITEM_FAILED;

  constructor(public payload: HttpErrorResponse) {
  }
}

export class CreateNewsItemAction implements Action {
  readonly type = NewsActionTypes.CREATE_NEWS_ITEM;

  constructor(public payload: CreateNews) {
  }
}

export class CreateNewsItemCompleteAction implements Action {
  readonly type = NewsActionTypes.CREATE_NEWS_ITEM_COMPLETE;

  constructor(public payload: NewsBroadcastItem) {
  }

}

export class CreateNewsItemFailedAction implements Action {
  readonly type = NewsActionTypes.CREATE_NEWS_ITEM_FAILED;

  constructor(public payload: HttpErrorResponse) {
  }
}


export class UpdateNewsItemAction implements Action {
  readonly type = NewsActionTypes.UPDATE_NEWS_ITEM;

  constructor(public payload: { id: number, item: CreateNews }) {
  }
}

export class UpdateNewsItemCompleteAction implements Action {
  readonly type = NewsActionTypes.UPDATE_NEWS_ITEM_COMPLETE;

  constructor(public payload: NewsBroadcastItem) {
  }

}

export class UpdateNewsItemFailedAction implements Action {
  readonly type = NewsActionTypes.UPDATE_NEWS_ITEM_FAILED;

  constructor(public payload: HttpErrorResponse) {
  }
}


export class DeleteNewsItemAction implements Action {
  readonly type = NewsActionTypes.DELETE_NEWS_ITEM;

  constructor(public payload: { id: number }) {
  }
}

export class DeleteNewsItemCompleteAction implements Action {
  readonly type = NewsActionTypes.DELETE_NEWS_ITEM_COMPLETE;

  constructor(public payload: { id: number }) {
  }

}

export class DeleteNewsItemFailedAction implements Action {
  readonly type = NewsActionTypes.DELETE_NEWS_ITEM_FAILED;

  constructor(public payload: HttpErrorResponse) {
  }
}


export type NewsActions = GetNewsOptionsAction
  | GetNewsOptionsCompleteAction
  | GetNewsOptionsFailedAction
  | GetNewsListAction
  | GetNewsListCompleteAction
  | GetNewsListFailedAction
  | GetNewsItemAction
  | GetNewsItemCompleteAction
  | GetNewsItemFailedAction
  | CreateNewsItemAction
  | CreateNewsItemCompleteAction
  | CreateNewsItemFailedAction
  | UpdateNewsItemAction
  | UpdateNewsItemCompleteAction
  | UpdateNewsItemFailedAction
  | DeleteNewsItemAction
  | DeleteNewsItemCompleteAction
  | DeleteNewsItemFailedAction;
