import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, ActivatedRouteSnapshot, Router } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { Observable, Subscription } from 'rxjs';
import { first, withLatestFrom } from 'rxjs/operators';
import { filterNull } from '../../../ngrx';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { CreateDefaultQrCodeTemplateAction, GetAppImageAction, GetQrCodeTemplatesAction, UpdateAppImageAction } from '../../../actions';
import { getApp, getAppImage, getAppImageStatus, getQrCodeTemplates } from '../../../console.state';
import { App, AppImageInfo, UpdateAppImagePayload } from '../../../interfaces';
import { FileSelector } from '../../../util';


@Component({
  selector: 'rcc-appearence-edit-image',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <rcc-appearance-edit-image-form [imageInfo]="imageInfo$ | async"
                                    [appId]="appId"
                                    [status]="status$ | async"
                                    (save)="submit($event)"></rcc-appearance-edit-image-form>`,
})
export class AppearanceEditImageComponent extends FileSelector implements OnInit, OnDestroy {
  imageInfo$: Observable<AppImageInfo>;
  app$: Observable<App>;
  status$: Observable<ApiRequestStatus>;
  appId: string;

  private _sub: Subscription;

  constructor(private store: Store,
              private router: Router,
              private route: ActivatedRoute) {
    super();
  }

  ngOnInit() {
    this.store.dispatch(new GetAppImageAction(this.route.snapshot.params.imageType));
    this.imageInfo$ = this.store.pipe(select(getAppImage), filterNull());
    this.status$ = this.store.select(getAppImageStatus);
    this.appId = (<ActivatedRouteSnapshot>(<ActivatedRouteSnapshot>this.route.snapshot.parent).parent).params.appId;
    this.app$ = this.store.pipe(select(getApp), filterNull());
    this._sub = this.app$.pipe(first()).subscribe(app => this.store.dispatch(new GetQrCodeTemplatesAction({ appId: app.app_id })));
  }

  ngOnDestroy() {
    this._sub.unsubscribe();
  }

  createDefaultQrTemplate(imageFile: File) {
    this.readFile(imageFile);
  }

  onReadCompleted(data: string) {
    this.app$.pipe(withLatestFrom(this.store.select(getQrCodeTemplates)), first()).subscribe(([app, templates]) => {
      // create the default qr template if there's not any
      if (!templates.some(template => template.is_default)) {
        this.store.dispatch(new CreateDefaultQrCodeTemplateAction({ appId: app.app_id, data }));
      }
    });
  }

  submit(payload: UpdateAppImagePayload) {
    if (payload.type.endsWith('icon')) {
      this.createDefaultQrTemplate(payload.file);
    }
    this.store.dispatch(new UpdateAppImageAction({ ...payload }));
    const sub = this.status$.subscribe((status: ApiRequestStatus) => {
      if (status.success) {
        this.router.navigate(['..'], {
          relativeTo: this.route,
          queryParams: {
            reloadImage: true,
          },
        });
      }
      if (status.success || status.error) {
        sub.unsubscribe();
      }
    });
  }

}
