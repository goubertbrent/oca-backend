import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnInit, Output, ViewChild } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatAutocompleteTrigger } from '@angular/material/autocomplete';
import { Observable } from 'rxjs';
import { map, startWith } from 'rxjs/operators';
import { CityAppLocations, Locality, NewsAddress, Street } from '../../interfaces';

@Component({
  selector: 'oca-choose-location',
  templateUrl: './choose-location.component.html',
  styleUrls: ['./choose-location.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ChooseLocationComponent implements OnInit {
  @ViewChild('autoCompleteTrigger', { static: true }) autoCompleteTrigger: MatAutocompleteTrigger;
  @Input() set locations(value: CityAppLocations | null) {
    this._locations = value;
    if (value && value.localities.length > 0) {
      this.zipChanged(value.localities[ 0 ].postal_code);
      // Ensure the streetNameControl.valueChanges observable emits by setting the value (else we may have no autocomplete options)
      this.streetNameControl.setValue('');
    }
  }

  get locations() {
    return this._locations;
  }

  @Output() addressAdded = new EventEmitter<NewsAddress>();

  streetNameControl = new FormControl();
  address: NewsAddress;
  currentLocality: Locality | null;
  filteredStreets$: Observable<Street[]>;

  private _locations: CityAppLocations | null;

  ngOnInit(): void {
    this.filteredStreets$ = this.streetNameControl.valueChanges.pipe(
      startWith(''),
      map(value => this._filterStreets(value)),
    );
  }

  zipChanged(zipCode: string) {
    const locations = this.locations as CityAppLocations;
    this.currentLocality = locations.localities.find(l => l.postal_code === zipCode) as Locality;
    this.address = {
      zip_code: this.currentLocality.postal_code,
      city: this.currentLocality.name,
      country_code: locations.country_code,
      level: 'STREET',
      street_name: '',
    };
  }

  addAddress(streetName: string) {
    this.streetNameControl.setValue('');
    this.addressAdded.emit({ ...this.address, street_name: streetName });
    setTimeout(() => this.autoCompleteTrigger.openPanel(), 0);
  }

  tryAddStreet() {
    const value = (this.streetNameControl.value || '').trim().toLowerCase();
    if (this.currentLocality && value) {
      const foundStreet = this.currentLocality.streets.find(street => street.name.toLowerCase() === value);
      if (foundStreet) {
        this.addAddress(foundStreet.name);
      }
    }
  }

  private _filterStreets(name: string) {
    const filterValue = name.trim().toLowerCase();
    if (this.currentLocality) {
      if (!filterValue) {
        return this.currentLocality.streets;
      }
      return this.currentLocality.streets.filter(street => street.name.toLowerCase().includes(filterValue));
    }
    return [];
  }

}
