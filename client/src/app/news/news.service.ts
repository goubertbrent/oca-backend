import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { CityAppLocations, CreateNews, NewsItem, NewsItemList, NewsOptions, NewsStats } from './interfaces';

@Injectable({ providedIn: 'root' })
export class NewsService {

  constructor(private _http: HttpClient,
              private _translate: TranslateService) {
  }

  getNewsList(cursor: string | null) {
    let params = new HttpParams();
    if (cursor) {
      params = params.set('cursor', cursor);
    }
    return this._http.get<NewsItemList>('/common/news', { params });
  }

  createNewsItem(newsItem: CreateNews) {
    // Returns null in case item needs to be reviewed
    return this._http.post<NewsItem | null>(`/common/news`, convertNewsItem(newsItem));
  }

  getNewsItem(id: number) {
    return this._http.get<NewsStats>(`/common/news/${id}`);
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

  getLocations(appId: string) {
    return this._http.get<CityAppLocations>(`/common/locations/${appId}`);
  }

  copyNewsItem(newsItem: NewsItem): CreateNews {
    return {
      app_ids: newsItem.app_ids,
      action_button: newsItem.buttons ? newsItem.buttons[ 0 ] : null,
      scheduled_at: null,
      group_type: newsItem.group_type,
      group_visible_until: null,
      qr_code_caption: newsItem.qr_code_caption,
      locations: newsItem.locations,
      id: null,
      media: newsItem.media,
      message: newsItem.message,
      role_ids: newsItem.role_ids,
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
