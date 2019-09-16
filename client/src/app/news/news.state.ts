import { createEntityAdapter, EntityState } from '@ngrx/entity';
import { createFeatureSelector, createSelector } from '@ngrx/store';
import { DEFAULT_LOADABLE, Loadable } from '../shared/loadable/loadable';
import { CityAppLocations, CreateNews, NewsApp, NewsItem, NewsItemList, NewsOptions, NewsStats } from './interfaces';

function selectNewsItemId(item: NewsItem) {
  return item.id;
}

function selectAppId(item: NewsApp) {
  return item.id;
}

export const appsAdapter = createEntityAdapter<NewsApp>({
  selectId: selectAppId,
  sortComparer: (a, b) => a.name.localeCompare(b.name),
});
export const newsAdapter = createEntityAdapter<NewsItem>({
  selectId: selectNewsItemId,
  sortComparer: (first, second) => second.timestamp - first.timestamp,
});
export const newsSelectors = newsAdapter.getSelectors();

export const initialNewsState: NewsState = {
  apps: appsAdapter.getInitialState(),
  items: newsAdapter.getInitialState({ cursor: null, more: true }),
  editingNewsItem: DEFAULT_LOADABLE,
  itemStats: DEFAULT_LOADABLE,
  listStatus: DEFAULT_LOADABLE,
  newsOptions: DEFAULT_LOADABLE,
  locations: DEFAULT_LOADABLE,
};

export interface NewsItemsState extends EntityState<NewsItem> {
  more: boolean;
  cursor: string | null;
}

export interface NewsState {
  apps: EntityState<NewsApp>;
  items: NewsItemsState;
  editingNewsItem: Loadable<CreateNews>;
  itemStats: Loadable<NewsStats>;
  listStatus: Loadable<NewsItemList>;
  newsOptions: Loadable<NewsOptions>;
  locations: Loadable<CityAppLocations>;
}

const featureSelector = createFeatureSelector<NewsState>('news');

export const getNews = createSelector(featureSelector, s => s.items);
export const getNewsItems = createSelector(getNews, s => newsSelectors.selectAll(s));
export const getNewsItemListStatus = createSelector(featureSelector, s => s.listStatus);
export const hasMoreNews = createSelector(featureSelector, s => s.items.more);
export const getNewsCursor = createSelector(featureSelector, s => s.items.cursor);
export const getNewsItemStats = createSelector(featureSelector, s => s.itemStats);
export const getEditingNewsItem = createSelector(featureSelector, s => s.editingNewsItem);
export const getNewsOptions = createSelector(featureSelector, s => s.newsOptions);
export const getLocations = createSelector(featureSelector, s => s.locations);
