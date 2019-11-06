import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { MapConfig } from './maps';
import { Incident, IncidentList } from './pages/reports';

@Injectable({ providedIn: 'root' })
export class ReportsService {

  constructor(private http: HttpClient) {
  }

  getIncidents() {
    return this.http.get<IncidentList>('/common/reports/incidents');
  }

  getIncident(id: string) {
    return this.http.get<Incident>(`/common/reports/incidents/${id}`);
  }

  updateIncident(incident: Incident) {
    return this.http.put<Incident>(`/common/reports/incidents/${incident.id}`, incident);
  }

  getMapConfig() {
    return this.http.get<MapConfig>('/common/maps/reports');
  }

  saveMapConfig(payload: MapConfig) {
    return this.http.put<MapConfig>('/common/maps/reports', payload);
  }
}
