import { ChangeDetectionStrategy, Component, Input, ViewEncapsulation } from '@angular/core';
import { SidebarItem } from '../sidenav/interfaces';

@Component({
  selector: 'oca-nav-item',
  templateUrl: './nav-item.component.html',
  styleUrls: [ './nav-item.component.scss' ],
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NavItemComponent {
  @Input()
  item: SidebarItem;
}
