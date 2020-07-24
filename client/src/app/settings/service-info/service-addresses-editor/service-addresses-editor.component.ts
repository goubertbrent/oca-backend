import { AgmMap, LatLngBounds, LatLngBoundsLiteral } from '@agm/core';
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
import { ControlValueAccessor, FormBuilder, FormGroup, NgModel, NG_VALUE_ACCESSOR, Validators } from '@angular/forms';
import { MatDialog, MatDialogConfig } from '@angular/material/dialog';
import { TranslateService } from '@ngx-translate/core';
import { SimpleDialogComponent, SimpleDialogData } from '@oca/web-shared';
import { ReplaySubject, Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged, filter, map, skip, take, takeUntil } from 'rxjs/operators';
import { markAllControlsAsDirty } from '../../../shared/util';
import { Country, ServiceAddress } from '../service-info';


@Component({
  selector: 'oca-service-addresses-editor',
  templateUrl: './service-addresses-editor.component.html',
  styleUrls: ['./service-addresses-editor.component.scss',
    '../service-synced-value-editor/service-synced-value-editor.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [{
    provide: NG_VALUE_ACCESSOR,
    useExisting: ServiceAddressesEditorComponent,
    multi: true,
  }],
})
export class ServiceAddressesEditorComponent implements ControlValueAccessor, OnInit, OnDestroy {
  @ViewChild('inputFieldModel', { static: true }) inputFieldModel: NgModel;
  @ViewChild('agmMap') agmMap: AgmMap;
  @Input() maxCount = 1;
  @Input() countries: Country[];
  @Output() requestCountries = new EventEmitter<Country[]>();

  values: ServiceAddress[] = [];
  editingIndex: number | null = null;
  NEW_ITEM_INDEX = -1;
  syncedMessage: string;
  disabled = false;

  mapBounds: LatLngBounds | LatLngBoundsLiteral | boolean = false;
  mapZoom = 14;
  mapLatitude = 50.9298839;
  mapLongitude = 3.6268476;
  formGroup: FormGroup;

  googleMapsResults$ = new Subject<google.maps.places.PlaceResult[]>();
  map = new ReplaySubject<google.maps.Map>();
  private destroyed$ = new Subject();

  constructor(private translate: TranslateService,
              private changeDetectorRef: ChangeDetectorRef,
              private matDialog: MatDialog,
              private fb: FormBuilder) {
    this.formGroup = fb.group({
      name: '',
      provider: fb.control(null),
      coordinates: fb.group({
        lat: fb.control(0),
        lon: fb.control(0),
      }),
      google_maps_place_id: fb.control(null),
      country: fb.control('', [Validators.required]),
      locality: fb.control('', [Validators.required]),
      postal_code: fb.control('', [Validators.required]),
      street: fb.control('', [Validators.required]),
      street_number: fb.control('', [Validators.required]),
    });
  }

  ngOnInit(): void {
    this.syncedMessage = this.translate.instant('oca.value_synced_via_paddle_cannot_edit');
    // Resolves a name to a google place
    this.formGroup.controls.name.valueChanges.pipe(
      takeUntil(this.destroyed$),
      skip(1),  // Skip initial update from setting the value of the one we're updating
      debounceTime(600),
      filter(name => typeof name === 'string'),
      map(name => name.trim()),
      filter(name => !!name),
      distinctUntilChanged(),
    ).subscribe(name => this.geocodeFromName(name));

    // Resolve address to coordinates when any address fields are changed
    this.formGroup.valueChanges.pipe(
      takeUntil(this.destroyed$),
      skip(1),  // Skip initial update from setting the value of the one we're updating
      debounceTime(600),
      map(({ locality, postal_code, street, street_number }: ServiceAddress) => {
        if (street && street_number && (postal_code || locality)) {
          return `${street} ${street_number} ${postal_code} ${locality}`.trim();
        }
        return null;
      }),
      distinctUntilChanged(),
    ).subscribe(address => this.onAddressChanged(address));
  }

