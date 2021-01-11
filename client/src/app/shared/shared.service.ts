import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Budget } from './billing/billing';
import { BrandingSettings, GlobalConfig, SolutionSettings } from './interfaces/oca';

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
}
