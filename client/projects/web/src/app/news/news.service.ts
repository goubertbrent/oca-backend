import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { NewsItem, retryWithBackoff } from '@oca/web-shared';

export const enum NewsStatisticsActionType {
  REACH = 'reached',
  ACTION = 'action',
  SHARE = 'share',
}

@Injectable({
  providedIn: 'root',
})
export class NewsService {

  constructor(private http: HttpClient) {
  }

  getNewsItem(appUrlName: string, id: number) {
    return this.http.get<NewsItem>(`/api/web/${appUrlName}/news/id/${id}`);
  }

  saveNewsStatistic(appUrlName: string, newsId: number, action: NewsStatisticsActionType) {
    return this.http.post(`/api/web/${appUrlName}/news/id/${newsId}/action/${action}`, null).pipe(retryWithBackoff());
  }
}
