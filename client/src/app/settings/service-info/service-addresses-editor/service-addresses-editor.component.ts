import { LatLngBounds, LatLngBoundsLiteral } from '@agm/core';
import { CdkDragDrop, moveItemInArray } from '@angular/cdk/drag-drop';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  EventEmitter,
  Input,
  OnDestroy,
  OnInit,
  Output,
  ViewChild,
} from '@angular/core';
import { NgModel } from '@angular/forms';
import { MatDialog, MatDialogConfig } from '@angular/material/dialog';
import { TranslateService } from '@ngx-translate/core';
import { ReplaySubject, Subject, Subscription } from 'rxjs';
import { debounceTime, distinctUntilChanged, take } from 'rxjs/operators';
import { SimpleDialogComponent, SimpleDialogData } from '../../../shared/dialog/simple-dialog.component';
import { ServiceAddress } from '../service-info';

const GOOGLE_PLACE_FIELDS = ['formatted_address', 'geometry', 'name', 'place_id', 'types'];

@Component({
  selector: 'oca-service-addresses-editor',
  templateUrl: './service-addresses-editor.component.html',
  styleUrls: ['./service-addresses-editor.component.scss',
    '../service-synced-value-editor/service-synced-value-editor.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ServiceAddressesEditorComponent implements OnInit, OnDestroy {
  @ViewChild('inputFieldModel') inputFieldModel: NgModel;
  @Input() values: ServiceAddress[];
  @Input() maxCount = 1;
  @Output() valueChanged = new EventEmitter<ServiceAddress[]>();
  editingIndex: number | null = null;
  editingValue: ServiceAddress | null = null;
  mapBounds: LatLngBounds | LatLngBoundsLiteral | boolean = true;
  NEW_ITEM_INDEX = -1;
  syncedMessage: string;

  resolvePlace$ = new Subject();
  inputChanged$ = new Subject<{ name: string | null, address: string | null }>();
  googleMapsResults$ = new Subject<google.maps.places.PlaceResult[]>();
  map = new ReplaySubject<any>();
  private subscriptions: Subscription[] = [];

  constructor(private translate: TranslateService,
              private changeDetectorRef: ChangeDetectorRef,
              private matDialog: MatDialog) {
  }

  ngOnInit(): void {
    this.syncedMessage = this.translate.instant('oca.value_synced_via_paddle_cannot_edit');
    this.subscriptions = [
      this.inputChanged$.pipe(
        debounceTime(600),
        distinctUntilChanged((prev, curr) => prev.name === curr.name && prev.address === curr.address),
      ).subscribe(() => this.geocode()),
      this.resolvePlace$.subscribe(() => this.geocodePlace()),
    ];
  }

  ngOnDestroy(): void {
    for (const s of this.subscriptions) {
      s.unsubscribe();
    }
  }

  changed() {
    this.valueChanged.emit(this.values);
  }

  removeValue(value: ServiceAddress) {
    this.values = this.values.filter(v => v !== value);
    this.changed();
  }

  saveAddress() {
    if (!this.editingValue || !(this.editingValue.value || '').trim()) {
      const control = this.inputFieldModel.control;
      control.markAsTouched();
      control.markAsDirty();
      control.updateValueAndValidity();
      return;
    }
    if (this.editingValue.coordinates === null) {
      const config: MatDialogConfig<SimpleDialogData> = {
        data: {
          title: this.translate.instant('oca.Error'),
          message: this.translate.instant('oca.could_not_resolve_address'),
          ok: this.translate.instant('oca.ok'),
        },
      };
      this.matDialog.open(SimpleDialogComponent, config);
      return;
    }
    if (this.editingIndex === this.NEW_ITEM_INDEX) {
      this.values.push(this.editingValue);
    } else {
      this.values[ this.editingIndex as number ] = this.editingValue;
    }
    this.editingIndex = null;
    this.editingValue = null;
    this.changed();
  }

  addValue() {
    this.editValue({ value: '', name: null, coordinates: null, google_maps_place_id: null });
  }

  editValue(value: ServiceAddress) {
    this.editingValue = { ...value };
    this.editingIndex = this.values.indexOf(value);
    this.googleMapsResults$.next([]);
    this.resolvePlace$.next();
  }

  itemMoved($event: CdkDragDrop<any>) {
    moveItemInArray(this.values, $event.previousIndex, $event.currentIndex);
  }

  nameChanged(name: string | google.maps.places.PlaceResult) {
    if (typeof name !== 'string') {
      return;
    }
    const val = this.editingValue as ServiceAddress;
    this.googleMapsResults$.next([]);
    this.editingValue = { ...val, name };
    this.inputChanged$.next({ name, address: val.value });
  }

  onMapReady($event: any) {
    this.map.next($event);
  }

  displayGoogleMapsResult(value: google.maps.places.PlaceResult | string | null) {
    if (typeof value === 'string') {
      return value;
    }
    if (value) {
      return `${value.name} - ${value.formatted_address}`;
    }
    return '';
  }

  mapsResultSelected(value: google.maps.places.PlaceResult) {
    const geometry = value.geometry as google.maps.places.PlaceGeometry;
    const coordinates = { lat: geometry.location.lat(), lon: geometry.location.lng() };
    this.editingValue = {
      ...this.editingValue as ServiceAddress,
      coordinates,
      google_maps_place_id: value.place_id,
      name: value.name,
      value: value.formatted_address as string,
    };
    this.mapBounds = geometry.viewport as LatLngBounds;
  }

  async addressValueChanged($event: string) {
    const val = this.editingValue as ServiceAddress;
    this.editingValue = { ...val, value: $event, coordinates: null, google_maps_place_id: null };
    this.inputChanged$.next({ name: val.name, address: $event });
  }

  private addressToGeometry(): Promise<google.maps.GeocoderGeometry> {
    return new Promise((resolve, reject) => {
      const geocoder = new google.maps.Geocoder();
      const { value } = this.editingValue as ServiceAddress;
      geocoder.geocode({ address: value as string }, (results, status) => {
        if (status === google.maps.GeocoderStatus.OK) {
          resolve(results[ 0 ].geometry);
        } else {
          reject(status);
        }
        this.changeDetectorRef.markForCheck();
      });
    });
  }

  private geocodePlace() {
    this.map.pipe(take(1)).subscribe(googleMap => {
      const service = new google.maps.places.PlacesService(googleMap);
      if (this.editingValue) {
        if (this.editingValue.google_maps_place_id) {
          service.getDetails({
            placeId: this.editingValue.google_maps_place_id,
            fields: GOOGLE_PLACE_FIELDS,
          }, (r, s) => this.processPlaceResult([r], s));
        } else if (this.editingValue.value || this.editingValue.name) {
          service.findPlaceFromQuery({
            query: this.editingValue.name || this.editingValue.value,
            fields: GOOGLE_PLACE_FIELDS,
          }, (r, s) => this.processPlaceResult(r, s));
        }
      }
    });
  }

  private processPlaceResult(result: google.maps.places.PlaceResult[], status: google.maps.places.PlacesServiceStatus) {
    if (status === google.maps.places.PlacesServiceStatus.OK) {
      const place = Array.isArray(result) ? result[ 0 ] : result;
      if (place.geometry) {
        this.mapBounds = place.geometry.viewport as LatLngBounds;
        this.changeDetectorRef.markForCheck();
      }
    }
  }

  private async geocode() {
    const value = this.editingValue?.name ?? '';
    if (value.length > 4) {
      this.map.pipe(take(1)).subscribe(googleMap => {
        const service = new google.maps.places.PlacesService(googleMap);
        service.textSearch({ query: value }, (results, status) => {
          if (status === google.maps.places.PlacesServiceStatus.OK) {
            let bounds = new google.maps.LatLngBounds();
            const filteredResults: google.maps.places.PlaceResult[] = [];
            for (const result of results) {
              if (result.geometry && result.formatted_address) {
                bounds = bounds.union(result.geometry.viewport);
                filteredResults.push(result);
              }
            }
            this.googleMapsResults$.next(filteredResults);
            this.mapBounds = bounds as LatLngBounds;
            this.changeDetectorRef.detectChanges();
          }
        });
      });
    } else {
      try {
        const geo = await this.addressToGeometry();
        const coordinates = { lat: geo.location.lat(), lon: geo.location.lng() };
        this.editingValue = {
          ...this.editingValue as ServiceAddress,
          coordinates,
        };
        // Bounds can be undefined
        this.mapBounds = (geo.bounds || geo.viewport) as LatLngBounds;
      } catch (err) {
        // ignore for now
      }
    }
  }
}
