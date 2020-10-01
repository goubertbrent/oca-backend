import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { NgForm } from '@angular/forms';
import { Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { Observable } from 'rxjs';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { RequestFacebookReviewAction, UpdateFacebookAction } from '../../../actions';
import { getRequestFacebookReviewStatus, getUpdateFacebookStatus } from '../../../console.state';
import { App, APP_TYPES, AppTypes, PatchAppPayload, RogerthatApp, TrackTypes } from '../../../interfaces';
import { cloneDeep } from '../../../util';

@Component({
  selector: 'rcc-app-basic-configuration-form',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'basic-configuration-form.component.html',
})
export class AppBasicConfigurationFormComponent implements OnInit {
  appTypes = APP_TYPES;
  trackTypes = TrackTypes.TYPES;
  @Input() status: ApiRequestStatus;
  @Input() updateStatus: ApiRequestStatus;
  @Output() save = new EventEmitter<PatchAppPayload>();
  updateFacebookStatus$: Observable<ApiRequestStatus>;
  requestFacebookReviewStatus$: Observable<ApiRequestStatus>;

  constructor(private translate: TranslateService,
              private store: Store) {
  }

  private _app: App;

  get app(): App {
    return this._app;
  }

  @Input() set app(value: App) {
    this._app = cloneDeep(value);
  }

  private _rogerthatApp: RogerthatApp;

  get rogerthatApp(): RogerthatApp {
    return this._rogerthatApp;
  }

  @Input() set rogerthatApp(value: RogerthatApp) {
    this._rogerthatApp = cloneDeep(value);
  }

  get fbUrl() {
    const u = '<a href="https://developers.facebook.com/apps" target="_blank">https://developers.facebook.com/apps</a>';
    return this.translate.get('rcc.facebook_settings_explanation', { url: u });
  }

  ngOnInit() {
    this.updateFacebookStatus$ = this.store.select(getUpdateFacebookStatus);
    this.requestFacebookReviewStatus$ = this.store.select(getRequestFacebookReviewStatus);
  }

  isMainServiceRequired() {
    return this.app.app_type === AppTypes.CITY_APP;
  }

  submit(form: NgForm) {
    if (form.invalid) {
      return;
    }
    const payload: PatchAppPayload = {
      title: this.app.title,
      app_type: this.app.app_type,
      main_service: this.app.main_service,
      playstore_track: this.app.playstore_track,
      secure: this.rogerthatApp.secure,
      facebook_registration: this.app.facebook_registration,
      facebook_app_id: this.rogerthatApp.facebook_app_id,
      facebook_app_secret: this.rogerthatApp.facebook_app_secret,
      chat_payments_enabled: this.app.chat_payments_enabled,
    };
    this.save.emit(payload);
  }

  updateFacebook() {
    this.store.dispatch(new UpdateFacebookAction());
  }

  requestFacebookReview() {
    this.store.dispatch(new RequestFacebookReviewAction());
  }
}
