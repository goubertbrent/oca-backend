import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { tap } from 'rxjs/operators';
import { Community, CreateCommunity, SimpleApp, UpdateNewsImagePayload } from './community/communities';
import { NewsGroup, NewsSettings, NewsSettingsWithGroups } from './news/news';

@Injectable({
  providedIn: 'root',
})
export class CommunityService {
  appsCache: SimpleApp[] = [];

  constructor(private http: HttpClient) {
  }

  getApps() {
    if (this.appsCache.length) {
      return of(this.appsCache);
    }
    return this.http.get<SimpleApp[]>('/console-api/apps').pipe(tap(apps => this.appsCache = apps));
  }

  getCountries() {
    return this.http.get<{ code: string; name: string; }[]>('/console-api/communities/countries');
  }

  getCommunities(country: string | null) {
    return this.http.get<Community[]>('/console-api/communities', { params: new HttpParams({ fromObject: { country: country ?? '' } }) });
  }

  getCommunity(id: number) {
    return this.http.get<Community>(`/console-api/communities/${id}`);
  }

  createCommunity(value: CreateCommunity) {
    return this.http.post<Community>(`/console-api/communities`, value);
  }

  updateCommunity(communityId: number, value: CreateCommunity) {
    return this.http.put<Community>(`/console-api/communities/${communityId}`, value);
  }

  deleteCommunity(communityId: number) {
    return this.http.delete(`/console-api/communities/${communityId}`);
  }

  getNewsSettings(communityId: number) {
    return this.http.get<NewsSettingsWithGroups>(`/console-api/communities/${communityId}/news-settings`);
  }

  updateNewsSettings(communityId: number, settings: NewsSettings) {
    return this.http.put<NewsSettings>(`/console-api/communities/${communityId}/news-settings`, settings);
  }

  updateNewsGroupImage(communityId: number, groupId: string, payload: UpdateNewsImagePayload): Observable<NewsGroup> {
    const formData = new FormData();
    formData.append('file', payload.file);
    return this.http.put<NewsGroup>(`/console-api/communities/${communityId}/news-settings/${groupId}/background-image`, formData);
  }

}
