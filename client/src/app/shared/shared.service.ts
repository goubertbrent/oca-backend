import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Budget } from './billing/billing';
import { BrandingSettings, GlobalConfig, SolutionSettings } from './interfaces/oca';
import { App, AppStatistics, ServiceIdentityInfo, ServiceMenuDetail } from './interfaces/rogerthat';

@Injectable({ providedIn: 'root' })
export class SharedService {
  hasYoutubeApi = false;

  constructor(private http: HttpClient) {
  }

  getSolutionSettings() {
    return this.http.get<SolutionSettings>('/common/settings');
  }

  getMenu() {
    return this.http.get<ServiceMenuDetail>('/common/get_menu');
  }

  getServiceIdentityInfo() {
    return this.http.get<ServiceIdentityInfo>('/common/get_info');
  }

  getApps() {
    return this.http.get<App[]>('/common/apps');
  }

  getAppStatistics() {
    return this.http.get<AppStatistics[]>('/common/statistics/apps');
  }

  getBudget() {
    return this.http.get<Budget>('/common/billing/budget');
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
}
