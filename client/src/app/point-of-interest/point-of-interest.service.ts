import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { CreatePointOfInterest, PointOfInterest, PointOfInterestList, POIStatus } from './point-of-interest';

@Injectable({ providedIn: 'root' })
export class PointOfInterestService {

  constructor(private http: HttpClient) {
  }

  listPointOfInterest(cursor: string | null, query: string | null, status: POIStatus | null) {
    let params = new HttpParams();
    if (cursor) {
      params = params.append('cursor', cursor);
    }
    if (status != null) {
      params = params.append('status', status.toString());
    }
    if (query) {
      params = params.append('query', query);
    }
    return this.http.get<PointOfInterestList>('/common/point-of-interest', { params });
  }

  createPointOfInterest(poi: CreatePointOfInterest) {
    return this.http.post<PointOfInterest>(`/common/point-of-interest`, poi);
  }

  getPointOfInterest(id: number) {
    return this.http.get<PointOfInterest>(`/common/point-of-interest/${id}`);
  }

  updatePointOfInterest(id: number, poi: CreatePointOfInterest) {
    return this.http.put<PointOfInterest>(`/common/point-of-interest/${id}`, poi);
  }

  deletePointOfInterest(id: number) {
    return this.http.delete(`/common/point-of-interest/${id}`);
  }
}
