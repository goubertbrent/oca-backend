import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { combineLatest, Observable, Subject } from 'rxjs';
import { map } from 'rxjs/operators';
import { SharedService } from '../../../shared/shared.service';
import { isPlaceTypesLoading } from '../../../shared/shared.state';
import { DeepPartial } from '../../../shared/util';
import { CreatePointOfInterest } from '../../point-of-interest';
import { createPointOfInterest } from '../../point-of-interest.actions';
import { isLoadingPoi } from '../../point-of-interest.selectors';

@Component({
  selector: 'oca-create-point-of-interest-page',
  templateUrl: './create-point-of-interest-page.component.html',
  styleUrls: ['./create-point-of-interest-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CreatePointOfInterestPageComponent implements OnInit {
  isLoading$: Observable<boolean>;
  poi$ = new Subject<DeepPartial<CreatePointOfInterest>>();

  constructor(private store: Store,
              private sharedService: SharedService) {
  }

  ngOnInit(): void {
    this.isLoading$ = combineLatest([
      this.store.pipe(select(isLoadingPoi)),
      this.store.pipe(select(isPlaceTypesLoading)),
    ]).pipe(map(results => results.some(r => r)));
    this.sharedService.getGeoFence().subscribe(fence => {
      this.poi$.next({
        location: {
          country: fence.country,
          locality: fence.defaults?.locality,
          postal_code: fence.defaults?.postal_code,
        },
      });
    });
  }

  submit(data: CreatePointOfInterest) {
    this.store.dispatch(createPointOfInterest({ data }));
  }

}
