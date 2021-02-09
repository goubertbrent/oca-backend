import { MouseEvent } from '@agm/core';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  EventEmitter,
  Input,
  NgZone,
  OnDestroy,
  OnInit,
  Output,
} from '@angular/core';
import { FormBuilder, FormControl, Validators } from '@angular/forms';
import { select, Store } from '@ngrx/store';
import { LatLonTO, maybeDispatchAction } from '@oca/web-shared';
import { IFormBuilder, IFormGroup } from '@rxweb/types';
import { merge, Observable, ReplaySubject, Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged, filter, skip, take, takeUntil } from 'rxjs/operators';
import { AVATAR_PLACEHOLDER } from '../../../consts';
import { AvailableOtherPlaceType, AvailablePlaceType, BaseOpeningHours, OpeningHourType } from '../../../shared/interfaces/oca';
import { GoogleMapsApiService } from '../../../shared/maps/google-maps-api.service';
import { GetAvailablePlaceTypesAction } from '../../../shared/shared.actions';
import { getAvailablePlaceTypes, getAvailablePlaceTypesState } from '../../../shared/shared.state';
import { UploadFileDialogConfig } from '../../../shared/upload-file';
import { DeepPartial } from '../../../shared/util';
import { CreatePointOfInterest, POILocation } from '../../point-of-interest';


