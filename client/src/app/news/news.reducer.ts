import { onLoadableError, onLoadableLoad, onLoadableSuccess } from '../shared/loadable/loadable';
import { CreateNews, NewsItem } from './interfaces';
import { NewsActions, NewsActionTypes } from './news.actions';
import { appsAdapter, initialNewsState, newsAdapter, NewsState } from './news.state';

export function newsReducer(state: NewsState = initialNewsState, action: NewsActions): NewsState {
  switch (action.type) {
    case NewsActionTypes.GET_NEWS_OPTIONS:
      return { ...state, newsOptions: onLoadableLoad(state.newsOptions.data) };
    case NewsActionTypes.GET_NEWS_OPTIONS_COMPLETE:
      return { ...state, newsOptions: onLoadableSuccess(action.payload) };
    case NewsActionTypes.GET_NEWS_OPTIONS_FAILED:
      return { ...state, newsOptions: onLoadableError(action.error, state.newsOptions.data) };
    case NewsActionTypes.GET_NEWS_LIST:
      return { ...state, listStatus: onLoadableLoad(state.listStatus.data) };
    case NewsActionTypes.GET_NEWS_LIST_COMPLETE:
      return {
        ...state,
        listStatus: onLoadableSuccess(action.payload),
        items: newsAdapter.addMany(action.payload.result, {
          ...state.items,
          cursor: action.payload.cursor,
          more: action.payload.more,
        }),
      };
    case NewsActionTypes.GET_NEWS_LIST_FAILED:
      return { ...state, listStatus: onLoadableError(action.error, state.listStatus.data) };
    case NewsActionTypes.GET_NEWS_ITEM:
      return {
        ...state,
        itemStats: onLoadableLoad(initialNewsState.itemStats.data),
        editingNewsItem: onLoadableLoad(initialNewsState.editingNewsItem.data),
      };
    case NewsActionTypes.GET_NEWS_ITEM_COMPLETE:
      return {
        ...state,
        itemStats: onLoadableSuccess(action.payload),
        items: newsAdapter.updateOne({ id: action.payload.news_item.id, changes: action.payload.news_item }, state.items),
        apps: appsAdapter.upsertMany(action.payload.apps, state.apps),
        editingNewsItem: onLoadableSuccess(convertNewsItem(action.payload.news_item)),
      };
    case NewsActionTypes.GET_NEWS_ITEM_FAILED:
      return { ...state, itemStats: onLoadableError(action.error, initialNewsState.itemStats.data) };
    case NewsActionTypes.SET_NEW_NEWS_ITEM:
      return {
        ...state,
        editingNewsItem: onLoadableSuccess(action.payload),
        itemStats: initialNewsState.itemStats,
      };
    case NewsActionTypes.CREATE_NEWS_ITEM:
      return { ...state, editingNewsItem: onLoadableLoad(action.payload) };
    case NewsActionTypes.CREATE_NEWS_ITEM_COMPLETE:
      if (action.payload) {
        return {
          ...state,
          items: newsAdapter.addOne(action.payload, state.items),
          editingNewsItem: onLoadableSuccess(convertNewsItem(action.payload)),
        };
      }
      break;
    case NewsActionTypes.CREATE_NEWS_ITEM_FAILED:
      return { ...state, editingNewsItem: onLoadableError(action.error, state.editingNewsItem.data) };
    case NewsActionTypes.UPDATE_NEWS_ITEM:
      return { ...state, editingNewsItem: onLoadableLoad(state.editingNewsItem.data) };
    case NewsActionTypes.UPDATE_NEWS_ITEM_COMPLETE:
      return {
        ...state,
        items: newsAdapter.updateOne({ id: action.payload.id, changes: action.payload }, state.items),
        editingNewsItem: onLoadableSuccess(convertNewsItem(action.payload)),
      };
    case NewsActionTypes.UPDATE_NEWS_ITEM_FAILED:
      return { ...state, editingNewsItem: onLoadableError(action.error, state.editingNewsItem.data) };
    case NewsActionTypes.DELETE_NEWS_ITEM:
      return { ...state, editingNewsItem: onLoadableLoad(initialNewsState.editingNewsItem.data) };
    case NewsActionTypes.DELETE_NEWS_ITEM_COMPLETE:
      return {
        ...state,
        editingNewsItem: onLoadableSuccess(null),
        items: newsAdapter.removeOne(action.payload.id, state.items),
      };
    case NewsActionTypes.DELETE_NEWS_ITEM_FAILED:
      return { ...state, editingNewsItem: onLoadableError(action.error, state.editingNewsItem.data) };
    case NewsActionTypes.GET_LOCATIONS:
      return { ...state, locations: onLoadableLoad(state.locations.data) };
    case NewsActionTypes.GET_LOCATIONS_COMPLETED:
      return { ...state, locations: onLoadableSuccess(action.payload) };
    case NewsActionTypes.GET_LOCATIONS_FAILED:
      return { ...state, locations: onLoadableError(action.error, state.locations.data) };
  }
  return state;
}

function convertNewsItem(newsItem: NewsItem): CreateNews {
  return {
    action_button: newsItem.buttons.length ? newsItem.buttons[ 0 ] : null,
    app_ids: newsItem.app_ids,
    id: newsItem.id,
    media: newsItem.media,
    message: newsItem.message,
    qr_code_caption: newsItem.qr_code_caption,
    role_ids: newsItem.role_ids,
    scheduled_at: newsItem.scheduled_at ? new Date(newsItem.scheduled_at * 1000) : null,
    target_audience: newsItem.target_audience,
    title: newsItem.title,
    type: newsItem.type,
    group_type: newsItem.group_type,
    locations: newsItem.locations,
    group_visible_until: newsItem.group_visible_until ? new Date(newsItem.group_visible_until * 1000) : null,
  };
}