  ngOnDestroy(): void {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  changed() {
    this.onChange(this.values.concat());
  }

  removeValue(value: ServiceAddress) {
    this.values = this.values.filter(v => v !== value);
    this.changed();
  }

  saveAddress() {
    if (this.formGroup.invalid) {
      markAllControlsAsDirty(this.formGroup);
      return;
    }
    if (!this.formGroup.controls.coordinates.value?.lat) {
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
      this.values.push(this.formGroup.value);
    } else {
      this.values[ this.editingIndex as number ] = this.formGroup.value;
    }
    this.editingIndex = null;
    this.formGroup.reset();
    this.changed();
  }

  addValue() {
    this.formGroup.patchValue({
      name: null,
      provider: null,
      coordinates: {},
      google_maps_place_id: null,
      country: 'BE',
      locality: '',
      postal_code: '',
      street: '',
      street_number: '',
    } as Partial<ServiceAddress>);
    this.editingIndex = this.NEW_ITEM_INDEX;
    this.googleMapsResults$.next([]);
    this.requestCountries.emit();
  }

  editValue(value: ServiceAddress) {
    this.formGroup.patchValue({ ...value, coordinates: value.coordinates ?? {} });
    this.editingIndex = this.values.indexOf(value);
    this.googleMapsResults$.next([]);
    this.setMapCoordinates();
    this.requestCountries.emit();
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

  async mapsResultSelected(value: google.maps.places.PlaceResult) {
    const result = await this.geocode({ placeId: value.place_id });
    const geometry = value.geometry as google.maps.places.PlaceGeometry;
    const coordinates = { lat: geometry.location.lat(), lon: geometry.location.lng() };
    const address: Partial<ServiceAddress> = {
      street: '',
      street_number: '',
      locality: '',
      country: '',
      postal_code: '',
    };
    for (const component of result.address_components ?? []) {
      for (const type of component.types) {
        switch (type) {
          case 'street_number':
            address.street_number = component.long_name;
            break;
          case 'route':
            address.street = component.long_name;
            break;
          case 'locality':
            address.locality = component.long_name;
            break;
          case 'country':
            address.country = component.short_name;
            break;
          case 'postal_code':
            address.postal_code = component.long_name;
            break;
        }
      }
    }
    this.formGroup.patchValue({
      coordinates,
      google_maps_place_id: value.place_id,
      name: value.name,
      ...address,
    }, { emitEvent: false }); // set emitEvent to false to avoid geocoding it again via onAddressChanged
    this.mapBounds = geometry.viewport as LatLngBounds;
  }

  registerOnChange(fn: any): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: any): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }

  writeValue(values?: ServiceAddress[]): void {
    if (values) {
      this.values = values;
      this.changeDetectorRef.markForCheck();
    }
  }

  private onChange = (_: any) => {
  };
  private onTouched = () => {
  };

  private geocode(request: google.maps.GeocoderRequest): Promise<google.maps.GeocoderResult> {
    return new Promise((resolve, reject) => {
      new google.maps.Geocoder().geocode(request, (results, status) => {
        if (status === google.maps.GeocoderStatus.OK) {
          resolve(results[ 0 ]);
        } else {
          reject(status);
        }
        this.changeDetectorRef.markForCheck();
      });
    });
  }

  private setMapCoordinates() {
    const value = this.formGroup.value as ServiceAddress;
    if (value.coordinates) {
      this.mapBounds = false;
      this.mapLatitude = value.coordinates.lat;
      this.mapLongitude = value.coordinates.lon;
      this.changeDetectorRef.markForCheck();
    }
  }

  private async geocodeFromName(name: string) {
    this.googleMapsResults$.next([]);
    if (name.length > 3) {
      this.map.pipe(take(1)).subscribe(googleMap => {
        const service = new google.maps.places.PlacesService(googleMap);
        const fields = ['formatted_address', 'geometry', 'name', 'place_id'];
        service.findPlaceFromQuery({ query: name, fields }, (results, status) => {
          if (status === google.maps.places.PlacesServiceStatus.OK) {
            let bounds = new google.maps.LatLngBounds();
            const filteredResults: google.maps.places.PlaceResult[] = [];
            for (const result of results) {
              if (result.geometry) {
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
    }
  }

  private async onAddressChanged(address: string | null) {
    let coordinates: Partial<{ lat: number; lon: number }> = {};
    if (address) {
      const request: google.maps.GeocoderRequest = { address };
      const countryCode = this.formGroup.value.country;
      if (countryCode) {
        request.region = countryCode;
      }
      const result = await this.geocode(request);
      const geo = result.geometry;
      coordinates = { lat: geo.location.lat(), lon: geo.location.lng() };
      // Bounds can be undefined
      this.mapBounds = (geo.bounds || geo.viewport) as LatLngBounds;
    }
    this.formGroup.patchValue({ coordinates }, { emitEvent: false });
  }
}
