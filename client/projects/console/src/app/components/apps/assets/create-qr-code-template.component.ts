import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Store } from '@ngrx/store';
import { Observable, Subscription } from 'rxjs';
import { first } from 'rxjs/operators';
import { filterNull } from '../../../ngrx';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import * as actions from '../../../actions/index';
import { getApp, getCreateQrCodeTemplateStatus, getQrCodeTemplateStatus } from '../../../console.state';
import { App, QrCodeTemplate } from '../../../interfaces';

@Component({
  selector: 'rcc-create-qr-code-template',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="default-component-margin">
      <rcc-qr-code-template
        [status]="qrCodeStatus$ | async"
        [createStatus]="qrCreateStatus$ | async"
        (create)="addTemplate($event)"></rcc-qr-code-template>
    </div>`,
})
export class CreateQrCodeTemplateComponent implements OnInit, OnDestroy {
  app$: Observable<App>;
  qrCodeStatus$: Observable<ApiRequestStatus>;
  qrCreateStatus$: Observable<ApiRequestStatus>;

  private qrSubscription: Subscription;

  constructor(private store: Store,
              private router: Router,
              private route: ActivatedRoute) {
  }

  public ngOnInit(): void {
    this.qrCodeStatus$ = this.store.select(getQrCodeTemplateStatus);
    this.qrCreateStatus$ = this.store.select(getCreateQrCodeTemplateStatus);
    this.app$ = this.store.select(getApp).pipe(filterNull());
    this.qrSubscription = this.qrCreateStatus$.subscribe((result: ApiRequestStatus) => {
      if (result.success) {
        this.router.navigate([`..`], { relativeTo: this.route });
      }
    });
  }

  ngOnDestroy() {
    this.qrSubscription.unsubscribe();
  }

  public addTemplate(template: QrCodeTemplate) {
    this.app$.pipe(first()).subscribe(app => {
      this.store.dispatch(new actions.AddQrCodeTemplateAction({ appId: app.app_id, data: template }));
    });
  }
}
