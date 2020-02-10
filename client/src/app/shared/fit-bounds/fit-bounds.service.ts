import { LatLng, LatLngBounds, LatLngLiteral, MapsAPILoader } from '@agm/core';
import { Injectable } from '@angular/core';
import { BehaviorSubject, from, Observable, timer } from 'rxjs';
import {
  flatMap,
  map,
  sample,
  shareReplay,
  switchMap,
} from 'rxjs/operators';

declare var google: any;

export interface FitBoundsDetails {
  latLng: LatLng | LatLngLiteral;
}

/**
 * @internal
 */
export type BoundsMap = Map<string, LatLng | LatLngLiteral>;

/**
 * Class to implement when you what to be able to make it work with the auto fit bounds feature
 * of AGM.
 */
export abstract class FitBoundsAccessor {
  abstract getFitBoundsDetails$(): Observable<FitBoundsDetails>;
}

/**
 * The FitBoundsService is responsible for computing the bounds of the a single map.
 * Copied from @agm/maps since they don't properly export it
 */
@Injectable({providedIn: 'root'})
export class FitBoundsService {
  protected readonly bounds$: Observable<LatLngBounds>;
  protected readonly _boundsChangeSampleTime$ = new BehaviorSubject<number>(200);
  protected readonly _includeInBounds$ = new BehaviorSubject<BoundsMap>(new Map<string, LatLng | LatLngLiteral>());

  constructor(loader: MapsAPILoader) {
    this.bounds$ = from(loader.load()).pipe(
      flatMap(() => this._includeInBounds$),
      sample(
        this._boundsChangeSampleTime$.pipe(switchMap(time => timer(0, time))),
      ),
      map(includeInBounds => this._generateBounds(includeInBounds)),
      shareReplay(1),
    );
  }

  private _generateBounds(
    includeInBounds: Map<string, LatLng | LatLngLiteral>,
  ) {
    const bounds = new google.maps.LatLngBounds() as LatLngBounds;
    includeInBounds.forEach(b => bounds.extend(b));
    return bounds;
  }

  addToBounds(latLng: LatLng | LatLngLiteral) {
    const id = this._createIdentifier(latLng);
    if (this._includeInBounds$.value.has(id)) {
      return;
    }
    const boundsMap = this._includeInBounds$.value;
    boundsMap.set(id, latLng);
    this._includeInBounds$.next(boundsMap);
  }

  removeFromBounds(latLng: LatLng | LatLngLiteral) {
    const boundsMap = this._includeInBounds$.value;
    boundsMap.delete(this._createIdentifier(latLng));
    this._includeInBounds$.next(boundsMap);
  }

  changeFitBoundsChangeSampleTime(timeMs: number) {
    this._boundsChangeSampleTime$.next(timeMs);
  }

  getBounds$(): Observable<LatLngBounds> {
    return this.bounds$;
  }

  protected _createIdentifier(latLng: LatLng | LatLngLiteral): string {
    return `${latLng.lat}+${latLng.lng}`;
  }
}
