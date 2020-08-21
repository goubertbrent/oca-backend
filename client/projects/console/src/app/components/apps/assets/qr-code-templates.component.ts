import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { Observable, Subscription } from 'rxjs';
import { first } from 'rxjs/operators';
import { filterNull } from '../../../ngrx';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import * as actions from '../../../actions/index';
import { getApp, getQrCodeTemplates, getQrCodeTemplateStatus } from '../../../console.state';
import { App, QrCodeTemplate } from '../../../interfaces';

@Component({
  selector: 'rcc-app-qr-code-templates',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'qr-code-templates.component.html',
})
export class QrCodeTemplatesComponent implements OnInit, OnDestroy {
  app$: Observable<App>;
  qrCodeTemplates$: Observable<QrCodeTemplate[]>;
  status$: Observable<ApiRequestStatus>;
  private subscription: Subscription;

  constructor(protected store: Store) {
  }

  public ngOnInit(): void {
    this.app$ = this.store.select(getApp).pipe(filterNull());
    this.subscription = this.app$.subscribe(app => this.store.dispatch(new actions.GetQrCodeTemplatesAction({ appId: app.app_id })));
    this.qrCodeTemplates$ = this.store.select(getQrCodeTemplates);
    this.status$ = this.store.select(getQrCodeTemplateStatus);
  }

  ngOnDestroy() {
    this.subscription.unsubscribe();
  }

  public removeTemplate(template: QrCodeTemplate) {
    this.app$.pipe(first()).subscribe(app => {
      const payload = {
        appId: app.app_id,
        backendId: app.backend_server,
        data: template,
      };
      this.store.dispatch(new actions.RemoveQrCodeTemplateAction(payload));
    });
  }
}
