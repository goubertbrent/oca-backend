import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnDestroy, OnInit } from '@angular/core';
import { FormBuilder, FormControl, Validators } from '@angular/forms';
import { MapCircle } from '@angular/google-maps';
import { ActivatedRoute } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { CommunityGeoFence, CommunityLocation, GeoFenceGeometry, LatLonTO } from '@oca/web-shared';
import { IFormBuilder, IFormGroup } from '@rxweb/types';
import { Observable, Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { GoogleMapsApiService } from '../../../../../../../src/app/shared/maps/google-maps-api.service';
import { GoogleMapsLoaderService } from '../../../shared/google-maps-loader.service';
import { getCurrentGeoFence } from '../../communities.selectors';
import { getGeoFence, updateGeoFence } from '../../community.actions';

@Component({
  selector: 'rcc-geo-fence-settings-page',
  templateUrl: './geo-fence-settings-page.component.html',
  styleUrls: ['./geo-fence-settings-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class GeoFenceSettingsPageComponent implements OnInit, OnDestroy {
  communityId: number;
  formGroup: IFormGroup<CommunityGeoFence>;
  searchControl = new FormControl(null);
  mapLoaded$: Observable<boolean>;
  mapPosition: google.maps.LatLngLiteral | google.maps.LatLng | null = null;
  circleOptions: google.maps.CircleOptions = { draggable: true, editable: true, radius: 5000 };
  private formBuilder: IFormBuilder;
  private destroyed$ = new Subject();

  constructor(private activatedRoute: ActivatedRoute,
              formBuilder: FormBuilder,
              private mapsApiLoader: GoogleMapsLoaderService,
              private changeDetectionRef: ChangeDetectorRef,
              private gmapsApis: GoogleMapsApiService,
              private store: Store) {
    this.mapLoaded$ = this.mapsApiLoader.loadApi().asObservable();
    this.formBuilder = formBuilder;
    this.formGroup = this.formBuilder.group<CommunityGeoFence>({
      defaults: this.formBuilder.group<CommunityLocation>({
        locality: this.formBuilder.control(null, Validators.required),
        postal_code: this.formBuilder.control(null, Validators.required),
      }),
      country: this.formBuilder.control(null),
      geometry: this.formBuilder.group<GeoFenceGeometry>({
        center: this.formBuilder.control<LatLonTO>(null, Validators.required),
        max_distance: this.formBuilder.control(5000, Validators.required),
      }),
    });
  }

  ngOnInit(): void {
    this.communityId = parseInt(this.activatedRoute.snapshot.parent!.params.communityId, 10);
    this.store.dispatch(getGeoFence({ communityId: this.communityId }));
    this.store.pipe(select(getCurrentGeoFence)).subscribe(f => {
      if (f) {
        this.formGroup.controls.country.setValue(f.country, { emitEvent: false });
        if (f.defaults) {
          this.formGroup.controls.defaults.setValue(f.defaults, { emitEvent: false });
        }
        if (f.geometry) {
          this.formGroup.controls.geometry.setValue(f.geometry, { emitEvent: false });
        }
        if (f.geometry?.center) {
          this.mapPosition = { lat: f.geometry.center.lat, lng: f.geometry.center.lon };
        } else {
          this.mapPosition = { lat: 50.845504, lng: 4.3549077 };
        }
        this.changeDetectionRef.markForCheck();
      }
    });
    this.searchControl.valueChanges.pipe(distinctUntilChanged(), debounceTime(400)).subscribe(async v => {
      if (!(v?.trim())) {
        return;
      }
      const country = this.formGroup.controls.country.value || undefined;
      const result = await this.gmapsApis.geocode({ address: v, region: country });
      if (result) {
        const geo = result.geometry;
        const bounds = geo.bounds ?? geo.viewport;
        const distance = google.maps.geometry.spherical.computeDistanceBetween(bounds.getNorthEast(), bounds.getSouthWest());
        this.formGroup.controls.geometry.setValue({ center: { lat: geo.location.lat(), lon: geo.location.lng() }, max_distance: distance });
        this.mapPosition = geo.location;
        this.changeDetectionRef.markForCheck();
      }
    });
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  save() {
    if (this.formGroup.valid) {
      this.store.dispatch(updateGeoFence({ communityId: this.communityId, data: this.formGroup.value! }));
    }
  }

  changeGeometry(circle: MapCircle | undefined) {
    if (!circle) {
      return;
    }
    const center = circle.getCenter();
    const v = {
      center: { lat: center.lat(), lon: center.lng() },
    };
    (this.formGroup.controls.geometry as IFormGroup<GeoFenceGeometry>).patchValue(v);
  }

  changeRadius(circle: MapCircle) {
    if (circle) {
      (this.formGroup.controls.geometry as IFormGroup<GeoFenceGeometry>).patchValue({ max_distance: Math.round(circle.getRadius()) });
    }
  }
}
