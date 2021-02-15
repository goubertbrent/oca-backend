import { createEntityAdapter, EntityState } from '@ngrx/entity';
import { createFeatureSelector, createSelector } from '@ngrx/store';
import { CallStateType, initialStateResult, NewsItem, ResultState } from '@oca/web-shared';
import { DEFAULT_LOADABLE, Loadable } from '../shared/loadable/loadable';
import {
  CityAppLocations,
  CreateNews,
  NewsCommunity,
  NewsFeaturedItem,
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
  items: newsAdapter.getInitialState({ cursor: null, more: true, can_edit_featured: false, can_edit_rss: false }),
  editingNewsItem: DEFAULT_LOADABLE,
  itemStats: DEFAULT_LOADABLE,
  timeStats: initialStateResult,
  listStatus: initialStateResult,
  newsOptions: initialStateResult,
  locations: DEFAULT_LOADABLE,
  communities: initialStateResult,
  featuredItems: initialStateResult,
};

export interface NewsItemsState extends EntityState<NewsListItem> {
  more: boolean;
  cursor: string | null;
  can_edit_rss: boolean;
  can_edit_featured: boolean;
}

export interface NewsState {
  items: NewsItemsState;
  editingNewsItem: Loadable<CreateNews>;
  itemStats: Loadable<NewsStats>;
  timeStats: ResultState<NewsItemTimeStatistics>;
  listStatus: ResultState<null>;
  newsOptions: ResultState<NewsOptions>;
  locations: Loadable<CityAppLocations>;
  communities: ResultState<NewsCommunity[]>;
  featuredItems: ResultState<NewsFeaturedItem[]>;
}

const featureSelector = createFeatureSelector<NewsState>('news');

export const getNews = createSelector(featureSelector, s => s.items);
export const getNewsItems = createSelector(getNews, s => newsSelectors.selectAll(s));
export const getNewsItemListStatus = createSelector(featureSelector, s => s.listStatus);
export const isNewsListLoading = createSelector(getNewsItemListStatus, s => s.state === CallStateType.LOADING);
export const hasMoreNews = createSelector(featureSelector, s => s.items.more);
export const getNewsCursor = createSelector(featureSelector, s => s.items.cursor);
export const canEditRss = createSelector(featureSelector, s => s.items.can_edit_rss);
export const canEditFeaturedItems = createSelector(featureSelector, s => s.items.can_edit_featured);
export const getNewsItemStats = createSelector(featureSelector, s => s.itemStats);
export const getNewsItemTimeStats = createSelector(featureSelector, s => s.timeStats.result);
export const areNewsItemTimeStatsLoading = createSelector(featureSelector, s => s.timeStats.state === CallStateType.LOADING);
export const getEditingNewsItem = createSelector(featureSelector, s => s.editingNewsItem);
export const getNewsOptions = createSelector(featureSelector, s => s.newsOptions.result);
export const getNewsOptionsError = createSelector(featureSelector, s =>
  s.newsOptions.state === CallStateType.ERROR ? s.newsOptions.error : null);
export const getLocations = createSelector(featureSelector, s => s.locations);
export const getNewsCommunities = createSelector(featureSelector, s => s.communities.result ?? []);
export const getFeaturedItems = createSelector(featureSelector, s => s.featuredItems.result ?? []);
