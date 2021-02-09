import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { FormControl, FormGroup } from '@angular/forms';
import { select, Store } from '@ngrx/store';
import { IFormGroup } from '@rxweb/types';
import { Observable, Subject } from 'rxjs';
import { debounceTime, take, takeUntil } from 'rxjs/operators';
import { PointOfInterest, POIStatus } from '../../point-of-interest';
import { loadPointOfInterests } from '../../point-of-interest.actions';
import { getPOICursor, getPoiFilter, getPointOfInterests, hasMorePoi, isLoadingPoiList } from '../../point-of-interest.selectors';

@Component({
  selector: 'oca-point-of-interest-list-page',
  templateUrl: './point-of-interest-list-page.component.html',
  styleUrls: ['./point-of-interest-list-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PointOfInterestListPageComponent implements OnInit, OnDestroy {
  isLoadingPoiList$: Observable<boolean>;
  hasMorePoi$: Observable<boolean>;
  pointsOfInterest$: Observable<PointOfInterest[]>;
  filterForm = new FormGroup({
    status: new FormControl(null),
    query: new FormControl(null),
  }) as IFormGroup<{ status: POIStatus | null; query: string | null }>;
  poiStatuses = [
    { value: POIStatus.VISIBLE, icon: '🟢', label: 'oca.visible' },
    { value: POIStatus.INCOMPLETE, icon: '🟠', label: 'oca.incomplete' },
    { value: POIStatus.INVISIBLE, icon: '🔴', label: 'oca.invisible' },
  ];

  private destroyed$ = new Subject();

  constructor(private store: Store) {
  }

  ngOnInit(): void {
    this.pointsOfInterest$ = this.store.pipe(select(getPointOfInterests));
    this.isLoadingPoiList$ = this.store.pipe(select(isLoadingPoiList));
    this.hasMorePoi$ = this.store.pipe(select(hasMorePoi));
    this.pointsOfInterest$.pipe(take(1)).subscribe(items => {
      // Only load items on initial page load
      if (items.length === 0) {
        this.store.dispatch(loadPointOfInterests({ cursor: null, status: null, query: null }));
      }
    });
    this.store.pipe(select(getPoiFilter), take(1)).subscribe(filter => this.filterForm.setValue(filter));
    this.filterForm.controls.query.valueChanges.pipe(
      takeUntil(this.destroyed$),
      debounceTime(600),
    ).subscribe((query) => this.loadFiltered({ query }));
    this.filterForm.controls.status.valueChanges.pipe(takeUntil(this.destroyed$)).subscribe((status) => this.loadFiltered({ status }));
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  loadMorePoi() {
    this.store.pipe(select(getPOICursor), take(1)).subscribe(cursor => {
      if (cursor) {
        this.store.dispatch(loadPointOfInterests({ cursor, ...this.filterForm.value! }));
      }
    });
  }

  loadFiltered(filter: Partial<{ status: POIStatus | null; query: string | null }>) {
    this.store.dispatch(loadPointOfInterests({ cursor: null, ...this.filterForm.value!, ...filter }));
  }
}
