import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { ServiceMenuDetail } from '../shared/interfaces/rogerthat';
import { Loadable, NonNullLoadable, onLoadableSuccess } from '../shared/loadable/loadable';
import { OPEN_OPTIONS } from './consts';
import {
  CityAppLocations,
  CreateNews,
  NewsActionButtonMenuItem,
  NewsActionButtonType,
  NewsItem,
  NewsItemList,
  NewsOptions,
  NewsStats,
  UINewsActionButton,
} from './interfaces';

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

  getActionButtons(menu: Loadable<ServiceMenuDetail>): NonNullLoadable<Readonly<UINewsActionButton>[]> {
    if (menu.data) {
      const defaultOpenOption = OPEN_OPTIONS[ 0 ];
      const result: UINewsActionButton[] = [
        {
          type: NewsActionButtonType.WEBSITE,
          label: this._translate.instant('oca.Website'),
          button: { action: '', caption: this._translate.instant('oca.open_website'), id: 'url' },
        },
        {
          type: NewsActionButtonType.ATTACHMENT,
          label: this._translate.instant('oca.Attachment'),
          button: { action: '', caption: this._translate.instant('oca.Attachment'), id: 'attachment' },
        },
        {
          type: NewsActionButtonType.EMAIL,
          label: this._translate.instant('oca.email_address'),
          email: '',
          button: { action: '', caption: this._translate.instant('oca.send_email'), id: 'email' },
        },
        {
          type: NewsActionButtonType.PHONE,
          label: this._translate.instant('oca.Phone number'),
          phone: '',
          button: { action: '', caption: this._translate.instant('oca.Call'), id: 'phone' },
        },
        {
          type: NewsActionButtonType.OPEN,
          label: this._translate.instant('oca.open_app_function'),
          params: { action: defaultOpenOption.value },
          button: {
            action: `open://{"action": "${defaultOpenOption.value}"}`,
            caption: this._translate.instant(defaultOpenOption.label),
            id: 'open',
          },
        },
        // use 'as' to ignore bug in typescript: Type 'NewsActionButtonType' is not assignable to type 'NewsActionButtonType.MENU_ITEM'.
        ...menu.data.items.map(item => ({
          type: NewsActionButtonType.MENU_ITEM,
          label: item.label,
          button: { action: `smi://${item.tag}`, caption: item.label.slice(0, 15), id: item.tag },
        } as NewsActionButtonMenuItem)),
      ];
      return onLoadableSuccess(result);
    } else {
      return { ...menu, data: [] };
    }
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
      tags: newsItem.tags,
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
