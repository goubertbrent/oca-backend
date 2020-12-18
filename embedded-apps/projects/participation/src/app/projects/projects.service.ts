import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import { AddParticipationData, AppMerchant, AppMerchantList, City, Project, ProjectDetails, UserSettings } from './projects';

@Injectable({
  providedIn: 'root',
})
export class ProjectsService {
  BASE_URL = `${environment.baseUrl}/api/plugins/psp/v1.0/app`;
  constructor(private http: HttpClient) {
  }

  getCity(cityId: number) {
    return this.http.get<City>(`${this.BASE_URL}/cities/${cityId}`);
  }

  getProjects(cityId: number): Observable<Project[]> {
    return this.http.get<Project[]>(`${this.BASE_URL}/cities/${cityId}/projects`);
  }

  getProjectDetails(cityId: number, projectId: number, appUser: string): Observable<ProjectDetails> {
    const params = new HttpParams({ fromObject: { app_user: encodeURIComponent(appUser) } });
    return this.http.get<ProjectDetails>(`${this.BASE_URL}/cities/${cityId}/projects/${projectId}/details`, { params });
  }

  addParticipation(data: AddParticipationData): Observable<ProjectDetails> {
    return this.http.post<ProjectDetails>(`${this.BASE_URL}/scan`, data);
  }

  getCityMerchants(cityId: number, cursor?: string | null): Observable<AppMerchantList> {
    let params = new HttpParams({ fromObject: { lang: rogerthat.user.language } });
    if (cursor) {
      params = params.set('cursor', cursor);
    }
    return this.http.get<AppMerchantList>(`${this.BASE_URL}/cities/${cityId}/merchants`, { params });
  }

  getMerchant(cityId: number, id: number) {
    const params = new HttpParams({ fromObject: { lang: rogerthat.user.language } });
    return this.http.get<AppMerchant>(`${this.BASE_URL}/cities/${cityId}/merchants/${id}`, { params });
  }

  getUserSettings(appUser: string) {
    return this.http.get<UserSettings>(`${this.BASE_URL}/users/${encodeURIComponent(appUser)}/settings`).pipe(map(transformSettings));
  }

  saveUserSettings(appUser: string, settings: UserSettings) {
    return this.http.put<UserSettings>(`${this.BASE_URL}/users/${encodeURIComponent(appUser)}/settings`, settings).pipe
    (map(transformSettings),
    );
  }

}

function transformSettings(t: any): UserSettings {
  return {
    ...t,
    tour_date: t.tour_date ? new Date(t.tour_date) : null,
  };
}
