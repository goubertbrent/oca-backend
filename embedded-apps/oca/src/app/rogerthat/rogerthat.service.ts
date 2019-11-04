import { Injectable, NgZone } from '@angular/core';
import { Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { CameraType, RogerthatCallbacks, RogerthatContext, RogerthatError } from 'rogerthat-plugin';
import { Observable, of, Subject, throwError } from 'rxjs';
import { filter, mergeMap } from 'rxjs/operators';
import { DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES } from '../shared/consts';
import { AppVersion } from './rogerthat';
import { ScanQrCodeUpdateAction, SetServiceDataAction, SetUserDataAction } from './rogerthat.actions';
import { RogerthatState } from './rogerthat.state';

@Injectable({ providedIn: 'root' })
export class RogerthatService {
  version: AppVersion;
  private apiCallResult$ = new Subject<{ method: string; result: any; error: string | null; tag: string }>();

  constructor(private ngZone: NgZone,
              private store: Store<RogerthatState>,
              private translate: TranslateService) {
  }

  initialize() {
    this.store.dispatch(new SetUserDataAction(rogerthat.user.data));
    this.store.dispatch(new SetServiceDataAction(rogerthat.service.data));
    const cb = rogerthat.callbacks as RogerthatCallbacks;
    cb.qrCodeScanned(result => this.ngZone.run(() => this.store.dispatch(new ScanQrCodeUpdateAction(result))));
    cb.userDataUpdated(() => this.ngZone.run(() => this.store.dispatch(new SetUserDataAction(rogerthat.user.data))));
    cb.serviceDataUpdated(() => this.ngZone.run(() => this.store.dispatch(new SetServiceDataAction(rogerthat.service.data))));
    rogerthat.api.callbacks.resultReceived((method, result, error, tag) =>
      this.ngZone.run(() => this.apiCallResult$.next({
        method,
        result: result ? JSON.parse(result) : null,
        error,
        tag,
      })));
    const [major, minor, patch] = rogerthat.system.appVersion.split('.').slice(0, 3).map(s => parseInt(s, 10));
    this.version = { major, minor, patch };
  }

  getContext(): Observable<RogerthatContext | null> {
    const zone = this.ngZone;
    return new Observable<RogerthatContext | null>(emitter => {
      rogerthat.context(success, error);

      function success(context: { context: RogerthatContext | null }) {
        zone.run(() => {
          emitter.next(context.context);
          emitter.complete();
        });
      }

      function error(err: RogerthatError) {
        zone.run(() => {
          emitter.error(err);
        });
      }
    });
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
    rogerthat.api.call(method, data, tag);
    return this.apiCallResult$.pipe(
      filter(r => r.method === method && r.tag === tag),
      mergeMap(result => result.error ? throwError(result.error) : of(result.result as T)),
    );
  }

  startScanningQrCode(cameraType: CameraType): Observable<null> {
    const zone = this.ngZone;
    return new Observable(emitter => {
      rogerthat.camera.startScanningQrCode(cameraType, success, error);

      function success() {
        zone.run(() => {
          emitter.next(null);
          emitter.complete();
        });
      }

      function error(err: RogerthatError) {
        zone.run(() => {
          emitter.error(err);
        });
      }
    });
  }

}
