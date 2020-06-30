import { Injectable, NgZone } from '@angular/core';
import { Store } from '@ngrx/store';
import { CameraType, GetNewsStreamItemsRequestTO, GetNewsStreamItemsResponseTO, RogerthatContext } from 'rogerthat-plugin';
import { from, Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { AppVersion } from './rogerthat';
import { ScanQrCodeUpdateAction, SetServiceDataAction, SetUserDataAction } from './rogerthat.actions';
import { RogerthatState } from './rogerthat.state';

@Injectable({ providedIn: 'root' })
export class RogerthatService {
  version: AppVersion;

  constructor(private ngZone: NgZone,
              private store: Store<RogerthatState>) {
  }

  initialize() {
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
    return from(rogerthat.context()).pipe(map(result => result.context));
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
    if (!tag) {
      tag = rogerthat.util.uuid();
    }
    if (data) {
      data = JSON.stringify(data);
    } else {
      data = '';
    }
    return from(rogerthat.api.call(method, data, tag, true)).pipe(
      map(result => (result && result.result ? JSON.parse(result.result) : null) as T),
      catchError(err => {
        let resultError = err;
        if (err.hasOwnProperty('error')) {
          try {
            resultError = JSON.parse(err.error);
          } catch (ignored) {
            resultError = err.error;
          }
        }
        return throwError(resultError);
      }),
    );
  }

  getNewsStreamItems(request: GetNewsStreamItemsRequestTO): Observable<GetNewsStreamItemsResponseTO> {
    return from(rogerthat.news.getNewsStreamItems(request));
  }

  startScanningQrCode(cameraType: CameraType): Observable<void> {
    return from(rogerthat.camera.startScanningQrCode(cameraType));
  }

}
