import { OverlayConfig, OverlayContainer } from '@angular/cdk/overlay';
import { ChangeDetectionStrategy, Component, HostBinding, OnInit, ViewEncapsulation } from '@angular/core';
import { ActivatedRoute, Event, NavigationEnd, Router } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { UpdateSidebarItemsAction } from '../../framework/client/nav/sidebar/actions';
import { SidebarItem } from '../../framework/client/nav/sidebar/interfaces';
import { getRoutes, getSidebarItems } from '../../framework/client/nav/sidebar/sidebar.state';
import { CleanToolbarItemsAction } from '../../framework/client/nav/toolbar/actions';
import { Route, RouteData } from './app.routes';
import { ThemingService } from './theming.service';

@Component({
  selector: 'console-root',
  templateUrl: 'app.component.html',
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AppComponent implements OnInit {
  @HostBinding('class') public cssClass = 'light-theme';

  toolbarTitle: string;
  sidebarItems$: Observable<SidebarItem[]>;
  previousBasePath: string;
  private currentParentRoute: string;

  constructor(private store: Store,
              private router: Router,
              private route: ActivatedRoute,
              private themingService: ThemingService,
              private overlayContainer: OverlayContainer) {
  }

  ngOnInit() {
    this.router.events.subscribe(event => this.handleRouteEvent(event));
    this.sidebarItems$ = this.store.pipe(select(getSidebarItems));
    this.store.pipe(select(getRoutes)).subscribe(routes => {
      this.store.dispatch(new UpdateSidebarItemsAction(this.updateSidebarItems(<Route[]>routes)));
    });
    this.themingService.theme.subscribe(theme => {
      const overlayClassList = this.overlayContainer.getContainerElement().classList;
      overlayClassList.remove(this.cssClass);
      this.cssClass = theme;
      overlayClassList.add(theme);
    });
  }

  private updateSidebarItems(routes: Route[]): SidebarItem[] {
    const sidebarItems = [];
    for (const route of routes) {
      const routeData: RouteData = <RouteData>route.data;
      const routeId = routeData && routeData.id;
      if (routeId) {
        const sidebarItem: SidebarItem = {
          id: <string>routeData.id,
          icon: routeData.icon,
          label: <string>(routeData.label || routeData.meta.title),
          description: routeData.description,
          route: <string>route.path,
        };
        sidebarItems.push(sidebarItem);
      }
    }
    return sidebarItems;
  }

  private handleRouteEvent(event: Event) {
    if (event instanceof NavigationEnd) {
      // Get the secondary sidebar items from the current route its 'data' property (if any)
      const currentRoute = this.route.root.snapshot.firstChild;
      if (!currentRoute) {
        console.warn('No route for /');
        return;
      }
      const routeData: RouteData = currentRoute.data;
      this.toolbarTitle = <string>routeData.label;
      const baseRoute = currentRoute.url.map(u => u.path);
      const parentRoute = JSON.parse(JSON.stringify(baseRoute));
      parentRoute.splice(baseRoute.length - 1);
      this.currentParentRoute = parentRoute.join('/');
      const basePath = baseRoute.join('/');
      if (this.previousBasePath !== basePath) {
        this.store.dispatch(new CleanToolbarItemsAction());
      }
      this.previousBasePath = basePath;
    }
  }

}
