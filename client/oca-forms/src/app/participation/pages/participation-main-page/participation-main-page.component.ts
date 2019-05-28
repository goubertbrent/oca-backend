import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';

interface NavItem {
  route: string;
  label: string;
  icon: string;
}

@Component({
  selector: 'oca-participation-main-page',
  templateUrl: './participation-main-page.component.html',
  styleUrls: [ './participation-main-page.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ParticipationMainPageComponent implements OnInit {
  navItems: NavItem[] = [
    { icon: 'list', label: 'oca.projects', route: 'projects' },
    { icon: 'settings', label: 'oca.settings', route: 'settings' },
  ];

  constructor() {
  }

  ngOnInit() {
  }

}
