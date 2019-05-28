import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { CitySettings, CreateProject, Project, ProjectStatistics } from './projects';

@Injectable({ providedIn: 'root' })
export class ParticipationService {

  constructor(private http: HttpClient) {
  }

  getProjects() {
    return this.http.get<Project[]>('/common/participation/projects');
  }

  createProject(project: CreateProject) {
    return this.http.post<Project>('/common/participation/projects', project);
  }

  getProject(projectId: number) {
    return this.http.get<Project>(`/common/participation/projects/${projectId}`);
  }

  saveProject(projectId: number, project: Project) {
    return this.http.put<Project>(`/common/participation/projects/${projectId}`, project);
  }

  getProjectStatistics(projectId: number, cursor: string | null) {
    const params = new HttpParams({ fromObject: (cursor ? { cursor } : {}) });
    return this.http.get<ProjectStatistics>(`/common/participation/projects/${projectId}/statistics`, { params });
  }

  getSettings() {
    return this.http.get<CitySettings>('/common/participation/settings');
  }

  saveSettings(settings: CitySettings) {
    return this.http.put<CitySettings>('/common/participation/settings', settings);
  }

}
