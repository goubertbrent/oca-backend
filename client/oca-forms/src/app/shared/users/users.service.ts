import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { UserDetailsTO } from './interfaces';

@Injectable({ providedIn: 'root' })
export class UsersService {

  constructor(private http: HttpClient) {
  }

  searchUsers(query: string) {
    return this.http.get<UserDetailsTO[]>('/common/users/search', { params: { query } });
  }
}
