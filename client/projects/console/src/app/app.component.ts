import { OverlayContainer } from '@angular/cdk/overlay';
import { DOCUMENT } from '@angular/common';
import { ChangeDetectionStrategy, Component, Inject, OnInit, ViewEncapsulation } from '@angular/core';
import { ActivatedRoute, Event, NavigationEnd, Router } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { getRoutes, getSidebarItems, SidebarItem, UpdateSidebarItemsAction } from '../../framework/client/nav/sidebar';
import { CleanToolbarItemsAction } from '../../framework/client/nav/toolbar';
import { Route, RouteData } from './app.routes';
import { ThemingService } from './theming.service';

@Component({
  selector: 'console-root',
  templateUrl: 'app.component.html',
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AppComponent implements OnInit {

  toolbarTitle: string;
  sidebarItems$: Observable<SidebarItem[]>;
  previousBasePath: string;
  private currentParentRoute: string;
  private currentCssClass = 'light-theme';

  constructor(private store: Store,
              private router: Router,
              private route: ActivatedRoute,
              private themingService: ThemingService,
              private overlayContainer: OverlayContainer,
              @Inject(DOCUMENT) private document: Document) {
  }

  ngOnInit() {
    this.router.events.subscribe(event => this.handleRouteEvent(event));
    this.sidebarItems$ = this.store.pipe(select(getSidebarItems));
    this.store.pipe(select(getRoutes)).subscribe(routes => {
      this.store.dispatch(new UpdateSidebarItemsAction(this.updateSidebarItems(routes as Route[])));
    });
    this.themingService.theme.subscribe(theme => {
      const overlayClassList = this.overlayContainer.getContainerElement().classList;
      overlayClassList.remove(this.currentCssClass);
      this.document.body.classList.remove(this.currentCssClass);
      overlayClassList.add(theme);
      this.document.body.classList.add(theme);
    });
  }

  private updateSidebarItems(routes: Route[]): SidebarItem[] {
    const sidebarItems = [];
    for (const route of routes) {
      const routeData: RouteData = route.data as RouteData;
      const routeId = routeData && routeData.id;
      if (routeId) {
        const sidebarItem: SidebarItem = {
          id: routeData.id as string,
          icon: routeData.icon,
          label: (routeData.label || routeData.meta.title) as string,
          description: routeData.description,
          route: route.path as string,
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
      this.toolbarTitle = (routeData.label as string);
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
