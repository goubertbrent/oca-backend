import { ChangeDetectionStrategy, Component, OnInit, ViewEncapsulation } from '@angular/core';
import { Router } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { Observable } from 'rxjs';
import { map, take } from 'rxjs/operators';
import { CreateNews } from '../../../news/interfaces';
import { NewsGroupType } from '../../../shared/interfaces/rogerthat';
import { deepCopy, filterNull } from '../../../shared/util';
import { EditJobOffer, JobOffer } from '../../jobs';
import { UpdateJobOfferAction } from '../../jobs.actions';
import { getJobOffer, isJobOfferLoading, JobsState } from '../../jobs.state';

@Component({
  selector: 'oca-edit-job-page',
  templateUrl: './edit-job-page.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class EditJobPageComponent implements OnInit {
  loading$: Observable<boolean>;
  jobOffer$: Observable<EditJobOffer | JobOffer>;
  editJobOffer$: Observable<EditJobOffer>;
  jobId: number;
  externalId: number;

  constructor(private store: Store<JobsState>,
              private translate: TranslateService,
              private router: Router) {
  }

  ngOnInit(): void {
    this.jobOffer$ = this.store.pipe(select(getJobOffer), filterNull());
    this.editJobOffer$ = this.jobOffer$.pipe(map(offer => {
      if ('id' in offer) {
        const { id, internal_id, ...createOffer } = offer;
        this.jobId = id;
        this.externalId = internal_id;
        return deepCopy(createOffer);
      }
      return deepCopy(offer);
    })) as Observable<EditJobOffer>;
    this.loading$ = this.store.pipe(select(isJobOfferLoading));
  }

  onSubmit($event: EditJobOffer) {
    this.store.dispatch(new UpdateJobOfferAction({ id: this.jobId, offer: $event }));
  }

  createNews() {
    this.editJobOffer$.pipe(take(1)).subscribe((jobOffer) => {
      const message = `${jobOffer.function.description}`;
      const buttonValue = JSON.stringify({ action_type: 'job', action: this.externalId.toString() });
      const data: Partial<CreateNews> = {
        action_button: {
          action: `open://${buttonValue}`,
          caption: this.translate.instant('oca.apply_for_job'),
          id: 'job',
        },
        message,
        title: jobOffer.function.title,
        type: 1,
        group_type: NewsGroupType.PROMOTIONS,
      };
      localStorage.setItem('news.item', JSON.stringify(data));
      this.router.navigateByUrl('/news/create');
      window.top.postMessage({ type: 'oca.set_navigation', path: 'news' }, '*');
    });
  }
}
