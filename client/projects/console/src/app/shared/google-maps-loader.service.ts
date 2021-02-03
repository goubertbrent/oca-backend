import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { ReplaySubject } from 'rxjs';

export const googleMapsKey = 'AIzaSyAPesOjDo8VzgaUeAsc4Od-GoBBO11vQZE';

@Injectable({ providedIn: 'root' })
export class GoogleMapsLoaderService {
  private apiLoaded$ = new ReplaySubject<boolean>();
  private hasRequested = false;

  constructor(private http: HttpClient) {
    this.apiLoaded$.next(false);
  }

  loadApi() {
    if (!this.hasRequested) {
      this.hasRequested = true;
      this.http.jsonp(`https://maps.googleapis.com/maps/api/js?key=${googleMapsKey}`, 'callback').subscribe(() => {
        this.apiLoaded$.next(true);
      }, error => {
        console.error(error);
        this.hasRequested = false;
        this.apiLoaded$.next(false);
      });
    }
    return this.apiLoaded$;
  }
}
