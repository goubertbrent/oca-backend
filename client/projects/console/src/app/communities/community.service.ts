import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { CommunityGeoFence } from '@oca/web-shared';
import { Observable, of } from 'rxjs';
import { tap } from 'rxjs/operators';
import { Community, CommunityMapSettings, CreateCommunity, SimpleApp, UpdateNewsImagePayload } from './community/communities';
import { HomeScreen } from './homescreen/models';
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

  getHomeScreen(communityId: number, homeScreenId: string) {
    return this.http.get<HomeScreen>(`/console-api/communities/${communityId}/home-screen/${homeScreenId}`);
  }

  updateHomeScreen(communityId: number, homeScreenId: string, data: HomeScreen) {
    return this.http.put<HomeScreen>(`/console-api/communities/${communityId}/home-screen/${homeScreenId}`, data);
  }

  publishHomeScreen(communityId: number, homeScreenId: string) {
    return this.http.put(`/console-api/communities/${communityId}/home-screen/${homeScreenId}/publish`, {});
  }

  testHomeScreen(communityId: number, homeScreenId: string, testUser: string) {
    return this.http.post(`/console-api/communities/${communityId}/home-screen/${homeScreenId}/test`, { test_user: testUser });
  }

  getGeoFence(communityId: number) {
    return this.http.get<CommunityGeoFence>(`/console-api/communities/${communityId}/geo-fence`);
  }

  updateGeoFence(communityId: number, data: CommunityGeoFence) {
    return this.http.put<CommunityGeoFence>(`/console-api/communities/${communityId}/geo-fence`, data);
  }

  getMapSettings(communityId: number) {
    return this.http.get<CommunityMapSettings>(`/console-api/communities/${communityId}/map-settings`);
  }

  updateMapSettings(communityId: number, data: CommunityMapSettings) {
    return this.http.put<CommunityMapSettings>(`/console-api/communities/${communityId}/map-settings`, data);
  }
}
