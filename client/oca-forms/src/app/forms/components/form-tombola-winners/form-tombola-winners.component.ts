import { ChangeDetectionStrategy, Component, Input, ViewEncapsulation } from '@angular/core';
import { UserDetailsTO } from '../../../shared/users/interfaces';

@Component({
  selector: 'oca-form-tombola-winners',
  templateUrl: './form-tombola-winners.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class FormTombolaWinnersComponent {

  @Input() tombolaWinners: UserDetailsTO[];

  trackByWinner(index: number, value: UserDetailsTO) {
    return value.email;
  }
}
