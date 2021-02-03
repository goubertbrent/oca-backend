import { ChangeDetectionStrategy, ChangeDetectorRef, Component, EventEmitter, Input, OnDestroy, OnInit, Output } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MapCircle } from '@angular/google-maps';
import { ActivatedRoute } from '@angular/router';
import { LatLonTO } from '@oca/web-shared';
import { Observable, Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged, takeUntil } from 'rxjs/operators';
import { GoogleMapsApiService } from '../../../../../../../src/app/shared/maps/google-maps-api.service';
import { GoogleMapsLoaderService } from '../../../shared/google-maps-loader.service';

@Component({
  selector: 'rcc-geo-location-form',
  templateUrl: './geo-location-form.component.html',
  styleUrls: ['./geo-location-form.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class GeoLocationFormComponent implements OnInit, OnDestroy {
  @Input() country: string | null;
  @Input() radius: number | null;
  searchControl = new FormControl(null);
  mapLoaded$: Observable<boolean>;
  mapPosition: google.maps.LatLngLiteral | google.maps.LatLng = { lat: 50.8503396, lng: 4.3517103 };
  circleOptions: google.maps.CircleOptions = { draggable: true, editable: true };
  @Output() centerChanged = new EventEmitter<LatLonTO>();
  @Output() radiusChanged = new EventEmitter<number>();
  private destroyed$ = new Subject();

  constructor(private activatedRoute: ActivatedRoute,
              private mapsApiLoader: GoogleMapsLoaderService,
              private changeDetectionRef: ChangeDetectorRef,
              private gmapsApis: GoogleMapsApiService) {
    this.mapLoaded$ = this.mapsApiLoader.loadApi().asObservable();
  }

  @Input() set center(value: LatLonTO | null) {
    if (value && value.lat && value.lon) {
      this.mapPosition = { lat: value.lat, lng: value.lon };
    }
  }

  ngOnInit(): void {
    this.searchControl.valueChanges.pipe(distinctUntilChanged(), debounceTime(400), takeUntil(this.destroyed$)).subscribe(async v => {
      if (!(v?.trim())) {
        return;
      }
      const result = await this.gmapsApis.geocode({ address: v, region: this.country ?? undefined });
      if (result) {
        const geo = result.geometry;
        const bounds = geo.bounds ?? geo.viewport;
        const distance = google.maps.geometry.spherical.computeDistanceBetween(bounds.getNorthEast(), bounds.getSouthWest());
        this.mapPosition = geo.location;
        this.centerChanged.emit({ lat: geo.location.lat(), lon: geo.location.lng() });
        this.radiusChanged.emit(distance);
        this.changeDetectionRef.markForCheck();
      }
    });
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  changeGeometry(circle: MapCircle | undefined) {
    if (!circle) {
      return;
    }
    const center = circle.getCenter();
    this.centerChanged.emit({ lat: center.lat(), lon: center.lng() });
  }

  changeRadius(circle: MapCircle) {
    this.radiusChanged.emit(Math.round(circle.getRadius()));
  }

}