@Component({
  selector: 'oca-point-of-interest-form',
  templateUrl: './point-of-interest-form.component.html',
  styleUrls: ['./point-of-interest-form.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PointOfInterestFormComponent implements OnInit, OnDestroy {
  AVATAR_PLACEHOLDER = AVATAR_PLACEHOLDER;

  @Output() saved = new EventEmitter<CreatePointOfInterest>();
  placeTypes$: Observable<AvailablePlaceType[]>;
  otherPlaceTypes$: ReplaySubject<AvailableOtherPlaceType[]> = new ReplaySubject();
  googleMapsPlaceResults$ = new Subject<google.maps.places.PlaceResult[]>();
  formGroup: IFormGroup<CreatePointOfInterest>;
  placeNameControl = new FormControl();
  map = new ReplaySubject<google.maps.Map>();
  uploadFileDialogConfig: Partial<UploadFileDialogConfig> = {
    uploadPrefix: '',
  };
  private destroyed$ = new Subject();

  constructor(private formBuilder: FormBuilder,
              private store: Store,
              private changeDetectorRef: ChangeDetectorRef,
              private ngZone: NgZone,
              private mapsService: GoogleMapsApiService) {
    const fb = (formBuilder as IFormBuilder);
    this.formGroup = fb.group<CreatePointOfInterest>({
      title: fb.control('', Validators.required),
      description: fb.control(null),
      location: fb.group<POILocation>({
        coordinates: fb.group<LatLonTO>({
            lat: fb.control<number>(50.9598),
            lon: fb.control<number>(3.5951),
          },
        ),
        country: fb.control(null),
        google_maps_place_id: fb.control(null),
        locality: fb.control(null),
        postal_code: fb.control(null),
        street: fb.control(null),
        street_number: fb.control(null),
      }),
      main_place_type: fb.control(null, Validators.required),
      place_types: fb.control([], Validators.required),
      opening_hours: fb.control<BaseOpeningHours>({
        periods: [],
        type: OpeningHourType.NOT_RELEVANT,
        text: null,
        exceptional_opening_hours: [],
      }),
      media: fb.control([]),
      visible: fb.control<boolean>(true),
    });
  }

  private _poiId: number | null = null;

  get poiId() {
    return this._poiId;
  }

  @Input() set poiId(value: number | null) {
    this._poiId = value;
    if (value) {
      this.uploadFileDialogConfig.reference = { type: 'point_of_interest', id: value };
    }
  }

  @Input() set poi(value: DeepPartial<CreatePointOfInterest> | null) {
    if (value) {
      this.formGroup.patchValue(value as any, { emitEvent: false });
    }
  }

  @Input() set disabled(value: boolean) {
    if (value) {
      this.formGroup.disable({ emitEvent: false });
    } else {
      this.formGroup.enable({ emitEvent: false });
    }
  }

  ngOnInit() {
    maybeDispatchAction(this.store, getAvailablePlaceTypesState, new GetAvailablePlaceTypesAction());
    this.placeTypes$ = this.store.pipe(select(getAvailablePlaceTypes));
    this.placeTypes$.pipe(takeUntil(this.destroyed$)).subscribe(() => this.setOtherPlaceTypes());
    this.formGroup.controls.main_place_type.valueChanges.pipe(
      takeUntil(this.destroyed$),
    ).subscribe(mainPlaceType => this.mainPlaceTypeChanged(mainPlaceType));
    const locationForm = this.formGroup.controls.location as IFormGroup<POILocation>;
    merge(locationForm.controls.locality.valueChanges,
      locationForm.controls.street.valueChanges,
      locationForm.controls.street_number.valueChanges,
    ).pipe(
      takeUntil(this.destroyed$),
      debounceTime(600),
      skip(1),
      distinctUntilChanged((previous, current) => JSON.stringify(previous) === JSON.stringify(current)),
    ).subscribe(() => {
      if (locationForm.valid) {
        const location = locationForm.value!;
        this.geocodeAddress(location);
      }
    });
    this.placeNameControl.valueChanges.pipe(
      takeUntil(this.destroyed$),
      // when selecting a suggestion, this won't be a string but an object containing the suggestion
      debounceTime(600),
      filter(name => typeof name === 'string'),
      filter(name => !!name),
      distinctUntilChanged(),
    ).subscribe(placeName => this.geoCodeFromPlaceName(placeName));
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  onMapReady($event: any) {
    this.map.next($event);
  }

  mainPlaceTypeChanged(mainPlaceType: string | null) {
    const placeTypes = this.formGroup.value!.place_types as string[];
    if (mainPlaceType && !placeTypes.includes(mainPlaceType)) {
      this.formGroup.controls.place_types.setValue([mainPlaceType, ...placeTypes]);
    }
    this.setOtherPlaceTypes();
  }

  submit() {
    if (this.formGroup.valid) {
      this.saved.emit(this.formGroup.value!);
    }
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

  async placeResultSelected(value: google.maps.places.PlaceResult) {
    const resolved = await this.mapsService.geocode({ placeId: value.place_id });
    const addr = this.mapsService.addressComponentsToObject(resolved.address_components);
    const location = value.geometry!.location;
    this.formGroup.patchValue({
      location: {
        google_maps_place_id: value.place_id!,
        locality: addr.locality,
        postal_code: addr.postalCode,
        street: addr.street,
        street_number: addr.streetNumber,
        country: addr.country!,
        coordinates: { lat: location.lat(), lon: location.lng() },
      },
    }, { emitEvent: false });
    this.changeDetectorRef.markForCheck();
  }

  private setOtherPlaceTypes() {
    this.placeTypes$.pipe(take(1), takeUntil(this.destroyed$)).subscribe(types => {
      const mainType = this.formGroup.value!.main_place_type;
      this.otherPlaceTypes$.next(types.map(p => ({ ...p, disabled: mainType === p.value })));
    });
  }

  async locationUpdated($event: MouseEvent) {
    this.formGroup.controls.location.patchValue({
      google_maps_place_id: null,
      coordinates: {
        lat: $event.coords.lat,
        lon: $event.coords.lng,
      },
    }, { emitEvent: false });
  }

  private async geocodeAddress(location: POILocation) {
    let address = '';
    if (location.street) {
      address += `${location.street}`;
    }
    if (location.street_number) {
      address += ` ${location.street_number}`;
    }
    address += ` ${location.postal_code} ${location.locality}`;
    const request: google.maps.GeocoderRequest = {
      address,
      componentRestrictions: {
        country: location.country!,
      },
    };
    try {
      const result = await this.mapsService.geocode(request);
      const resolvedLocation = result.geometry.location;
      this.formGroup.controls.location.patchValue({
        google_maps_place_id: result.place_id,
        coordinates: { lat: resolvedLocation.lat(), lon: resolvedLocation.lng() },
      }, { emitEvent: false });
    } catch (e) {
      console.log('Failed to geocode', e);
    }
  }

  private geoCodeFromPlaceName(placeName: string) {
    this.googleMapsPlaceResults$.next([]);
    this.map.pipe(take(1)).subscribe(googleMap => {
      const service = new google.maps.places.PlacesService(googleMap);
      const fields = ['formatted_address', 'geometry', 'name', 'place_id'];
      service.findPlaceFromQuery({ query: placeName, fields }, (results, status) => {
        if (status === google.maps.places.PlacesServiceStatus.OK) {
          const filteredResults = results.filter(result => !!result.geometry);
          this.ngZone.run(() => {
            this.googleMapsPlaceResults$.next(filteredResults);
            this.changeDetectorRef.markForCheck();
          });
        }
      });
    });
  }
}
