import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { take } from 'rxjs/operators';
import {
  apiRequestInitial,
  apiRequestLoading,
  ApiRequestStatus,
  apiRequestSuccess,
  transformErrorResponse,
} from '../../../../../framework/client/rpc';
import { getApp } from '../../../console.state';
import { App, Branding, MAX_BRANDING_SIZE } from '../../../interfaces';
import { AppsService } from '../../../services';
import { FileSelector } from '../../../util';

@Component({
  selector: 'rcc-app-assets',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'core-branding.component.html',
})
export class CoreBrandingComponent extends FileSelector implements OnInit {
  status: ApiRequestStatus;
  file: string | null;

  constructor(private store: Store,
              private appsService: AppsService,
              private cdRef: ChangeDetectorRef) {
    super();
  }

  public ngOnInit(): void {
    this.resetStatus();
  }

  save() {
    this.store.select(getApp).pipe(take(1)).subscribe(this.doUpload.bind(this));
  }

  doUpload(app: App) {
    if (!this.file) {
      return;
    }
    this.status = apiRequestLoading;
    const payload = {
      file: this.file,
    };
    // todo refactor to use @ngrx/store
    this.appsService.updateCoreBranding(app.app_id, payload)
      .toPromise().then(this.handleSuccess.bind(this), this.handleError.bind(this));
  }

  handleSuccess(branding: Branding) {
    this.status = apiRequestSuccess;
    this.file = null;
    this.cdRef.markForCheck();
  }

  handleError(response: HttpErrorResponse) {
    this.status = transformErrorResponse(response);
    this.cdRef.markForCheck();
  }

  onFileSelected(file: File) {
    this.resetStatus();
    this.file = null;
    this.readFile(file, MAX_BRANDING_SIZE);
  }

  private resetStatus() {
    this.status = apiRequestInitial;
  }

  onMaxSizeReached() {
    this.status = {
      loading: false,
      success: false,
      error: {
        error: 'file_too_large',
        status_code: 413,
        data: {
          size: MAX_BRANDING_SIZE / 1024 + ' kB',
        },
      },
    };
    this.cdRef.markForCheck();
  }

  onReadCompleted(data: string) {
    this.file = data;
    this.cdRef.markForCheck();
  }
}
