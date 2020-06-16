import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { MatChipInputEvent } from '@angular/material/chips';
import { MatDialog, MatDialogConfig } from '@angular/material/dialog';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { combineLatest, Observable, Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged, map, take, takeUntil } from 'rxjs/operators';
import { environment } from 'src/environments/environment';
import { DEFAULT_AVATAR_URL, DEFAULT_LOGO_URL } from '../../../consts';
import { AvailableOtherPlaceType, AvailablePlaceType, BrandingSettings } from '../../../shared/interfaces/oca';
import { GetBrandingSettingsAction, UpdateAvatarAction, UpdateLogoAction } from '../../../shared/shared.actions';
import { getBrandingSettings, isBrandingSettingsLoading } from '../../../shared/shared.state';
import { UploadedFileResult, UploadFileDialogComponent, UploadFileDialogConfig } from '../../../shared/upload-file';
import { filterNull, markAllControlsAsDirty } from '../../../shared/util';
import { FormControlTyped, FormGroupTyped } from '../../../shared/util/forms';
import { GetAvailablePlaceTypesAction, GetCountriesAction, GetServiceInfoAction, UpdateServiceInfoAction } from '../../settings.actions';
import {
  getAvailablePlaceTypes,
  getCountries,
  getServiceInfo,
  isPlaceTypesLoading,
  isServiceInfoLoading,
  SettingsState,
} from '../../settings.state';
import { CURRENCIES, TIMEZONES } from '../constants';
import { Country, ServiceInfo, ServiceInfoSyncProvider, SyncedFields, SyncedNameValue } from '../service-info';

const DEFAULT_SYNCED_VALUES: { [T in SyncedFields]: null } = {
  name: null,
  description: null,
  addresses: null,
  email_addresses: null,
  phone_numbers: null,
  websites: null,
};

