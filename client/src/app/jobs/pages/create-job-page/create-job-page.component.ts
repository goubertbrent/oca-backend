import { ChangeDetectionStrategy, Component, OnInit, ViewEncapsulation } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { ContractType, EditJobOffer, JobMatchSource, JobStatus } from '../../jobs';
import { CreateJobOfferAction } from '../../jobs.actions';
import { isJobOfferLoading, JobsState } from '../../jobs.state';

@Component({
  selector: 'oca-create-job-page',
  templateUrl: './create-job-page.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class CreateJobPageComponent implements OnInit {
  loading$: Observable<boolean>;
  jobOffer: EditJobOffer;

  constructor(private store: Store<JobsState>) {
  }

  ngOnInit(): void {
    this.jobOffer = {
      contract: { type: ContractType.FULLTIME },
      job_domains: [],
      location: {
        postal_code: '',
        street_number: '',
        street: '',
        city: '',
        country_code: 'BE',
        geo_location: null,
      },
      details: '',
      employer: { name: '' },
      function: { title: '', description: '' },
      status: JobStatus.NEW,
      start_date: null,
      profile: '',
      contact_information: {
        email: '',
        phone_number: '',
      },
      match: {
        source: JobMatchSource.NO_MATCH,
        platform: null,
      },
    };
    this.loading$ = this.store.pipe(select(isJobOfferLoading));
  }

  onSubmit($event: EditJobOffer) {
    this.store.dispatch(new CreateJobOfferAction($event));
  }
}
