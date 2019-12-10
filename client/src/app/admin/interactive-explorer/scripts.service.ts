import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { NewScript, RunResult, RunScript, Script } from './scripts';

@Injectable()
export class ScriptsService {
  BASE_URL = '/admin/api';

  constructor(private http: HttpClient) {
  }

  getScripts() {
    return this.http.get<Script[]>(this.BASE_URL + '/scripts');
  }

  getScript(scriptId: number) {
    return this.http.get<Script>(`${this.BASE_URL}/scripts/${scriptId}`);
  }

  createScript(script: NewScript) {
    return this.http.post<Script>(`${this.BASE_URL}/scripts`, script);
  }

  updateScript(script: Script) {
    return this.http.put<Script>(`${this.BASE_URL}/scripts/${script.id}`, script);
  }

  deleteScript(scriptId: number): Observable<number> {
    return this.http.delete(`${this.BASE_URL}/scripts/${scriptId}`).pipe(
      map(() => scriptId),
    );
  }

  runFunction(parameters: RunScript) {
    return this.http.post<RunResult>(`${this.BASE_URL}/scripts/${parameters.id}`, parameters);
  }
}
