import { onLoadableError, onLoadableLoad, onLoadableSuccess } from '../shared/loadable/loadable';
import { NewsActions, NewsActionTypes } from './news.actions';
import { appsAdapter, initialNewsState, newsAdapter, NewsState } from './news.state';

export function newsReducer(state: NewsState = initialNewsState, action: NewsActions): NewsState {
  switch (action.type) {
    case NewsActionTypes.GET_NEWS_OPTIONS:
      return { ...state, newsOptions: onLoadableLoad(state.newsOptions.data) };
    case NewsActionTypes.GET_NEWS_OPTIONS_COMPLETE:
      return { ...state, newsOptions: onLoadableSuccess(action.payload) };
    case NewsActionTypes.GET_NEWS_OPTIONS_FAILED:
      return { ...state, newsOptions: onLoadableError(action.payload) };
    case NewsActionTypes.GET_NEWS_LIST:
      return { ...state, listStatus: onLoadableLoad(state.listStatus.data) };
    case NewsActionTypes.GET_NEWS_LIST_COMPLETE:
      return {
        ...state,
        listStatus: onLoadableSuccess(action.payload),
        items: newsAdapter.addMany(action.payload.results, {
          ...state.items,
          cursor: action.payload.cursor,
          more: action.payload.more,
        }),
      };
    case NewsActionTypes.GET_NEWS_LIST_FAILED:
      return { ...state, listStatus: onLoadableError(action.payload) };
    case NewsActionTypes.GET_NEWS_ITEM:
      return { ...state, itemStats: onLoadableLoad(initialNewsState.itemStats.data) };
    case NewsActionTypes.GET_NEWS_ITEM_COMPLETE:
      return {
        ...state,
        itemStats: onLoadableSuccess(action.payload),
        items: newsAdapter.updateOne({ id: action.payload.news_item.id, changes: action.payload.news_item }, state.items),
        apps: appsAdapter.upsertMany(action.payload.apps, state.apps),
      };
    case NewsActionTypes.GET_NEWS_ITEM_FAILED:
      return { ...state, itemStats: onLoadableError(action.payload) };
    case NewsActionTypes.CREATE_NEWS_ITEM:
      return { ...state, status: onLoadableLoad(null) };
    case NewsActionTypes.CREATE_NEWS_ITEM_COMPLETE:
      return {
        ...state,
        items: newsAdapter.addOne(action.payload, state.items),
        status: onLoadableSuccess(action.payload),
      };
    case NewsActionTypes.CREATE_NEWS_ITEM_FAILED:
      return { ...state, status: onLoadableError(action.payload) };
    case NewsActionTypes.UPDATE_NEWS_ITEM:
      return { ...state, status: onLoadableLoad(null) };
    case NewsActionTypes.UPDATE_NEWS_ITEM_COMPLETE:
      return {
        ...state,
        items: newsAdapter.updateOne({ id: action.payload.id, changes: action.payload }, state.items),
        status: onLoadableSuccess(action.payload),
      };
    case NewsActionTypes.UPDATE_NEWS_ITEM_FAILED:
      return { ...state, status: onLoadableError(action.payload) };
    case NewsActionTypes.DELETE_NEWS_ITEM:
      return { ...state, status: onLoadableLoad(null) };
    case NewsActionTypes.DELETE_NEWS_ITEM_COMPLETE:
      return {
        ...state,
        status: onLoadableSuccess(null),
        items: newsAdapter.removeOne(action.payload.id, state.items),
      };
    case NewsActionTypes.DELETE_NEWS_ITEM_FAILED:
      return { ...state, status: onLoadableError(action.payload) };
  }
  return state;
}
