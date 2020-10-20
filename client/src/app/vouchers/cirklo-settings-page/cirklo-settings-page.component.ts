import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnDestroy, OnInit } from '@angular/core';
import { FormBuilder } from '@angular/forms';
import { MatDialog, MatDialogConfig } from '@angular/material/dialog';
import { select, Store } from '@ngrx/store';
import { IFormBuilder, IFormGroup } from '@rxweb/types';
import { Observable, Subject } from 'rxjs';
import { UploadedFileResult, UploadFileDialogComponent, UploadFileDialogConfig } from '../../shared/upload-file';
import { CirkloSettings, SignupLanguageProperty, SignupMails } from '../vouchers';
import { GetCirkloSettingsAction, SaveCirkloSettingsAction } from '../vouchers.actions';
import { areCirkloSettingsLoading, getCirkloSettings } from '../vouchers.selectors';

@Component({
  selector: 'oca-cirklo-settings-page',
  templateUrl: './cirklo-settings-page.component.html',
  styleUrls: ['./cirklo-settings-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CirkloSettingsPageComponent implements OnInit, OnDestroy {
  languages = ['nl', 'fr'];
  formGroup: IFormGroup<CirkloSettings>;
  cirkloSettingsLoading$: Observable<boolean>;
  destroyed$ = new Subject();

  constructor(private store: Store,
              private matDialog: MatDialog,
              private changeDetectorRef: ChangeDetectorRef,
              formBuilder: FormBuilder) {
    const fb = formBuilder as IFormBuilder;
    this.formGroup = fb.group<CirkloSettings>({
      city_id: fb.control(null),
      logo_url: fb.control(null),
      signup_enabled: fb.control(false),
      signup_logo_url: fb.control(null),
      signup_name_nl: fb.control(null),
      signup_name_fr: fb.control(null),
      signup_mail: fb.group<SignupMails>({
        accepted: fb.group<SignupLanguageProperty>({
          nl: fb.control(null),
          fr: fb.control(null),
        }),
        denied: fb.group<SignupLanguageProperty>({
          nl: fb.control(null),
          fr: fb.control(null),
        }),
      }),
    });
  }

  ngOnInit(): void {
    this.store.dispatch(new GetCirkloSettingsAction());
    this.cirkloSettingsLoading$ = this.store.pipe(select(areCirkloSettingsLoading));
    this.store.pipe(select(getCirkloSettings)).subscribe(settings => {
      if (settings) {
        this.formGroup.setValue(settings);
      }
    });
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  save() {
    if (this.formGroup.valid) {
      this.store.dispatch(new SaveCirkloSettingsAction(this.formGroup.value!));
    }
  }

  changeLogo() {
    this.getImage().afterClosed().subscribe(result => {
      const url = result && result.getUrl();
      if (url) {
        this.formGroup.controls.logo_url.setValue(url);
        this.changeDetectorRef.markForCheck();
      }
    });
  }

  changeSignupLogo() {
    this.getImage().afterClosed().subscribe(result => {
      const url = result && result.getUrl();
      if (url) {
        this.formGroup.controls.signup_logo_url.setValue(url);
        this.changeDetectorRef.markForCheck();
      }
    });
  }

  private getImage() {
    const config: MatDialogConfig<UploadFileDialogConfig> = {
      data: {
        fileType: 'image',
        cropOptions: {
          dragMode: 'crop',
          rotatable: true,
          autoCropArea: 1.0,
          aspectRatio: 1,
        },
        croppedCanvasOptions: {
          width: 300,
          height: 300,
          imageSmoothingEnabled: true,
          imageSmoothingQuality: 'high',
        },
        accept: 'image/png',
        title: 'Set logo',
        croppedImageType: 'image/png',
        uploadPrefix: 'branding/avatar',
        listPrefix: 'branding/avatar',
        gallery: { prefix: 'avatar' },
      },
    };
    return this.matDialog.open<UploadFileDialogComponent, UploadFileDialogConfig, UploadedFileResult>(UploadFileDialogComponent, config);
  }
}
