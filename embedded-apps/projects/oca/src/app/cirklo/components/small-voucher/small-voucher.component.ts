import { animate, style, transition, trigger } from '@angular/animations';
import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-small-voucher',
  templateUrl: './small-voucher.component.html',
  styleUrls: ['./small-voucher.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  animations: [
    trigger('fabAppearAnimation', [
      transition(':enter', [
        style({ transform: 'scale(0)' }),
        animate('250ms cubic-bezier(0.4, 0.0, 0.2, 1)', style({ transform: 'scale(1)' })),
      ]),
      transition(':leave', [
        animate('200ms cubic-bezier(0.4, 0.0, 0.2, 1)', style({ transform: 'scale(0)' })),
      ]),
    ]),
  ],
})
export class SmallVoucherComponent {
  @Input() logoUrl: string;
  @Input() remainingValue: number;
  @Input() value: number;
  @Input() validDate: string;
  @Input() expired = false;
  @Input() canDelete = false;
  @Output() delete = new EventEmitter();

  onDeleteClicked($event: MouseEvent) {
    // Prevent possible click events that have registered on the element from triggering
    $event.stopPropagation();
    this.delete.emit();
  }
}
