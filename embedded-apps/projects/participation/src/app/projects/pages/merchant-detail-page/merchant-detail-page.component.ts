import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { encodeURIObject, filterNull } from '../../../util';
import { AppMerchant } from '../../projects';
import { GetMerchantAction } from '../../projects.actions';
import { getMerchantDetails, ProjectsState } from '../../projects.state';

@Component({
  selector: 'pp-merchant-detail-page',
  templateUrl: './merchant-detail-page.component.html',
  styleUrls: ['./merchant-detail-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MerchantDetailPageComponent implements OnInit {
  merchant$: Observable<AppMerchant | null>;
  mapsUrl$: Observable<string>;
  openingHoursExpanded = false;
  expandIcon = 'md-arrow-dropdown';
  fullscreenActive = false;
  fullscreenImage: string | null = null;

  constructor(private store: Store<ProjectsState>,
              private route: ActivatedRoute) {
  }

  ngOnInit() {
    const merchantId = parseInt(this.route.snapshot.params.id, 10);
    this.store.dispatch(new GetMerchantAction({ id: merchantId }));
    this.merchant$ = this.store.pipe(select(getMerchantDetails));
    this.mapsUrl$ = this.merchant$.pipe(filterNull(), map(m => {
      const params: any = {
        api: 1,
        destination: m.formatted_address,
      };
      if (m.place_id) {
        params.destination_place_id = m.place_id;
      }
      return `https://www.google.com/maps/dir/?${encodeURIObject(params)}`;
    }));
  }

  toggleOpeningHours() {
    this.openingHoursExpanded = !this.openingHoursExpanded;
    this.expandIcon = this.openingHoursExpanded ? 'md-arrow-dropup' : 'md-arrow-dropdown';
  }

  showFullScreen(image: string) {
    this.fullscreenImage = image;
    this.fullscreenActive = true;
  }

  closeOverlay() {
    this.fullscreenActive = false;
    setTimeout(() => {
      this.fullscreenImage = null;
    }, 700);
  }
}
