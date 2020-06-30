import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  OnChanges,
  Output,
  SimpleChanges,
  ViewChild,
  ViewEncapsulation,
} from '@angular/core';
import { NgForm } from '@angular/forms';
import { Locations } from '../../../appointments';

@Component({
  selector: 'app-jcc-location-time',
  templateUrl: './jcc-location-time.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class JccLocationTimeComponent implements OnChanges {
  @Input() locations: Locations;
  @Input() availableDays: string[];
  @Input() availableTimes: string[];
  @Output() locationPicked = new EventEmitter<string>();
  @Output() dayPicked = new EventEmitter<string>();
  @Output() timePicked = new EventEmitter<string>();
  selectedLocation: string | null = null;
  selectedDate: string | null = null;
  selectedTime: string | null = null;
  @ViewChild('form', { static: true }) private form: NgForm;

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.locations && this.locations && this.locations.length > 0) {
      this.setLocation(this.locations[ 0 ].locationID);
    }
    if (changes.availableDays && this.availableDays && this.availableDays.length > 0) {
      // this.setDate(this.availableDays[ 0 ]);
    }
    if (changes.availableTimes && this.availableTimes && this.availableTimes.length > 0) {
      this.setTime(this.availableTimes[ 0 ]);
    }
  }

  setLocation(locationID: string) {
    this.selectedLocation = locationID;
    this.selectedDate = null;
    this.locationPicked.emit(locationID);
  }

  setDate(date: string) {
    this.selectedDate = date;
    this.selectedTime = null;
    this.dayPicked.emit(date);
  }

  setTime(date: string) {
    this.selectedTime = date;
    this.timePicked.emit(date);
  }

  isValid() {
    return this.form.form.valid;
  }
}
