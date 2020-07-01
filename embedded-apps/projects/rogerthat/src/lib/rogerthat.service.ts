import { Injectable, NgZone } from '@angular/core';
import { Store } from '@ngrx/store';
import { CameraType, GetNewsStreamItemsRequestTO, GetNewsStreamItemsResponseTO, RogerthatContext } from 'rogerthat-plugin';
import { from, Observable, of, Subject, throwError } from 'rxjs';
import { catchError, filter, map, mergeMap, take } from 'rxjs/operators';
import { AppVersion } from './rogerthat';
import { ScanQrCodeUpdateAction, SetServiceDataAction, SetUserDataAction } from './rogerthat.actions';
import { RogerthatState } from './rogerthat.state';

@Injectable({ providedIn: 'root' })
export class RogerthatService {
  version: AppVersion;
  private apiCallResult$: Subject<{ method: string; result: any; error: string | null; tag: string }>;

  constructor(private ngZone: NgZone,
              private store: Store<RogerthatState>) {
  }

  initialize() {
    NgZone.assertInAngularZone();
    this.store.dispatch(new SetUserDataAction(rogerthat.user.data));
    this.store.dispatch(new SetServiceDataAction(rogerthat.service.data));
    const cb = rogerthat.callbacks;
    // Callbacks aren't using promises so these need to run in the ngZone
    cb.qrCodeScanned(result => this.ngZone.run(() => this.store.dispatch(new ScanQrCodeUpdateAction(result))));
    cb.userDataUpdated(() => this.ngZone.run(() => this.store.dispatch(new SetUserDataAction(rogerthat.user.data))));
    cb.serviceDataUpdated(() => this.ngZone.run(() => this.store.dispatch(new SetServiceDataAction(rogerthat.service.data))));
    const [major, minor, patch] = rogerthat.system.appVersion.split('.').slice(0, 3).map(s => parseInt(s, 10));
    this.version = { major, minor, patch };
  }

  getContext(): Observable<RogerthatContext | null> {
    return from(this.wrapPromise(rogerthat.context())).pipe(map(result => result.context));
  }

  isSupported(androidVersion: [number, number, number], iosVersion: [number, number, number]) {
    if (rogerthat.system.os === 'android') {
      return this.isGreaterVersion(...androidVersion);
    } else {
      return this.isGreaterVersion(...iosVersion);
    }
  }

  isGreaterVersion(major: number, minor: number, patch: number) {
    const v = this.version;
    return (major < v.major || major === v.major && minor < v.minor || major === v.major && minor === v.minor && patch <= v.patch);
  }

  apiCall<T>(method: string, data?: any, tag?: string | null): Observable<T> {
    NgZone.assertInAngularZone();
    if (!tag) {
      tag = rogerthat.util.uuid();
    }
    if (data) {
      data = JSON.stringify(data);
    } else {
      data = '';
    }
    const callResult = rogerthat.api.call(method, data, tag, true);
    if (callResult instanceof Promise) {
      return from(this.wrapPromise(callResult)).pipe(
        map(result => (result && result.result ? JSON.parse(result.result) : null) as T),
        catchError(err => {
          let resultError = err;
          if (err.hasOwnProperty('error')) {
            resultError = this.getError(err);
          }
          return throwError(resultError);
        }));
    } else {
      if (!this.apiCallResult$) {
        this.setupApiResultListener();
      }
      return this.ngZone.run(() => this.apiCallResult$.pipe(
        filter(r => r.method === method && r.tag === tag),
        mergeMap(result => result.error ? throwError(this.getError(result.error)) : of(result.result as T)),
        take(1),
      ));
    }
  }

  getNewsStreamItems(request: GetNewsStreamItemsRequestTO): Observable<GetNewsStreamItemsResponseTO> {
    return from(this.wrapPromise(rogerthat.news.getNewsStreamItems(request)));
  }

  startScanningQrCode(cameraType: CameraType): Observable<void> {
    return from(this.wrapPromise(rogerthat.camera.startScanningQrCode(cameraType)));
  }

  private getError(error: any) {
    try {
      return JSON.parse(error.error);
    } catch (ignored) {
      return error.error;
    }
  }

  private setupApiResultListener() {
    this.apiCallResult$ = new Subject();
    rogerthat.api.callbacks.resultReceived((method, result, error, tag) => {
      this.ngZone.run(() => this.apiCallResult$.next({
        method,
        result: result ? JSON.parse(result) : null,
        error,
        tag,
      }));
    });
  }

  private wrapPromise<T>(promise: Promise<T>) {
      return new Promise<T>((resolve, reject) => {
        promise.then(result => this.ngZone.run(() => resolve(result)));
        promise.catch(err => this.ngZone.run(() => reject(err)));
      });
  }
}
