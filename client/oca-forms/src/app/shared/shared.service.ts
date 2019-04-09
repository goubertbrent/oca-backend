import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { ServiceMenuDetail } from './rogerthat';

@Injectable({ providedIn: 'root' })
export class SharedService {
  constructor(private http: HttpClient) {
  }

  getMenu() {
    return this.http.get<ServiceMenuDetail>('/common/get_menu');
  }
}
