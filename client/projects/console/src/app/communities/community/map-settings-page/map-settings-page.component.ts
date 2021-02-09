import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { FormArray, FormBuilder, Validators } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { ActivatedRoute } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { IFormBuilder, IFormGroup } from '@rxweb/types';
import { Observable, Subject } from 'rxjs';
import { map, takeUntil } from 'rxjs/operators';
import { AlertDialogComponent, AlertDialogData } from '../../../../../framework/client/dialog';
import { getCommunity, getCommunityMapSettings, isMapSettingsLoading } from '../../communities.selectors';
import { getMapSettings, updateMapSettings } from '../../community.actions';
import { CommunityMapSettings, MapButton, MapLayers, MapLayerSettings, ReportsMapFilter } from '../communities';

@Component({
  selector: 'rcc-map-settings-page',
  templateUrl: './map-settings-page.component.html',
  styleUrls: ['./map-settings-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MapSettingsPageComponent implements OnInit, OnDestroy {
  communityId: number;
  formGroup: IFormGroup<CommunityMapSettings>;
  fb: IFormBuilder;
  countryCode$: Observable<string | null>;
  loading$: Observable<boolean>;
  layers: { id: keyof MapLayers, name: string }[] = [
    { id: 'gipod', name: 'Gipod' },
    { id: 'poi', name: 'Point of interest' },
    { id: 'reports', name: 'Reports' },
    { id: 'services', name: 'Services' },
  ];
  possibleFilters: { [key in keyof MapLayers]: { value: string; label: string }[] } = {
    reports: [
      { value: ReportsMapFilter.ALL, label: 'All' },
      { value: ReportsMapFilter.NEW, label: 'New' },
      { value: ReportsMapFilter.IN_PROGRESS, label: 'In progress' },
      { value: ReportsMapFilter.RESOLVED, label: 'Resolved' },
    ],
    gipod: [],
    poi: [],
    services: [],
  };
  private destroyed$ = new Subject();

  constructor(private store: Store,
              formBuilder: FormBuilder,
              private matDialog: MatDialog,
              private route: ActivatedRoute) {
    const fb = formBuilder as IFormBuilder;
    this.fb = fb;
    this.countryCode$ = this.store.pipe(select(getCommunity), map(community => community?.country ?? null));
    this.formGroup = fb.group<CommunityMapSettings>({
      center: fb.group({
        lat: fb.control(null, Validators.required),
        lon: fb.control(null, Validators.required),
      }),
      distance: fb.control(5000, Validators.required),
      layers: fb.group<MapLayers>({
        gipod: this.getLayerGroup(),
        poi: this.getLayerGroup(),
        reports: this.getLayerGroup(),
        services: this.getLayerGroup(),
      }),
    });
    this.communityId = parseInt(route.snapshot.parent!.params.communityId, 10);
  }

  get layersForm() {
    return this.formGroup.controls.layers as IFormGroup<MapLayers>;
  }

  ngOnInit(): void {
    this.store.dispatch(getMapSettings({ communityId: this.communityId }));
    this.store.pipe(select(getCommunityMapSettings), takeUntil(this.destroyed$)).subscribe(result => {
      if (result) {
        for (const layer of this.layers) {
          const buttonsForm = (this.getLayerForm(layer.id).controls.buttons as FormArray);
          buttonsForm.clear();
          for (const button of result.layers[ layer.id ].buttons) {
            buttonsForm.push(this.getButtonForm());
          }
        }
        this.formGroup.patchValue({ ...result, center: result.center ?? { lat: 50.8503396, lon: 4.3517103 } }, { emitEvent: false });
      }
    });
    this.loading$ = this.store.pipe(select(isMapSettingsLoading));
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  getLayerForm(id: keyof MapLayers) {
    return this.layersForm.controls[ id ] as IFormGroup<MapLayerSettings>;
  }

  removeButton(id: keyof MapLayers, index: number) {
    (this.getLayerForm(id).controls.buttons as FormArray).removeAt(index);
  }

  addButton(id: keyof MapLayers) {
    (this.getLayerForm(id).controls.buttons as FormArray).push(this.getButtonForm());
  }

  saveSettings() {
    if (this.formGroup.valid) {
      this.store.dispatch(updateMapSettings({ communityId: this.communityId, data: this.formGroup.value! }));
    } else {
      this.matDialog.open<AlertDialogComponent, AlertDialogData>(AlertDialogComponent, {
        data: {
          ok: 'Ok',
          title: 'Error',
          message: 'Please fill in all required fields',
        },
      });
    }
  }

  private getLayerGroup() {
    return this.fb.group<MapLayerSettings>({
      buttons: this.fb.array([]),
      default_filter: this.fb.control(null),
      filters: this.fb.control([]),
    });
  }

  private getButtonForm() {
    return this.fb.group<MapButton>({
      action: this.fb.control(null, Validators.required),
      color: this.fb.control(null),
      icon: this.fb.control(null),
      text: this.fb.control(null),
      service: this.fb.control(null),
    });
  }
}
