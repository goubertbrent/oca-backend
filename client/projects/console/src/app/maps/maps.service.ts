import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { MapConfig } from './maps';

@Injectable({ providedIn: 'root' })
export class MapsService {
  constructor(private http: HttpClient) {
  }

  getMapConfig(appId: string) {
    return this.http.get<MapConfig>( `/console-api/maps/${appId}`);
  }

  saveMapConfig(appId: string, config: MapConfig) {
    return this.http.put<MapConfig>(`/console-api/maps/${appId}`, config);
  }
}
