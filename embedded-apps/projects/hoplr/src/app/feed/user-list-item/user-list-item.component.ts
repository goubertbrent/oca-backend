import { ChangeDetectionStrategy, Component, Input, ViewEncapsulation } from '@angular/core';
import { HoplrUser } from '../../hoplr';

@Component({
  selector: 'hoplr-user-list-item',
  templateUrl: './user-list-item.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class UserListItemComponent {
  @Input() user: HoplrUser;
}