@Component({
  selector: 'oca-service-info-page',
  templateUrl: './service-info-page.component.html',
  styleUrls: ['./service-info-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ServiceInfoPageComponent implements OnInit, OnDestroy {
  loading$: Observable<boolean>;
  brandingSettings$: Observable<BrandingSettings>;
  timezones = TIMEZONES;
  currencies = CURRENCIES;
  DEFAULT_AVATAR_URL = DEFAULT_AVATAR_URL;
  DEFAULT_LOGO_URL = DEFAULT_LOGO_URL;
  placeTypes$: Observable<AvailablePlaceType[]>;
  otherPlaceTypes$ = new Subject<AvailableOtherPlaceType[]>();
  countries$: Observable<Country[]>;
  syncedValues: { [T in SyncedFields]: ServiceInfoSyncProvider | null } = DEFAULT_SYNCED_VALUES;
  submitted = false;
  formGroup: FormGroupTyped<ServiceInfo>;
  saveErrorMessage$ = new Subject<string>();

  private destroyed$ = new Subject();

  constructor(private store: Store<SettingsState>,
              private translate: TranslateService,
              private matDialog: MatDialog,
              private fb: FormBuilder) {
    this.formGroup = fb.group({
      cover_media: fb.control([]),
      websites: fb.control([]) as FormControlTyped<SyncedNameValue[]>,
      name: fb.control('', [Validators.required, Validators.minLength(2), Validators.maxLength(50)]),
      timezone: fb.control('', Validators.required),
      phone_numbers: fb.control([]),
      email_addresses: fb.control([]),
      description: fb.control(''),
      currency: fb.control('', Validators.required),
      addresses: fb.control([]),
      keywords: fb.control([]),
      main_place_type: fb.control(null, Validators.required),
      place_types: fb.control([], Validators.required),
      synced_fields: fb.control([]),
      visible: fb.control(true),
    }) as FormGroupTyped<ServiceInfo>;

  }

  ngOnInit() {
    this.store.dispatch(new GetServiceInfoAction());
    this.store.dispatch(new GetBrandingSettingsAction());
    this.store.dispatch(new GetAvailablePlaceTypesAction());
    this.placeTypes$ = this.store.pipe(select(getAvailablePlaceTypes));
    this.placeTypes$.pipe(takeUntil(this.destroyed$)).subscribe(() => this.setOtherPlaceTypes());
    this.store.pipe(select(getServiceInfo), takeUntil(this.destroyed$)).subscribe(serviceInfo => {
      if (serviceInfo) {
        this.formGroup.setValue(serviceInfo, { emitEvent: false });
        const newSyncedValues: { [T in SyncedFields]: ServiceInfoSyncProvider | null } = { ...DEFAULT_SYNCED_VALUES };
        for (const field of serviceInfo.synced_fields) {
          newSyncedValues[ field.key ] = field.provider;
        }
        this.syncedValues = newSyncedValues;
        this.setOtherPlaceTypes();
      }
    });
    this.brandingSettings$ = this.store.pipe(select(getBrandingSettings), filterNull());
    this.loading$ = combineLatest([
      this.store.pipe(select(isServiceInfoLoading)),
      this.store.pipe(select(isBrandingSettingsLoading)),
      this.store.pipe(select(isPlaceTypesLoading)),
    ]).pipe(map(results => results.some(r => r)));
    this.loading$.pipe(distinctUntilChanged(), takeUntil(this.destroyed$)).subscribe(loading => {
      if (loading) {
        this.formGroup.disable({ emitEvent: false });
      } else {
        this.formGroup.enable({ emitEvent: false });
        if (this.formGroup.invalid) {
          this.showErrors();
        }
      }
    });
    this.countries$ = this.store.pipe(select(getCountries));

    this.formGroup.controls.main_place_type.valueChanges.pipe(
      takeUntil(this.destroyed$),
    ).subscribe(mainPlaceType => this.mainPlaceTypeChanged(mainPlaceType));
    this.formGroup.valueChanges.pipe(
      debounceTime(environment.production ? 7500 : 2000),
      takeUntil(this.destroyed$),
    ).subscribe(() => this.save());
  }

  ngOnDestroy(): void {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  save() {
    if (this.formGroup.valid) {
      this.submitted = false;
      this.store.dispatch(new UpdateServiceInfoAction(this.formGroup.value as ServiceInfo));
      this.saveErrorMessage$.next('');
    } else {
      this.submitted = true;
      this.showErrors();
    }
  }

  mainPlaceTypeChanged(mainPlaceType: string | null) {
    const placeTypes = this.formGroup.value.place_types as string[];
    if (mainPlaceType && !placeTypes.includes(mainPlaceType)) {
      this.formGroup.patchValue({ place_types: [mainPlaceType, ...placeTypes] });
    }
    this.setOtherPlaceTypes();
  }

  removeKeyword(keyword: string) {
    this.formGroup.patchValue({ keywords: this.formGroup.value.keywords.filter((k: string) => k !== keyword) });
  }

  addKeyword($event: MatChipInputEvent) {
    const value = $event.value.trim();
    const currentKeywords = this.formGroup.value.keywords;
    if (value && !currentKeywords.includes(value)) {
      this.formGroup.patchValue({ keywords: [...currentKeywords, value] });
    }
    $event.input.value = '';
  }

  updateAvatar() {
    const dialog = this.updateImage(250, 250, '/common/settings/avatar', {
      title: this.translate.instant('oca.Change logo'),
      uploadPrefix: 'branding/avatar',
      listPrefix: 'branding/avatar',
      gallery: { prefix: 'avatar' },
    });
    dialog.afterClosed().subscribe((result: UploadedFileResult | null) => {
      if (result) {
        this.store.dispatch(new UpdateAvatarAction({ avatar_url: result.getUrl() }));
      }
    });
  }

  updateLogo() {
    const dialog = this.updateImage(1440, 540, '/common/settings/logo', {
      title: this.translate.instant('oca.change_cover_photo'),
      uploadPrefix: 'branding/logo',
      listPrefix: 'branding/logo',
      gallery: { prefix: 'logo' },
      croppedImageType: 'image/jpeg',
    });
    dialog.afterClosed().subscribe((result: UploadedFileResult | null) => {
      if (result) {
        this.store.dispatch(new UpdateLogoAction({ logo_url: result.getUrl() }));
      }
    });
  }

  updateImage(width: number, height: number, uploadUrl: string,
              partialConfig: Pick<UploadFileDialogConfig, 'title' | 'uploadPrefix' | 'listPrefix' | 'gallery'| 'croppedImageType'>) {
    const config: MatDialogConfig<UploadFileDialogConfig> = {
      data: {
        cropOptions: {
          dragMode: 'crop',
          rotatable: true,
          autoCropArea: 1.0,
          aspectRatio: width / height,
        },
        croppedCanvasOptions: {
          width,
          height,
          imageSmoothingEnabled: true,
          imageSmoothingQuality: 'high',
        },
        reference: { type: 'branding_settings' },
        ...partialConfig,
      },
    };
    console.log(config);
    return this.matDialog.open(UploadFileDialogComponent, config);
  }

  private showErrors() {
    markAllControlsAsDirty(this.formGroup);
    this.saveErrorMessage$.next(this.translate.instant('oca.please_fill_in_required_fields'));
  }

  requestCountries() {
    this.countries$.pipe(take(1)).subscribe(countries => {
      if (!countries.length) {
        this.store.dispatch(new GetCountriesAction());
      }
    });
  }

  private setOtherPlaceTypes() {
    this.placeTypes$.pipe(take(1), takeUntil(this.destroyed$)).subscribe(types => {
      const mainType = this.formGroup.value.main_place_type;
      this.otherPlaceTypes$.next(types.map(p => ({ ...p, disabled: mainType === p.value })));
    });
  }

  getError() {
    console.log(this.formGroup.controls.place_types);
  }
}
