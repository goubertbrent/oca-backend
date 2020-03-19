import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { NgForm } from '@angular/forms';
import { MatChipInputEvent } from '@angular/material/chips';
import { MatDialog, MatDialogConfig } from '@angular/material/dialog';
import { MatSlideToggleChange } from '@angular/material/slide-toggle';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { combineLatest, Observable, Subject } from 'rxjs';
import { debounceTime, map, takeUntil } from 'rxjs/operators';
import { DEFAULT_AVATAR_URL, DEFAULT_LOGO_URL } from '../../../consts';
import { AvailablePlaceType, BrandingSettings } from '../../../shared/interfaces/oca';
import { GetBrandingSettingsAction, UpdateAvatarAction, UpdateLogoAction } from '../../../shared/shared.actions';
import { getBrandingSettings, isBrandingSettingsLoading } from '../../../shared/shared.state';
import { UploadedFileResult, UploadFileDialogComponent, UploadFileDialogConfig } from '../../../shared/upload-file';
import { deepCopy, filterNull } from '../../../shared/util';
import { GetAvailablePlaceTypesAction, GetServiceInfoAction, UpdateServiceInfoAction } from '../../settings.actions';
import { getAvailablePlaceTypes, getServiceInfo, isPlaceTypesLoading, isServiceInfoLoading, SettingsState } from '../../settings.state';
import { CURRENCIES, TIMEZONES } from '../constants';
import { MapServiceMediaItem, ServiceInfo, ServiceInfoSyncProvider, SyncedFields, SyncedNameValue } from '../service-info';

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
  @ViewChild('form') form: NgForm;
  loading$: Observable<boolean>;
  brandingSettings$: Observable<BrandingSettings>;
  timezones = TIMEZONES;
  currencies = CURRENCIES;
  DEFAULT_AVATAR_URL = DEFAULT_AVATAR_URL;
  DEFAULT_LOGO_URL = DEFAULT_LOGO_URL;
  placeTypes$: Observable<AvailablePlaceType[]>;
  serviceInfo: ServiceInfo | null = null;
  syncedValues: { [T in SyncedFields]: ServiceInfoSyncProvider | null } = DEFAULT_SYNCED_VALUES;
  submitted = false;

  private destroyed$ = new Subject();
  private autoSave$ = new Subject();

  constructor(private store: Store<SettingsState>,
              private translate: TranslateService,
              private matDialog: MatDialog,
              private changeDetectorRef: ChangeDetectorRef) {
  }

  ngOnInit() {
    this.store.dispatch(new GetServiceInfoAction());
    this.store.dispatch(new GetBrandingSettingsAction());
    this.store.dispatch(new GetAvailablePlaceTypesAction());
    this.store.pipe(select(getServiceInfo), takeUntil(this.destroyed$)).subscribe(serviceInfo => {
      this.serviceInfo = serviceInfo ? deepCopy(serviceInfo) : serviceInfo;
      if (serviceInfo) {
        const newSyncedValues: { [T in SyncedFields]: ServiceInfoSyncProvider | null } = { ...DEFAULT_SYNCED_VALUES };
        for (const field of serviceInfo.synced_fields) {
          newSyncedValues[ field.key ] = field.provider;
        }
        this.syncedValues = newSyncedValues;
      }
      this.changeDetectorRef.markForCheck();
    });
    this.brandingSettings$ = this.store.pipe(select(getBrandingSettings), filterNull());
    this.loading$ = combineLatest([
      this.store.pipe(select(isServiceInfoLoading)),
      this.store.pipe(select(isBrandingSettingsLoading)),
      this.store.pipe(select(isPlaceTypesLoading)),
    ]).pipe(map(results => results.some(r => r)));
    this.placeTypes$ = this.store.pipe(select(getAvailablePlaceTypes));
    this.autoSave$.pipe(debounceTime(2000), takeUntil(this.destroyed$)).subscribe(() => this.save());
  }

  ngOnDestroy(): void {
    this.destroyed$.next();
    this.destroyed$.complete();
    this.autoSave$.unsubscribe();
  }

  setCoverMedia($event: MapServiceMediaItem[]) {
    this.serviceInfo = { ...this.serviceInfo as ServiceInfo, cover_media: $event };
    this.save();
  }

  setValues($event: SyncedNameValue[], property: 'websites' | 'phone_numbers' | 'email_addresses' | 'addresses') {
    this.serviceInfo = { ...this.serviceInfo as ServiceInfo, [ property ]: $event };
    this.save();
  }

  autoSave() {
    this.autoSave$.next();
  }

  save() {
    if (this.form.valid) {
      this.submitted = false;
      this.store.dispatch(new UpdateServiceInfoAction(this.serviceInfo as ServiceInfo));
    } else {
      this.submitted = true;
      this.markFieldsAsDirty();
    }
  }

  removeKeyword(keyword: string) {
    const serviceInfo = this.serviceInfo as ServiceInfo;
    this.serviceInfo = { ...serviceInfo, keywords: serviceInfo.keywords.filter(k => k !== keyword) };
    this.autoSave();
  }

  addKeyword($event: MatChipInputEvent) {
    const value = $event.value.trim();
    const serviceInfo = this.serviceInfo as ServiceInfo;
    if (value && !serviceInfo.keywords.includes(value)) {
      this.serviceInfo = { ...serviceInfo, keywords: [...serviceInfo.keywords, value] };
    }
    $event.input.value = '';
    this.autoSave();
  }

  updateAvatar() {
    const dialog = this.updateImage(150, 150, '/common/settings/avatar', {
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
    });
    dialog.afterClosed().subscribe((result: UploadedFileResult | null) => {
      if (result) {
        this.store.dispatch(new UpdateLogoAction({ logo_url: result.getUrl() }));
      }
    });
  }

  updateImage(width: number, height: number, uploadUrl: string, partialConfig: Pick<UploadFileDialogConfig, 'title' | 'uploadPrefix' | 'listPrefix' | 'gallery'>) {
    const config: MatDialogConfig<UploadFileDialogConfig> = {
      data: {
        cropOptions: {
          viewMode: 0,
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
    return this.matDialog.open(UploadFileDialogComponent, config);
  }

  setVisibility($event: MatSlideToggleChange) {
    this.serviceInfo = { ...this.serviceInfo as ServiceInfo, visible: $event.checked };
    this.save();
  }

  mainPlaceTypeChanged(mainPlaceType: string) {
    const info = this.serviceInfo as ServiceInfo;
    const placeTypes = info.place_types;
    if (!info.place_types.includes(mainPlaceType)) {
      this.serviceInfo = { ...info, main_place_type: mainPlaceType, place_types: [mainPlaceType, ...placeTypes] };
    }
    this.autoSave();
  }

  private markFieldsAsDirty() {
    for (const control of Object.values(this.form.controls)) {
      if (!control.valid) {
        control.markAsTouched();
        control.markAsDirty();
        control.updateValueAndValidity();
      }
    }
  }
}
