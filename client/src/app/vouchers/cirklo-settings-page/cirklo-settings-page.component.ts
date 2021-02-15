import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { FormBuilder, FormControl, Validators } from '@angular/forms';
import { MatDialog, MatDialogConfig } from '@angular/material/dialog';
import { MatSlideToggle, MatSlideToggleChange } from '@angular/material/slide-toggle';
import { select, Store } from '@ngrx/store';
import { MediaType, SimpleDialogComponent, SimpleDialogData, SimpleDialogResult } from '@oca/web-shared';
import { IFormArray, IFormBuilder, IFormGroup } from '@rxweb/types';
import { Observable, Subject } from 'rxjs';
import { takeUntil, withLatestFrom } from 'rxjs/operators';
import { UploadedFileResult, UploadFileDialogComponent, UploadFileDialogConfig } from '../../shared/upload-file';
import { LanguagePickerDialogComponent } from '../language-picker-dialog/language-picker-dialog.component';
import {
  CirkloAppInfo,
  CirkloAppInfoButton,
  CirkloButton,
  CirkloCity,
  CirkloSettings,
  SignupLanguageProperty,
  SignupMails,
} from '../vouchers';
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
  fb: IFormBuilder;

  constructor(private store: Store,
              private matDialog: MatDialog,
              private changeDetectorRef: ChangeDetectorRef,
              formBuilder: FormBuilder) {
    const fb = formBuilder as IFormBuilder;
    this.fb = fb;
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
      app_info: fb.group<CirkloAppInfo>({
        enabled: fb.control(false),
        title: fb.group({}),
        buttons: fb.array<CirkloAppInfoButton>([]),
      }),
    });
  }

  get appInfoForm() {
    return this.formGroup.controls.app_info as IFormGroup<CirkloAppInfo>;
  }

  get buttonsArray() {
    return this.appInfoForm.controls.buttons as IFormArray<CirkloButton>;
  }

  ngOnInit(): void {
    this.store.dispatch(GetCirkloSettingsAction());
    this.cirkloCities$ = this.store.pipe(select(getCirkloCities));
    this.cirkloSettingsLoading$ = this.store.pipe(select(areCirkloSettingsLoading));
    this.store.pipe(select(getCirkloSettings)).subscribe(settings => {
      let staging = false;
      if (settings) {
        staging = settings.city_id?.startsWith('staging-') ?? false;
        this.createAppInfoForm(settings.app_info);
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
      const url = result?.url;
      if (url) {
        this.formGroup.controls.logo_url.setValue(url);
        this.changeDetectorRef.markForCheck();
      }
    });
  }

  changeSignupLogo() {
    this.getImage().afterClosed().subscribe(result => {
      const url = result?.url;
      if (url) {
        this.formGroup.controls.signup_logo_url.setValue(url);
        this.changeDetectorRef.markForCheck();
      }
    });
  }

  private getImage() {
    const config: MatDialogConfig<UploadFileDialogConfig> = {
      data: {
        mediaType: MediaType.IMAGE,
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

  addLanguageForm(formGroup: IFormGroup<{ [ key: string ]: string }>) {
    this.matDialog.open<LanguagePickerDialogComponent, unknown, string>(LanguagePickerDialogComponent)
      .afterClosed()
      .subscribe(newLanguage => {
        if (newLanguage) {
          const ogValue = formGroup.value!;
          const languages = new Set(Object.keys(formGroup.controls));
          languages.add(newLanguage);
          this.createTranslationFormControls(Array.from(languages), formGroup);
          formGroup.patchValue(ogValue);
          this.changeDetectorRef.markForCheck();
        }
      });
  }

  changeStaging($event: MatSlideToggleChange) {
    this.store.dispatch(GetCirkloCities({ staging: $event.checked }));
    this.formGroup.controls.city_id.setValue(null);
  }

  addAppInfoButton() {
    const btn = this.createInfoButtonForm({
      url: 'https://cirklo-light.com',
      labels: { en: 'Buy voucher', nl: 'Bon kopen', fr: 'Acheter coupon' },
    });
    this.buttonsArray.push(btn);
  }

  removeLanguage(formGroup: IFormGroup<{ [ key: string ]: string }>, language: string) {
    if (language === 'en') {
      this.matDialog.open<SimpleDialogComponent, SimpleDialogData>(SimpleDialogComponent, {
        data: {
          title: 'Error',
          message: 'The English translation cannot be removed.',
          ok: 'Ok',
        },
      });
    } else {
      formGroup.removeControl(language);
    }
  }

  private createTranslationFormControls(keys: string[], formGroup: IFormGroup<{ [ key: string ]: string }>) {
    for (const key in formGroup.controls) {
      if (!(key in keys)) {
        formGroup.removeControl(key);
      }
    }
    for (const key of keys) {
      if (!(key in formGroup.controls)) {
        formGroup.addControl(key, new FormControl(null, Validators.required));
      }
    }
  }

  private createAppInfoForm(appInfo: CirkloAppInfo) {
    const titleGroup = this.appInfoForm.controls.title as IFormGroup<{ [ key: string ]: string }>;
    this.createTranslationFormControls(Object.keys(appInfo.title), titleGroup);
    this.buttonsArray.clear();
    for (const button of appInfo.buttons) {
      this.buttonsArray.push(this.createInfoButtonForm(button));
    }
  }

  private createInfoButtonForm(button: CirkloAppInfoButton) {
    const labels = this.fb.group<{ [ key: string ]: string }>({});
    const group = this.fb.group<CirkloAppInfoButton>({
      url: this.fb.control(button.url),
      labels,
    });
    this.createTranslationFormControls(Object.keys(button.labels), labels);
    return group;
  }

  removeButton(index: number) {
    const btn = this.buttonsArray.at(index);
    const url = btn.value!.url;
    this.matDialog.open<SimpleDialogComponent, SimpleDialogData, SimpleDialogResult>(SimpleDialogComponent, {
      data: {
        title: 'Confirm deletion',
        message: `Delete button ${url}?`,
        ok: 'Yes',
        cancel: 'Cancel',
      },
    }).afterClosed().subscribe(result => {
      if (result?.submitted) {
        this.buttonsArray.removeAt(index);
        this.changeDetectorRef.markForCheck();
      }
    });
  }
}
