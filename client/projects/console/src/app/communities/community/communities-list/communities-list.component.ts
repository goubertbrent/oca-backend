import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { FormControl, FormGroup, Validators } from '@angular/forms';
import { select, Store } from '@ngrx/store';
import { IFormControl } from '@rxweb/types';
import { Observable } from 'rxjs';
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
export class CommunitiesListComponent implements OnInit {
  countryFormControl = new FormControl('BE', Validators.required) as IFormControl<string>;
  formGroup = new FormGroup({
    country: this.countryFormControl,
  });
  countries$: Observable<{ code: string; name: string; }[]>;
  communities$: Observable<Community[]>;

  constructor(private communityService: CommunityService,
              private store: Store) {
  }

  ngOnInit(): void {
    this.store.dispatch(loadCommunities({ country: this.countryFormControl.value! }));
    this.countries$ = this.communityService.getCountries();
    this.communities$ = this.store.pipe(select(getCommunities));
    this.countryFormControl.valueChanges.subscribe(country => {
      this.store.dispatch(loadCommunities({ country: country! }));
    });
  }

  deleteCommunity(id: number) {
    this.store.dispatch(deleteCommunity({ id }));
  }
}
