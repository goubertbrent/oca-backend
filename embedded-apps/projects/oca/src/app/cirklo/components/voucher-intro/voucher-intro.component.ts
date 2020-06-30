import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

@Component({
  selector: 'app-voucher-intro',
  templateUrl: './voucher-intro.component.html',
  styleUrls: ['./voucher-intro.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class VoucherIntroComponent {
  @Input() title: string;
  @Input() description: string;
  @Input() logoUrl: string;
}
