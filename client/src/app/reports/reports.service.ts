import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { EMPTY_ARRAY } from '../shared/util';
import { MapConfig } from './maps';
import { Incident, IncidentList, IncidentStatisticsList, IncidentStatus, RawIncidentStatistics } from './reports';

@Injectable({ providedIn: 'root' })
export class ReportsService {

  constructor(private http: HttpClient) {
  }

  getIncidents(data: { status: IncidentStatus; cursor: string | null }) {
    const object: { [ key: string ]: string } = { status: data.status };
    if (data.cursor) {
      object.cursor = data.cursor;
    }
    const params = new HttpParams({ fromObject: object });
    return this.http.get<IncidentList>('/common/reports/incidents', { params });
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

  listStatistics() {
    return this.http.get<IncidentStatisticsList>('/common/reports/incident-statistics');
  }

  getStatistics(dates: string[]): Observable<RawIncidentStatistics[]> {
    if (dates.length === 0) {
      return of(EMPTY_ARRAY);
    }
    const url = `/common/reports/incident-statistics/details`;
    let params = new HttpParams();
    for (const date of dates) {
      params = params.append('date', date);
    }
    return this.http.get<RawIncidentStatistics[]>(url, { params });
  }
}
