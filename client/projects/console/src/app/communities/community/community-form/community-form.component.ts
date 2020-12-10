import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { IFormBuilder, IFormGroup } from '@rxweb/types';
import { EmbeddedApp } from '../../../interfaces';
import { COUNTRIES } from '../../countries';
import { AppFeature, CreateCommunity, CustomizationFeature, SimpleApp } from '../communities';

@Component({
  selector: 'rcc-community-form',
  templateUrl: './community-form.component.html',
  styleUrls: ['./community-form.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CommunityFormComponent {
  @Input() apps: SimpleApp[];
  @Input() embeddedApps: EmbeddedApp[];
  @Output() saved = new EventEmitter<CreateCommunity>();
  formGroup: IFormGroup<CreateCommunity>;
  countries = COUNTRIES;
  features = [
    { label: 'Events: Show merchants in feed from main service', value: AppFeature.EVENTS_SHOW_MERCHANTS },
    { label: 'Jobs', value: AppFeature.JOBS },
    { label: 'Loyalty', value: AppFeature.LOYALTY },
    { label: 'News: videos in feed', value: AppFeature.NEWS_VIDEO },
    { label: 'News: location filter', value: AppFeature.NEWS_LOCATION_FILTER },
    { label: 'News: city must review all merchant news', value: AppFeature.NEWS_REVIEW },
    { label: 'News: regional news', value: AppFeature.NEWS_REGIONAL },
  ];
  customizationFeatures = [
    { label: 'Store home address in user data', value: CustomizationFeature.HOME_ADDRESS_IN_USER_DATA },
  ];
  private formBuilder: IFormBuilder;

  constructor(formBuilder: FormBuilder) {
    const fb = formBuilder as IFormBuilder;
    this.formGroup = fb.group<CreateCommunity>({
      auto_connected_services: [[]],
      country: [''],
      name: ['', Validators.required],
      default_app: ['', Validators.required],
      embedded_apps: [[]],
      main_service: [''],
      demo: [false],
      signup_enabled: [false],
      features: [[AppFeature.NEWS_VIDEO]],
    });
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

  @Input() set community(community: CreateCommunity) {
    if (community) {
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
      customization_features: [[]],
    });
    if (this._community) {
      // Since the formGroup might not have been initialized the moment the community was set,
      // set it here as well to ensure that the form is hydrated.
      this.formGroup.patchValue(this._community);
    }
  }

  save() {
    if (this.formGroup.valid) {
      this.saved.emit(this.formGroup.value!!);
    }
  }
}
