import { createEntityAdapter, EntityState } from '@ngrx/entity';
import { createFeatureSelector, createSelector } from '@ngrx/store';
import { CallStateType, initialStateResult, ResultState, NewsItem } from '@oca/web-shared';
import { DEFAULT_LOADABLE, Loadable } from '../shared/loadable/loadable';
import {
  CityAppLocations,
  CreateNews,
  NewsCommunity,
  NewsItemList,
  NewsItemTimeStatistics,
  NewsListItem,
  NewsOptions,
  NewsStats,
} from './news';

function selectNewsItemId(item: NewsItem) {
  return item.id;
}

export const newsAdapter = createEntityAdapter<NewsListItem>({
  selectId: selectNewsItemId,
  sortComparer: (first, second) => second.timestamp - first.timestamp,
});
export const newsSelectors = newsAdapter.getSelectors();

export const initialNewsState: NewsState = {
  items: newsAdapter.getInitialState({ cursor: null, more: true }),
  editingNewsItem: DEFAULT_LOADABLE,
  itemStats: DEFAULT_LOADABLE,
  timeStats: initialStateResult,
  listStatus: DEFAULT_LOADABLE,
  newsOptions: initialStateResult,
  locations: DEFAULT_LOADABLE,
  communities: initialStateResult,
};

export interface NewsItemsState extends EntityState<NewsListItem> {
  more: boolean;
  cursor: string | null;
}

export interface NewsState {
  items: NewsItemsState;
  editingNewsItem: Loadable<CreateNews>;
  itemStats: Loadable<NewsStats>;
  timeStats: ResultState<NewsItemTimeStatistics>;
  listStatus: Loadable<NewsItemList>;
  newsOptions: ResultState<NewsOptions>;
  locations: Loadable<CityAppLocations>;
  communities: ResultState<NewsCommunity[]>;
}

const featureSelector = createFeatureSelector<NewsState>('news');

export const getNews = createSelector(featureSelector, s => s.items);
export const getNewsItems = createSelector(getNews, s => newsSelectors.selectAll(s));
export const getNewsItemListStatus = createSelector(featureSelector, s => s.listStatus);
export const hasMoreNews = createSelector(featureSelector, s => s.items.more);
export const getNewsCursor = createSelector(featureSelector, s => s.items.cursor);
export const getNewsItemStats = createSelector(featureSelector, s => s.itemStats);
export const getNewsItemTimeStats = createSelector(featureSelector, s => s.timeStats.result);
export const areNewsItemTimeStatsLoading = createSelector(featureSelector, s => s.timeStats.state === CallStateType.LOADING);
export const getEditingNewsItem = createSelector(featureSelector, s => s.editingNewsItem);
export const getNewsOptions = createSelector(featureSelector, s => s.newsOptions.result);
export const getNewsOptionsError = createSelector(featureSelector, s =>
  s.newsOptions.state === CallStateType.ERROR ? s.newsOptions.error : null);
export const getLocations = createSelector(featureSelector, s => s.locations);
export const getNewsCommunities = createSelector(featureSelector, s => s.communities.result ?? []);
