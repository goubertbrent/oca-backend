import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { ActivatedRoute } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { SimpleDialogComponent, SimpleDialogData, SimpleDialogResult } from '@oca/web-shared';
import { combineLatest, Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { isPlaceTypesLoading } from '../../../shared/shared.state';
import { CreatePointOfInterest, PointOfInterest } from '../../point-of-interest';
import { deletePointOfInterest, getPointOfInterest, updatePointOfInterest } from '../../point-of-interest.actions';
import { getCurrentPointOfInterest, isLoadingPoi } from '../../point-of-interest.selectors';

@Component({
  selector: 'oca-edit-point-of-interest-page',
  templateUrl: './edit-point-of-interest-page.component.html',
  styleUrls: ['./edit-point-of-interest-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EditPointOfInterestPageComponent implements OnInit {
  poi$: Observable<PointOfInterest | null>;
  isLoading$: Observable<boolean>;
  poiId: number;

  constructor(private store: Store,
              private matDialog: MatDialog,
              private translate: TranslateService,
              private route: ActivatedRoute) {
  }

  ngOnInit(): void {
    this.poiId = parseInt(this.route.snapshot.params.id, 10);
    this.store.dispatch(getPointOfInterest({ id: this.poiId }));
    this.isLoading$ = combineLatest([
      this.store.pipe(select(isLoadingPoi)),
      this.store.pipe(select(isPlaceTypesLoading)),
    ]).pipe(map(results => results.some(r => r)));
    this.poi$ = this.store.pipe(select(getCurrentPointOfInterest));
  }

  submit(data: CreatePointOfInterest) {
    this.store.dispatch(updatePointOfInterest({ id: this.poiId, data }));
  }

  deletePoi() {
    this.matDialog.open<SimpleDialogComponent, SimpleDialogData, SimpleDialogResult>(SimpleDialogComponent, {
      data: {
        ok: this.translate.instant('oca.Yes'),
        cancel: this.translate.instant('oca.Cancel'),
        title: this.translate.instant('oca.confirm_deletion'),
        message: this.translate.instant('oca.confirm_delete_poi'),
      },
    }).afterClosed().subscribe(result => {
      if (result?.submitted) {
        this.store.dispatch(deletePointOfInterest({ id: this.poiId }));
      }
    });
  }
}
