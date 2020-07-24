import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { PublicAppInfo } from '@oca/web-shared';

@Injectable({ providedIn: 'root' })
export class AppService {

  constructor(private http: HttpClient) {
  }

  getAppInfo(urlName: string) {
    return this.http.get<PublicAppInfo>(`/api/web/app/name/${urlName}`);
  }
}
