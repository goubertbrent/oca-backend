import { LatLngLiteral } from '@agm/core';
import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { NgForm } from '@angular/forms';
import { deepCopy } from '../../../shared/util';
import { MapButton, MapConfig } from '../../maps';

@Component({
  selector: 'oca-map-config',
  templateUrl: './map-config.component.html',
  styleUrls: ['./map-config.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MapConfigComponent {
  @Input() filters: { value: string; label: string }[];

  @Input() set mapConfig(value: MapConfig) {
    this._mapConfig = deepCopy(value);
  }

  get mapConfig() {
    return this._mapConfig;
  }

  @Input() disabled = false;
  @Output() saved = new EventEmitter<MapConfig>();

  private _mapConfig: MapConfig;

  addButton() {
    this.mapConfig = {
      ...this.mapConfig,
      buttons: [...this.mapConfig.buttons, {
        icon: 'fa-external-link',
        action: 'https://onzestadapp.be',
        color: null,
        text: null,
        service: null,
      }],
    };
  }

  removeButton(button: MapButton) {
    this.mapConfig = { ...this.mapConfig, buttons: this.mapConfig.buttons.filter(b => b !== button) };
  }

  submit(form: NgForm) {
    if (form.form.valid) {
      this.saved.emit({ ...this.mapConfig, distance: Math.round(this.mapConfig.distance) });
    }
  }

  setNewCenter($event: LatLngLiteral) {
    this.mapConfig = { ...this.mapConfig, center: { lat: $event.lat, lon: $event.lng } };
  }
}
