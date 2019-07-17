import { HttpClient } from '@angular/common/http';
import { Injectable, NgZone } from '@angular/core';
import { Observable } from 'rxjs';
import { shareReplay, switchMap } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import LoginOptions = facebook.LoginOptions;
import StatusResponse = facebook.StatusResponse;

export const enum FBTask {
  /**
   * Create ads and unpublished Page Posts
   */
  ADVERTISE = 'ADVERTISE',
  /**
   *  View Insights
   */
  ANALYZE = 'ANALYZE',
  /**
   * Create Posts as the Page
   */
  CREATE_CONTENT = 'CREATE_CONTENT',
  /**
   * Approve and manage Page tasks for Users
   */
  MANAGE = 'MANAGE',
  /**
   * Respond to and delete comments, send messages as the Page
   */
  MODERATE = 'MODERATE',
}

export interface FBPage {
  access_token: string;
  name: string;
  id: number;
  tasks: FBTask[];
}

export interface FBPagesResult {
  error?: {
    code: number;
    fbtrace_id: string;
    message: string;
    type: string;
  };
  data: FBPage[];
  paging: {
    cursors: {
      before: string;
      after: string;
    }
  };
}

@Injectable({ providedIn: 'root' })
export class FacebookService {
  private initialized$: Observable<string>;
  private initialized = false;

  constructor(private http: HttpClient,
              private zone: NgZone) {
  }

  init(): Observable<string> {
    if (!this.initialized$) {
      this.initialized$ = new Observable<string>(subscriber => {
        this.http.get<string>('/common/settings/facebook-app-id').subscribe(appId => {
          if (!appId) {
            this.initialized = true;
            subscriber.error('No facebook app id found');
            subscriber.complete();
            return;
          }
          if (typeof FB !== 'undefined') {
            subscriber.next(appId);
            subscriber.complete();
            this.initialized = true;
            return;
          }
          (window as any).fbAsyncInit = () => {
            this.zone.run(() => {
              console.log('fb initialized');
              FB.init({
                appId,
                status: true, // Check Facebook Login status
                cookie: true, // enable cookies to allow the server to access the session
                xfbml: false,
                version: 'v3.3',
              });
              subscriber.next(appId);
              subscriber.complete();
              this.initialized = true;
            });
          };
          const body = document.querySelector('body') as HTMLBodyElement;
          const fbElement = document.createElement('script');
          fbElement.type = 'text/javascript';
          fbElement.async = true;
          fbElement.defer = true;
          const script = environment.production ? 'sdk.js' : 'sdk/debug.js';
          fbElement.src = `https://connect.facebook.net/en_US/${script}`;
          body.append(fbElement);
        });
      }).pipe(shareReplay(1));
    }
    return this.initialized$;
  }

  login = (options: LoginOptions) => this.init().pipe(switchMap(() => new Observable<StatusResponse>(subscriber => {
    FB.login(response => {
      this.zone.run(() => {
        subscriber.next(response);
        subscriber.complete();
      });
    }, options);
  })));

  getAccounts = () => this.init().pipe(switchMap(() => new Observable<FBPagesResult>(subscriber => {
    const fields = [ 'access_token', 'name', 'id', 'tasks' ];
    FB.api<FBPagesResult>(`/me/accounts?fields=${fields.join(',')}`, response => {
      if (response.error) {
        subscriber.error(response.error);
      } else {
        this.zone.run(() => {
          subscriber.next(response);
          subscriber.complete();
        });
      }
    });
  })));
}
