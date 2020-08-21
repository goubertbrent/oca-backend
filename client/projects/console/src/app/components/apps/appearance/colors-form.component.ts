import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { AppColors } from '../../../interfaces';

@Component({
  selector: 'rcc-app-colors-form',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'colors-form.component.html',
})
export class ColorsFormComponent {
  @Input() status: ApiRequestStatus;
  @Output() save = new EventEmitter<AppColors>();

  private _colors: AppColors;

  get colors(): AppColors {
    return this._colors;
  }

  @Input()
  set colors(value: AppColors) {
    if (value) {
      this._colors = { ...value };
    }
  }

  submit() {
    this.save.emit(this.colors);
  }
}
