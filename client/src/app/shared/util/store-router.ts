import { ActivatedRouteSnapshot, Data, Params, RouterStateSnapshot } from '@angular/router';
import { RouterReducerState, RouterStateSerializer, StoreRouterConfig } from '@ngrx/router-store';

export interface StoreRouter {
  url: string;
  queryParams: Params;
  params: Params;
  data: Data;
}

export type MergedRouteReducerState = RouterReducerState<StoreRouter>;

export class MergedRouterStateSerializer implements RouterStateSerializer<StoreRouter> {

  serialize(routerState: RouterStateSnapshot): StoreRouter {
    return {
      url: routerState.url,
      params: mergeRouteParams(routerState.root, 'params'),
      queryParams: mergeRouteParams(routerState.root, 'queryParams'),
      data: mergeRouteParams(routerState.root, 'data'),
    };
  }
}

function mergeRouteParams(route: ActivatedRouteSnapshot | null, property: 'params' | 'queryParams' | 'data'): Params {
  if (!route) {
    return {};
  }
  const currentParams = route[ property ];
  const primaryChild = route.children.find(c => c.outlet === 'primary') || route.firstChild;
  return { ...currentParams, ...mergeRouteParams(primaryChild, property) };
}

export const storeRouterConfig: StoreRouterConfig<StoreRouter> = { stateKey: 'router', serializer: MergedRouterStateSerializer };
