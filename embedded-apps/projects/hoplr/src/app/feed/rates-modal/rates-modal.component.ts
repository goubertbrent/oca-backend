import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { ModalController } from '@ionic/angular';
import { HoplrRate } from '../../hoplr';

export interface  RateOption {
  label: string;
  iconUrl?: string;
  iconName?: string;
  rates: HoplrRate[];
}


@Component({
  selector: 'hoplr-rates-modal',
  templateUrl: './rates-modal.component.html',
  styleUrls: ['./rates-modal.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RatesModalComponent {
  @Input() rates: RateOption[] = [];
  @Input() label: string;

  constructor(private modal: ModalController) {
  }

  closeModal() {
    this.modal.dismiss();
  }
}
