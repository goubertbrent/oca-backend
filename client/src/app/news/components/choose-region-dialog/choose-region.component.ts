import { LatLngBoundsLiteral, LatLngLiteral, MouseEvent } from '@agm/core';
import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnDestroy, OnInit, Output } from '@angular/core';
import { MatDialog, MatDialogConfig } from '@angular/material/dialog';
import { TranslateService } from '@ngx-translate/core';
import { ReplaySubject, Subject } from 'rxjs';
import { filter, map, takeUntil } from 'rxjs/operators';
import { SimpleDialogComponent, SimpleDialogData, SimpleDialogResult } from '../../../shared/dialog/simple-dialog.component';
import { FitBoundsService } from '../../../shared/fit-bounds/fit-bounds.service';
import { LocationBounds, NewsGeoAddress } from '../../interfaces';

@Component({
  selector: 'oca-choose-region',
  templateUrl: './choose-region.component.html',
  styleUrls: ['./choose-region.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ChooseRegionComponent implements OnInit, OnDestroy {
  @Input() set bounds(value: LocationBounds[]) {
    this._bounds = value;
    this.setBounds(this._bounds);
  }

  @Input() addresses: NewsGeoAddress[] = [];

  @Input() set disabled(value: boolean) {
    this._disabled = value;
    if (value && this.addresses.length) {
      this.bounds$.next(true);
    }
  }

  get disabled() {
    return this._disabled;
  }

  @Output() addressesChanged = new EventEmitter<NewsGeoAddress[]>();

  bounds$ = new ReplaySubject<LatLngBoundsLiteral | boolean>();
  private _bounds: LocationBounds[];
  private _disabled = false;
  private destroyed$ = new Subject();

  constructor(private fitBoundsService: FitBoundsService,
              private matDialog: MatDialog,
              private translate: TranslateService) {
  }

  ngOnInit(): void {
    this.fitBoundsService.getBounds$().pipe(filter(b => b.getNorthEast().lat() !== -1), map(bounds => ({
      north: bounds.getNorthEast().lat(),
      east: bounds.getNorthEast().lng(),
      south: bounds.getSouthWest().lat(),
      west: bounds.getSouthWest().lng(),
    })), takeUntil(this.destroyed$)).subscribe(bounds => {
      if (!this.disabled || !this.addresses.length) {
        this.bounds$.next(bounds);
      }
    });
  }

  ngOnDestroy(): void {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  private setBounds(bounds: LocationBounds[]) {
    for (const bound of bounds) {
      this.fitBoundsService.addToBounds({ lat: bound.northeast.lat, lng: bound.northeast.lon });
      this.fitBoundsService.addToBounds({ lat: bound.southwest.lat, lng: bound.southwest.lon });
    }
  }

  addMarker(event: MouseEvent) {
    if (!this.disabled) {
      this.addresses = [...this.addresses, { distance: 1000, latitude: event.coords.lat, longitude: event.coords.lng }];
      this.addressesChanged.emit(this.addresses);
    }
  }

  setCenter(index: number, $event: LatLngLiteral) {
    this.addresses[ index ] = { distance: this.addresses[ index ].distance, latitude: $event.lat, longitude: $event.lng };
    this.addressesChanged.emit(this.addresses);
  }

  setRadius(index: number, $event: number) {
    this.addresses[ index ] = { ...this.addresses[ index ], distance: Math.round($event) };
    this.addressesChanged.emit(this.addresses);
  }

  removeCircle(circle: NewsGeoAddress) {
    if (this.disabled) {
      return;
    }
    const config: MatDialogConfig<SimpleDialogData> = {
      data: {
        title: this.translate.instant('oca.confirmation'),
        ok: this.translate.instant('oca.Yes'),
        cancel: this.translate.instant('oca.No'),
        message: this.translate.instant('oca.ask_delete_location'),
      },
    };
    this.matDialog.open<SimpleDialogComponent, SimpleDialogData, SimpleDialogResult>(SimpleDialogComponent, config)
      .afterClosed().subscribe(result => {
      if (result && result.submitted) {
        this.addresses = this.addresses.filter(c => !(c.latitude === circle.latitude && c.longitude === circle.longitude));
        this.addressesChanged.emit(this.addresses);
      }
    });
  }

}
