import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Store } from '@ngrx/store';
import { Observable, Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { ClearAppResourceAction, CreateAppAssetAction } from '../../../actions';
import { getAppAssetsStatus } from '../../../console.state';
import { App, EditAppAssetPayload } from '../../../interfaces';

@Component({
  selector: 'rcc-create-app-resource',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <rcc-app-resource [asset]="asset"
                      [status]="status$ | async"
                      [edit]="false"
                      [allowCreateDefault]="false"
                      (save)="submit($event)"></rcc-app-resource>`,
})
export class CreateAppResourceComponent implements OnInit, OnDestroy {
  app: App;
  asset: EditAppAssetPayload;
  file: any;
  status$: Observable<ApiRequestStatus>;
  private subscription: Subscription;

  constructor(private store: Store,
              private router: Router,
              private route: ActivatedRoute) {
  }

  public ngOnInit(): void {
    this.asset = {
      id: '',
      kind: 'ChatBackgroundImage',
      app_ids: [],
      content_type: '',
      file: null,
      is_default: false,
      url: '',
      scale_x: 1.0,
    };
    this.store.dispatch(new ClearAppResourceAction());
    this.status$ = this.store.select(getAppAssetsStatus);
    this.subscription = this.status$.pipe(filter((s: ApiRequestStatus) => s.success))
      .subscribe(() => this.router.navigate([ '../' ], { relativeTo: this.route }));
  }

  ngOnDestroy() {
    this.subscription.unsubscribe();
  }

  submit(asset: EditAppAssetPayload) {
    this.store.dispatch(new CreateAppAssetAction(asset));
  }
}
