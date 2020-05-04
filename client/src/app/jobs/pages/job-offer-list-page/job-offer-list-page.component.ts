import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { JobOfferDetails, JobStatus } from '../../jobs';
import { GetJobOfferListAction } from '../../jobs.actions';
import { areJobOffersListLoading, getJobOffersList, JobsState } from '../../jobs.state';

interface JobList {
  title: string;
  items: JobOfferDetails[];
  card?: {
    description: string;
    actionButton?: {
      route: string;
      label: string;
    }
  };
}

@Component({
  selector: 'oca-job-offer-list-page',
  templateUrl: './job-offer-list-page.component.html',
  styleUrls: ['./job-offer-list-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class JobOfferListPageComponent implements OnInit {
  loading$: Observable<boolean>;
  jobLists$: Observable<JobList[]>;
  indexes = {
    [ JobStatus.NEW ]: 0,
    [ JobStatus.ONGOING ]: 1,
    [ JobStatus.HIDDEN ]: 2,
    [ JobStatus.DELETED ]: 2,  // shouldn't be returned by server
  };

  constructor(private store: Store<JobsState>) {
    this.store.dispatch(new GetJobOfferListAction());
  }

  ngOnInit(): void {
    this.jobLists$ = this.store.pipe(select(getJobOffersList), map(offers => {
      const lists: JobList[] = [{
        title: 'oca.drafts',
        items: [],
        card: {
          description: 'oca.create_new_job_info',
          actionButton: {
            route: '/jobs/create',
            label: 'oca.create',
          },
        },
      }, {
        title: 'oca.active',
        items: [],
        card:{
          description: 'oca.active_jobs_info',
        }
      }, {
        title: 'oca.inactive',
        items: [],
        card: {
          description: 'oca.inactive_jobs_info'
        }
      }];
      for (const offer of offers) {
        lists[ this.indexes[ offer.offer.status ] ].items.push(offer);
      }
      return lists;
    }));
    this.loading$ = this.store.pipe(select(areJobOffersListLoading));
  }
}
