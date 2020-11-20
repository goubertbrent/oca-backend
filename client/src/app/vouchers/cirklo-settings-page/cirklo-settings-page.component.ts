import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { MatDialog, MatDialogConfig } from '@angular/material/dialog';
import { MatSlideToggle, MatSlideToggleChange } from '@angular/material/slide-toggle';
import { select, Store } from '@ngrx/store';
import { IFormBuilder, IFormGroup } from '@rxweb/types';
import { Observable, Subject } from 'rxjs';
import { takeUntil, withLatestFrom } from 'rxjs/operators';
import { UploadedFileResult, UploadFileDialogComponent, UploadFileDialogConfig } from '../../shared/upload-file';
import { CirkloCity, CirkloSettings, SignupLanguageProperty, SignupMails } from '../vouchers';
import { GetCirkloCities, GetCirkloSettingsAction, SaveCirkloSettingsAction } from '../vouchers.actions';
import { areCirkloSettingsLoading, getCirkloCities, getCirkloSettings } from '../vouchers.selectors';

// TODO: move this page to admin settings
@Component({
  selector: 'oca-cirklo-settings-page',
  templateUrl: './cirklo-settings-page.component.html',
  styleUrls: ['./cirklo-settings-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CirkloSettingsPageComponent implements OnInit, OnDestroy {
  @ViewChild('stagingToggle', {static: true}) stagingToggle: MatSlideToggle;
  languages = ['nl', 'fr'];
  formGroup: IFormGroup<CirkloSettings>;
  cirkloSettingsLoading$: Observable<boolean>;
  cirkloCities$: Observable<CirkloCity[]>;
  destroyed$ = new Subject();

  constructor(private store: Store,
              private matDialog: MatDialog,
              private changeDetectorRef: ChangeDetectorRef,
              formBuilder: FormBuilder) {
    const fb = formBuilder as IFormBuilder;
    this.formGroup = fb.group<CirkloSettings>({
      city_id: fb.control(null, Validators.required),
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
    this.store.dispatch(GetCirkloSettingsAction());
    this.cirkloCities$ = this.store.pipe(select(getCirkloCities));
    this.cirkloSettingsLoading$ = this.store.pipe(select(areCirkloSettingsLoading));
    this.store.pipe(select(getCirkloSettings)).subscribe(settings => {
      let staging = false;
      if (settings) {
        staging = settings.city_id?.startsWith('staging-') ?? false;
        this.formGroup.setValue(settings);
      }
      this.stagingToggle.checked = staging;
      this.store.dispatch(GetCirkloCities({ staging }));
    });
    this.formGroup.controls.city_id.valueChanges.pipe(
      takeUntil(this.destroyed$),
      withLatestFrom(this.cirkloCities$),
    ).subscribe(([cityId, cities]) => {
      if (cityId) {
        const city = cities.find(c => c.id === cityId);
        if (city) {
          this.formGroup.patchValue({
            signup_name_fr: city.nameFr,
            signup_name_nl: city.nameNl,
          });
        }
      }
    });
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  save() {
    if (this.formGroup.valid) {
      this.store.dispatch(SaveCirkloSettingsAction({ payload: this.formGroup.value! }));
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

  changeStaging($event: MatSlideToggleChange) {
    this.store.dispatch(GetCirkloCities({ staging: $event.checked }));
    this.formGroup.controls.city_id.setValue(null);
  }
}
