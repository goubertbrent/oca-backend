import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { NewsItem } from '@oca/web-shared';
import { Observable, of } from 'rxjs';
import {
  CityAppLocations,
  CreateNews,
  NewsCommunity,
  NewsFeaturedItem,
  NewsItemBasicStatistics,
  NewsItemList,
  NewsItemTimeStatistics,
  NewsOptions,
  NewsStats,
  RssSettings,
  SetFeaturedItemData,
} from './news';

@Injectable({ providedIn: 'root' })
export class NewsService {

  constructor(private _http: HttpClient,
              private _translate: TranslateService) {
  }

  getNewsList(cursor: string | null, query: string | null, amount: number | undefined) {
    let params = new HttpParams();
    if (cursor) {
      params = params.set('cursor', cursor);
    }
    if (query) {
      params = params.set('query', encodeURIComponent(query));
    }
    if (amount) {
      params = params.set('amount', amount.toString());
    }
    return this._http.get<NewsItemList>('/common/news', { params });
  }

  getNewsItemsStats(ids: number[]): Observable<NewsItemBasicStatistics[]> {
    let params = new HttpParams();
    if (ids.length === 0) {
      return of([]);
    }
    for (const id of ids) {
      params = params.append('id', id.toString());
    }
    return this._http.get<NewsItemBasicStatistics[]>('/common/news/statistics', { params });
  }

  createNewsItem(newsItem: CreateNews) {
    // Returns null in case item needs to be reviewed
    return this._http.post<NewsItem | null>(`/common/news`, convertNewsItem(newsItem));
  }

  getNewsItem(id: number) {
    return this._http.get<NewsStats>(`/common/news/${id}`);
  }

  getNewsItemTimeStats(id: number) {
    return this._http.get<NewsItemTimeStatistics>(`/common/news/${id}/statistics`);
  }

  updateNewsItem(id: number, newsItem: CreateNews) {
    return this._http.put<NewsItem>(`/common/news/${id}`, convertNewsItem(newsItem));
  }

  deleteNewsItem(id: number) {
    return this._http.delete(`/common/news/${id}`);
  }

  getNewsOptions() {
    return this._http.get<NewsOptions>(`/common/news-options`);
  }

  getLocations(communityId: number) {
    return this._http.get<CityAppLocations>(`/common/locations/${communityId}`);
  }

  getCommunities() {
    return this._http.get<NewsCommunity[]>(`/common/news/communities`);
  }

  getFeaturedItems() {
    return this._http.get<NewsFeaturedItem[]>(`/common/news/featured`);
  }

  setFeaturedItem(item: SetFeaturedItemData) {
    return this._http.put<NewsFeaturedItem[]>(`/common/news/featured`, item);
  }

  getRssSettings() {
    return this._http.get<RssSettings>(`/common/news/rss`);
  }

  saveRssSettings(settings: RssSettings) {
    return this._http.put<RssSettings>(`/common/news/rss`, settings);
  }

  validateUrl(url: string) {
    return this._http.post<{ url: string; success: boolean; errormsg: string | null }>(`/common/news/rss.validate`, {url});
  }

  copyNewsItem(newsItem: NewsItem): CreateNews {
    return {
      community_ids: newsItem.community_ids,
      action_button: newsItem.buttons ? newsItem.buttons[ 0 ] : null,
      scheduled_at: null,
      group_type: newsItem.group_type,
      group_visible_until: null,
      qr_code_caption: newsItem.qr_code_caption,
      locations: newsItem.locations,
      id: null,
      media: newsItem.media,
      message: newsItem.message,
      target_audience: newsItem.target_audience,
      title: newsItem.title,
      type: newsItem.type,
    };
  }
}

function convertNewsItem(item: CreateNews<Date>): CreateNews<number> {
  return {
    ...item,
    scheduled_at: item.scheduled_at && Math.round(item.scheduled_at.getTime() / 1000),
    group_visible_until: item.group_visible_until && Math.round(item.group_visible_until.getTime() / 1000),
  };
}
