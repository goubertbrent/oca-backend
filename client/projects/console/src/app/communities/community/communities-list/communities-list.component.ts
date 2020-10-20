import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { FormControl, FormGroup, Validators } from '@angular/forms';
import { select, Store } from '@ngrx/store';
import { IFormControl } from '@rxweb/types';
import { Observable, Subject } from 'rxjs';
import { distinctUntilChanged, takeUntil } from 'rxjs/operators';
import { getCommunities } from '../../communities.selectors';
import { deleteCommunity, loadCommunities } from '../../community.actions';
import { CommunityService } from '../../community.service';
import { Community } from '../communities';

@Component({
  selector: 'rcc-communities-list',
  templateUrl: './communities-list.component.html',
  styleUrls: ['./communities-list.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CommunitiesListComponent implements OnInit, OnDestroy {
  countryFormControl = new FormControl('BE') as IFormControl<string>;
  formGroup = new FormGroup({
    country: this.countryFormControl,
  });
  countries$: Observable<{ code: string; name: string; }[]>;
  communities$: Observable<Community[]>;

  private destroyed$ = new Subject();

  constructor(private communityService: CommunityService,
              private store: Store) {
  }

  ngOnInit(): void {
    this.store.dispatch(loadCommunities({ country: this.countryFormControl.value }));
    this.countries$ = this.communityService.getCountries();
    this.communities$ = this.store.pipe(select(getCommunities));
    this.countryFormControl.valueChanges.pipe(distinctUntilChanged(), takeUntil(this.destroyed$)).subscribe(country => {
      this.store.dispatch(loadCommunities({ country }));
    });
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  deleteCommunity(id: number) {
    this.store.dispatch(deleteCommunity({ id }));
  }
}
