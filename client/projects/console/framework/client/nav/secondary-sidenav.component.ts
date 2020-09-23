import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { SecondarySidebarItem, SidebarTitle } from './sidebar';

@Component({
  selector: 'secondary-sidenav',
  templateUrl: 'secondary-sidenav.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  styleUrls: ['./secondary-sidenav.component.scss'],
})
export class SecondarySidenavComponent {
  @Input() sidebarItems: SecondarySidebarItem[];
  @Input() sidebarTitle: SidebarTitle;
}
