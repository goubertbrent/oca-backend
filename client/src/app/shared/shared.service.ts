import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { CommunityGeoFence } from '@oca/web-shared';
import { map } from 'rxjs/operators';
import { Budget } from './billing/billing';
import { BrandingSettings, Country, GlobalConfig, PlaceType, SolutionSettings } from './interfaces/oca';

@Injectable({ providedIn: 'root' })
export class SharedService {
  hasYoutubeApi = false;

  constructor(private http: HttpClient) {
  }

  getSolutionSettings() {
    return this.http.get<SolutionSettings>('/common/settings');
  }

  getBudget() {
    return this.http.get<Budget>('/common/billing/budget');
  }

  addBudget(vat: string) {
    return this.http.post<Budget>('/common/billing/budget', { vat });
  }

  getBrandingSettings() {
    return this.http.get<BrandingSettings>('/common/settings/branding');
  }

  getGlobalConstants() {
    return this.http.get<GlobalConfig>('/common/consts');
  }

  ensureYoutubeLoaded() {
    if (!this.hasYoutubeApi) {
      const tag = document.createElement('script');
      tag.src = 'https://www.youtube.com/iframe_api';
      const firstScriptTag = document.getElementsByTagName('script')[ 0 ];
      (firstScriptTag.parentNode as HTMLBodyElement).insertBefore(tag, firstScriptTag);
      this.hasYoutubeApi = true;
    }
  }

  updateAvatar(avatar_url: string) {
    return this.http.put<BrandingSettings>('/common/settings/avatar', { avatar_url });
  }

  updateLogo(logo_url: string) {
    return this.http.put<BrandingSettings>('/common/settings/logo', { logo_url });
  }

  getCountries(): Observable<Country[]> {
    return this.http.get<{ countries: [string, string][] }>('/common/countries').pipe(
      map(results => results.countries.map(([code, name]) => ({ code, name }))),
    );
  }

  getAvailablePlaceTypes() {
    return this.http.get<{ results: PlaceType[] }>('/common/available-place-types');
  }

  getGeoFence(){
    return this.http.get<CommunityGeoFence>(`/common/community/geo-fence`);
  }
}
