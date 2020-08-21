import { ChangeDetectionStrategy, Component, Input, ViewEncapsulation } from '@angular/core';
import { SecondarySidebarItem, SidebarTitle } from './sidebar';

@Component({
  selector: 'secondary-sidenav',
  templateUrl: 'secondary-sidenav.component.html',
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SecondarySidenavComponent {
  @Input() sidebarItems: SecondarySidebarItem[];
  @Input() sidebarTitle: SidebarTitle;
}
