import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnChanges, Output, SimpleChanges } from '@angular/core';
import { NgForm } from '@angular/forms';
import { Loadable } from '../../../shared/loadable/loadable';
import { deepCopy } from '../../../shared/util/misc';
import { CitySettings } from '../../projects';

@Component({
  selector: 'oca-city-settings',
  templateUrl: './city-settings.component.html',
  styleUrls: [ './city-settings.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CitySettingsComponent implements OnChanges {
  @Input() settings: Loadable<CitySettings>;
  @Output() saved = new EventEmitter<CitySettings>();

  _settings: CitySettings;

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.settings) {
      if (this.settings.data) {
        this._settings = deepCopy(this.settings.data);
      }
    }
  }

  submit(form: NgForm) {
    if (form.form.valid) {
      this.saved.emit(this._settings);
    }
  }
}
