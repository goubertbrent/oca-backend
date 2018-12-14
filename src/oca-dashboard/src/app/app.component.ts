import { BreakpointObserver, Breakpoints, BreakpointState } from '@angular/cdk/layout';
import { ChangeDetectionStrategy, Component, ViewChild } from '@angular/core';
import { MatSidenav } from '@angular/material';
import { NavigationEnd, Router } from '@angular/router';
import { Observable, of } from 'rxjs';
import { filter, map, tap } from 'rxjs/operators';
import { SidebarItem } from './sidenav/interfaces';

@Component({
  selector: 'oca-root',
  templateUrl: './app.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AppComponent {
  title = 'oca-dashboard';
  sidebarItems$: Observable<SidebarItem[]>;
  toolbarTitle = 'Page title';
  smallScreenObserver$: Observable<BreakpointState>;
  sideNavMode$: Observable<'over' | 'push' | 'side'>;
  @ViewChild(MatSidenav)
  sideNav: MatSidenav;

  constructor(private breakpointObserver: BreakpointObserver, private router: Router) {
    this.sidebarItems$ = of([ {
      id: 'home',
      label: 'Homepage with long name',
      route: '',
      icon: 'home',
      subItems: [],
    }, {
      id: 'news',
      label: 'News',
      route: 'news',
      icon: 'list',
      subItems: [
        {
          id: 'news.list',
          label: 'Sent news',
          route: 'news/list',
        },
        {
          id: 'news.create',
          label: 'Create news',
          route: 'news/create',
        },
      ],
    }, {
      id: 'home',
      label: 'Homepage with long name',
      route: '',
      icon: 'home',
      subItems: [],
    }, {
      id: 'news',
      label: 'News',
      route: 'news',
      icon: 'list',
      subItems: [
        {
          id: 'news.list',
          label: 'Sent news',
          route: 'news/list',
        },
        {
          id: 'news.create',
          label: 'Create news',
          route: 'news/create',
        },
      ],
    } ]);
    this.smallScreenObserver$ = breakpointObserver.observe([ Breakpoints.XSmall, Breakpoints.Small,
    ]);
    // Open on close sidenav depending on screen size
    this.sideNavMode$ = this.smallScreenObserver$.pipe(
      tap(state => state.matches ? this.sideNav.close() : this.sideNav.open()),
      map(state => state.matches ? 'over' : 'side'));
  }
}
