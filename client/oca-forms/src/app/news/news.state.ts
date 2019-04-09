import { createEntityAdapter, EntityState } from '@ngrx/entity';
import { createFeatureSelector, createSelector } from '@ngrx/store';
import { DEFAULT_LOADABLE, Loadable } from '../shared/loadable/loadable';
import { CreateNews, NewsApp, NewsBroadcastItem, NewsBroadcastItemList, NewsOptions, NewsStats } from './interfaces';

function selectNewsItemId(item: NewsBroadcastItem) {
  return item.id;
}

function selectAppId(item: NewsApp) {
  return item.id;
}

export const appsAdapter = createEntityAdapter<NewsApp>({ selectId: selectAppId });
export const newsAdapter = createEntityAdapter<NewsBroadcastItem>({ selectId: selectNewsItemId });
export const newsSelectors = newsAdapter.getSelectors();

export const initialNewsState: NewsState = {
  apps: appsAdapter.getInitialState(),
  items: newsAdapter.getInitialState({ cursor: null, more: true }),
  itemStats: DEFAULT_LOADABLE,
  status: DEFAULT_LOADABLE,
  listStatus: DEFAULT_LOADABLE,
  newsOptions: DEFAULT_LOADABLE,
};

export interface NewsItemsState extends EntityState<NewsBroadcastItem> {
  more: boolean;
  cursor: string | null;
}

export interface NewsState {
  apps: EntityState<NewsApp>;
  items: NewsItemsState;
  itemStats: Loadable<NewsStats>;
  status: Loadable<NewsBroadcastItem>;
  listStatus: Loadable<NewsBroadcastItemList>;
  newsOptions: Loadable<NewsOptions>;
}

const featureSelector = createFeatureSelector<NewsState>('news');

export const getNews = createSelector(featureSelector, s => s.items);
export const selectAllNewsItems = createSelector(getNews, newsSelectors.selectEntities);
export const getNewsItems = createSelector(getNews, s => newsSelectors.selectAll(s));
export const getNewsItemListStatus = createSelector(featureSelector, s => s.listStatus);
export const hasMoreNews = createSelector(featureSelector, s => s.items.more);
export const getNewsCursor = createSelector(featureSelector, s => s.items.cursor);
export const getNewsItem = createSelector(featureSelector, s => s.itemStats);
export const getCreateNewsItem = createSelector(getNewsItem, item => {
  const result: Loadable<CreateNews> = {
    success: item.success,
    loading: item.loading,
    error: item.loading,
    data: null,
  };
  if (item.success && item.data) {
    const newsItem = item.data.news_item;
    result.data = {
      action_button: newsItem.buttons.length ? newsItem.buttons[ 0 ] : null,
      app_ids: newsItem.app_ids,
      broadcast_on_facebook: newsItem.broadcast_on_facebook,
      broadcast_on_twitter: newsItem.broadcast_on_twitter,
      broadcast_type: newsItem.broadcast_type,
      facebook_access_token: null,
      id: newsItem.id,
      media: newsItem.media,
      message: newsItem.message,
      qr_code_caption: newsItem.qr_code_caption,
      role_ids: newsItem.role_ids,
      scheduled_at: newsItem.scheduled_at,
      tags: newsItem.tags,
      target_audience: newsItem.target_audience,
      title: newsItem.title,
      type: newsItem.type,
    };
  }
  return result;
});
export const getNewsOptions = createSelector(featureSelector, s => s.newsOptions);

