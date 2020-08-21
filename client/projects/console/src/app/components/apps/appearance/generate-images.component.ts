import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { Observable, Subscription } from 'rxjs';
import { first, withLatestFrom } from 'rxjs/operators';
import { filterNull } from '../../../ngrx';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import {
  CreateDefaultQrCodeTemplateAction,
  GenerateAppImagesAction,
  GetAppImagesAction,
  GetQrCodeTemplatesAction,
} from '../../../actions';
import { getApp, getAppImages, getAppImagesStatus, getGenerateAppImagesStatus, getQrCodeTemplates } from '../../../console.state';
import { App, AppImageInfo, GenerateImagesPayload } from '../../../interfaces';
import { FileSelector } from '../../../util';

@Component({
  selector: 'rcc-appeance-generate-images',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <rcc-appearance-generate-images-form [imagesInfo]="imagesInfo$ | async"
                                         [status]="status$ | async"
                                         [generateStatus]="generateStatus$ | async"
                                         (generate)="submit($event)">
    </rcc-appearance-generate-images-form>`,
})
export class AppearanceGenerateImagesComponent extends FileSelector implements OnInit, OnDestroy {
  imagesInfo$: Observable<AppImageInfo[]>;
  status$: Observable<ApiRequestStatus>;
  generateStatus$: Observable<ApiRequestStatus>;
  app$: Observable<App>;
  private _sub: Subscription;

  constructor(private store: Store,
              private router: Router,
              private route: ActivatedRoute) {
    super();
  }

  ngOnInit() {
    this.store.dispatch(new GetAppImagesAction());
    this.app$ = this.store.pipe(select(getApp), filterNull());
    this._sub = this.app$.pipe(first()).subscribe(app => this.store.dispatch(new GetQrCodeTemplatesAction({ appId: app.app_id })));
    this.imagesInfo$ = this.store.select(getAppImages);
    this.status$ = this.store.select(getAppImagesStatus);
    this.generateStatus$ = this.store.select(getGenerateAppImagesStatus);
    this.generateStatus$.subscribe(status => {
      if (status.success) {
        this.router.navigate(['../'], {
          relativeTo: this.route,
          queryParams: {
            reloadImage: true,
          },
        });
      }
    });
  }

  ngOnDestroy() {
    this._sub.unsubscribe();
  }

  createDefaultQrTemplate(imageFile: File) {
    this.readFile(imageFile);
  }

  onReadCompleted(data: string) {
    this.app$.pipe(
      withLatestFrom(this.store.select(getQrCodeTemplates)),
      first(),
    ).subscribe(([app, templates]) => {
      // create the default qr template if there's not any
      if (!templates.some(template => template.is_default)) {
        this.store.dispatch(new CreateDefaultQrCodeTemplateAction({ appId: app.app_id, data }));
      }
    });
  }

  submit(payload: GenerateImagesPayload) {
    this.store.dispatch(new GenerateAppImagesAction(payload));
    this.createDefaultQrTemplate(payload.file);
  }

}
