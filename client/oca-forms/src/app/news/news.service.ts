import { HttpClient, HttpEvent, HttpParams, HttpRequest } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { Observable, of } from 'rxjs';
import { UploadedFile } from '../shared/images';
import { Loadable, NonNullLoadable, onLoadableSuccess } from '../shared/loadable/loadable';
import { ServiceMenuDetail } from '../shared/rogerthat';
import {
  CreateNews,
  NewsActionButtonMenuItem,
  NewsActionButtonType,
  NewsBroadcastItem,
  NewsBroadcastItemList,
  NewsItemType,
  NewsOptions,
  NewsStats,
  SimpleApp,
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
    return this._http.get<NewsBroadcastItemList>('/common/news', { params });
  }

  createNewsItem(newsItem: CreateNews) {
    return this._http.post<NewsBroadcastItem>(`/common/news`, newsItem);
  }

  getNewsItem(id: number) {
    return this._http.get<NewsStats>(`/common/news/${id}`);
  }

  updateNewsItem(id: number, newsItem: CreateNews) {
    return this._http.put<NewsBroadcastItem>(`/common/news/${id}`, newsItem);
  }

  deleteNewsItem(id: number) {
    return this._http.delete(`/common/news/${id}`);
  }

  getNewsOptions() {
    return this._http.get<NewsOptions>(`/common/broadcast/options`);
  }

  uploadImage(image: Blob): Observable<HttpEvent<UploadedFile>> {
    const data = new FormData();
    data.append('file', image);
    return this._http.request(new HttpRequest('POST', `/common/images/news`, data, { reportProgress: true }));
  }

  getApps() {
    return this._http.get<SimpleApp[]>('/common/apps');
  }

  getActionButtons(menu: Loadable<ServiceMenuDetail>): NonNullLoadable<UINewsActionButton[]> {
    if (menu.data) {
      const result: UINewsActionButton[] = [
        {
          type: NewsActionButtonType.WEBSITE,
          label: this._translate.instant('oca.website'),
          button: { action: '', caption: this._translate.instant('oca.open_website'), id: 'url' },
        },
        {
          type: NewsActionButtonType.ATTACHMENT,
          label: this._translate.instant('oca.attachment'),
          button: { action: '', caption: this._translate.instant('oca.attachment'), id: 'attachment' },
        },
        {
          type: NewsActionButtonType.EMAIL,
          label: this._translate.instant('oca.email_address'),
          email: '',
          button: { action: '', caption: this._translate.instant('oca.send_email'), id: 'email' },
        },
        {
          type: NewsActionButtonType.PHONE,
          label: this._translate.instant('oca.phone number'),
          phone: '',
          button: { action: '', caption: this._translate.instant('oca.call'), id: 'phone' },
        },
        // use 'as' to ignore bug in typescript: Type 'NewsActionButtonType' is not assignable to type 'NewsActionButtonType.MENU_ITEM'.
        ...menu.data.items.map(item => ({
          type: NewsActionButtonType.MENU_ITEM,
          label: item.label,
          button: { action: `smi://${item.tag}`, caption: item.label.slice(0, 16), id: item.tag },
        } as NewsActionButtonMenuItem)),
      ];
      return onLoadableSuccess(result);
    } else {
      return { ...menu, data: [] };
    }
  }

  getNewNewsItem(broadcastTypes: string[], defaultAppId: string): Observable<CreateNews> {
    return of({
      action_button: null,
      type: NewsItemType.NORMAL,
      target_audience: null,
      app_ids: [ defaultAppId ],
      scheduled_at: 0,
      title: '',
      message: '',
      media: null,
      facebook_access_token: null,
      tags: [],
      broadcast_on_twitter: false,
      broadcast_on_facebook: false,
      broadcast_type: broadcastTypes[0],
      role_ids: [],
      qr_code_caption: null,
    });
  }
}
