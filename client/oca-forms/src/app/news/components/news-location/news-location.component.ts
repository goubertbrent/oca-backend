import { ChangeDetectionStrategy, Component, forwardRef, Input, OnChanges, OnInit, SimpleChanges } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { Loadable } from '../../../shared/loadable/loadable';
import { CityAppLocations, LocationBounds, NewsAddress, NewsGeoAddress, NewsLocation } from '../../interfaces';
import { GetLocationsAction } from '../../news.actions';
import { getLocations, NewsState } from '../../news.state';

@Component({
  selector: 'oca-news-location',
  templateUrl: './news-location.component.html',
  styleUrls: ['./news-location.component.scss'],
  providers: [{
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => NewsLocationComponent),
    multi: true,
  }],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NewsLocationComponent implements OnInit, OnChanges, ControlValueAccessor {
  @Input() appId: string;
  disabled: boolean;

  set locations(value: NewsLocation) {
    this._locations = value;
    this.onChange(value);
  }

  get locations() {
    return this._locations;
  }

  bounds$: Observable<LocationBounds[]>;
  cityAppLocations$: Observable<Loadable<CityAppLocations>>;

  private _locations: NewsLocation;

  constructor(private store: Store<NewsState>) {
  }

  ngOnInit(): void {
    this.cityAppLocations$ = this.store.pipe(select(getLocations));
    this.bounds$ = this.cityAppLocations$.pipe(map(result => result.data ? result.data.localities.map(l => l.bounds) : []));
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.appId) {
      if (this.appId) {
        this.store.dispatch(new GetLocationsAction({ appId: this.appId }));
      }
    }
  }

  addAddress(address: NewsAddress) {
    if (!this.locations.addresses.some(a => a.street_name === address.street_name && a.zip_code === address.zip_code)) {
      this.locations = { ...this.locations, addresses: [...this.locations.addresses, address] };
      this.onChange(this.locations);
    }
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

  writeValue(value: any): void {
    if (value !== this.locations) {
      this.locations = value;
      this.onChange(value);
    }
  }

  private onChange = (_: any) => {
  };
  private onTouched = () => {
  };

  removeAddress(addr: NewsAddress) {
    this.locations = {
      ...this.locations,
      addresses: this.locations.addresses.filter(l => !(l.street_name === addr.street_name && l.zip_code === addr.zip_code)),
    };
  }

  updateGeoAddresses($event: NewsGeoAddress[]) {
    this.locations = { ...this.locations, geo_addresses: $event };
  }
}
