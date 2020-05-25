import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

@Component({
  selector: 'app-large-voucher',
  templateUrl: './large-voucher.component.html',
  styleUrls: ['./large-voucher.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LargeVoucherComponent {
  @Input() voucherId: string;
  @Input() logoUrl: string;
  @Input() qrData: string;
  @Input() remainingValue: number;
  @Input() value: number;
  @Input() validDate: string;
  @Input() expired = false;
  cirkloUrl = '<a href="https://cirklo-light.com">cirklo-light.com</a>';
}
