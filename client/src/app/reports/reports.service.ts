import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Incident, IncidentList, IncidentStatus } from './pages/reports';

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
}
