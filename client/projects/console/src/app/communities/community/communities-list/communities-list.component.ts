import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { FormControl, FormGroup, Validators } from '@angular/forms';
import { Observable, Subject } from 'rxjs';
import { CommunityService } from '../../community.service';
import { Community } from '../communities';

@Component({
  selector: 'oca-communities-list',
  templateUrl: './communities-list.component.html',
  styleUrls: ['./communities-list.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CommunitiesListComponent implements OnInit {
  countryFormControl = new FormControl('BE', Validators.required);
  formGroup = new FormGroup({
    country: this.countryFormControl,
  });
  countries$: Observable<{ code: string; name: string; }[]>;
  communities$ = new Subject<Community[]>();

  constructor(private communityService: CommunityService,
              private changeDetectionRef: ChangeDetectorRef) {
  }

  ngOnInit(): void {
    this.countries$ = this.communityService.getCountries();
    this.fetchCommunities(this.countryFormControl.value);
    this.countryFormControl.valueChanges.subscribe(country => {
      this.fetchCommunities(country);
    });
  }

  fetchCommunities(country: string) {
    this.communityService.getCommunities(country).subscribe(communities => {
      this.communities$.next(communities);
      this.changeDetectionRef.markForCheck();
    });
  }

}
