import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { IFormBuilder, IFormGroup } from '@rxweb/types';
import { EmbeddedApp } from '../../../interfaces';
import { COUNTRIES } from '../../countries';
import { AppFeature, CreateCommunity, SimpleApp } from '../communities';

@Component({
  selector: 'rcc-community-form',
  templateUrl: './community-form.component.html',
  styleUrls: ['./community-form.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CommunityFormComponent implements OnInit {
  @Input() apps: SimpleApp[];
  @Input() embeddedApps: EmbeddedApp[];
  @Output() saved = new EventEmitter<CreateCommunity>();
  formGroup: IFormGroup<CreateCommunity>;
  countries = COUNTRIES;
  features = [
    { label: 'Jobs', value: AppFeature.JOBS },
    { label: 'News: videos in feed', value: AppFeature.NEWS_VIDEO },
    { label: 'News: location filter', value: AppFeature.NEWS_LOCATION_FILTER },
    { label: 'News: city must review all merchant news', value: AppFeature.NEWS_REVIEW },
    { label: 'News: regional news', value: AppFeature.NEWS_REGIONAL },
  ];
  private formBuilder: IFormBuilder;

  constructor(formBuilder: FormBuilder) {
    this.formBuilder = formBuilder;
  }

  @Input() set loading(value: boolean) {
    if (this.formGroup) {
      if (value) {
        this.formGroup.disable();
      } else {
        this.formGroup.enable();
      }
    }
  }

  private _community: CreateCommunity;

  @Input() set community(community: CreateCommunity) {
    this._community = community;
    if (this.formGroup) {
      this.formGroup.patchValue(community);
    }
  }

  ngOnInit(): void {
    this.formGroup = this.formBuilder.group<CreateCommunity>({
      auto_connected_services: [[]],
      country: [''],
      name: ['', Validators.required],
      default_app: ['', Validators.required],
      embedded_apps: [[]],
      main_service: [''],
      demo: [false],
      signup_enabled: [false],
      features: [[AppFeature.NEWS_VIDEO, AppFeature.JOBS]],
    });
    if (this._community) {
      // Since the formGroup might not have been initialized the moment the community was set,
      // set it here as well to ensure that the form is hydrated.
      this.formGroup.patchValue(this._community);
    }
  }

  save() {
    if (this.formGroup.valid) {
      // tslint:disable-next-line:no-non-null-assertion
      this.saved.emit(this.formGroup.value!!);
    }
  }
}
