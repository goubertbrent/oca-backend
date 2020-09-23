import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { FormArray, FormBuilder, Validators } from '@angular/forms';
import { select, Store } from '@ngrx/store';
import { ErrorService, NewsGroupType } from '@oca/web-shared';
import { IFormArray, IFormBuilder, IFormGroup } from '@rxweb/types';
import { Observable, Subject } from 'rxjs';
import { GetGlobalConfigAction } from '../../../shared/shared.actions';
import { NewsCommunity, RssScraper, RssSettings } from '../../news';
import { GetCommunities } from '../../news.actions';
import { NewsService } from '../../news.service';
import { getNewsCommunities } from '../../news.state';

@Component({
  selector: 'oca-news-settings-page',
  templateUrl: './news-settings-page.component.html',
  styleUrls: ['./news-settings-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NewsSettingsPageComponent implements OnInit, OnDestroy {
  // This page is for admins only
  newsGroups = [
    { type: NewsGroupType.CITY, label: 'City' },
    { type: NewsGroupType.EVENTS, label: 'Events' },
    { type: NewsGroupType.POLLS, label: 'Polls' },
    { type: NewsGroupType.PRESS, label: 'Press' },
    { type: NewsGroupType.PROMOTIONS, label: 'Promotions' },
    { type: NewsGroupType.TRAFFIC, label: 'Traffic' },
    { type: NewsGroupType.PUBLIC_SERVICE_ANNOUNCEMENTS, label: 'Public service announcements' },
  ];
  communities$: Observable<NewsCommunity[]>;

  formGroup: IFormGroup<RssSettings>;
  scraperFormGroup: IFormGroup<RssScraper>;
  editingScraper: RssScraper | null = null;
  editingIndex = -1;

  private formBuilder: IFormBuilder;
  private destroyed$ = new Subject();

  constructor(formBuilder: FormBuilder,
              private store: Store,
              private errorService: ErrorService,
              private newsService: NewsService) {
    this.formBuilder = formBuilder;
  }

  ngOnInit(): void {
    this.formGroup = this.formBuilder.group<RssSettings>({
      notify: [false],
      scrapers: this.formBuilder.array<RssScraper>([]),
    });
    this.scraperFormGroup = this.newScraperGroup();
    this.store.dispatch(new GetCommunities());
    this.communities$ = this.store.pipe(select(getNewsCommunities));
    this.newsService.getRssSettings().subscribe(settings => {
      for (const scraper of settings.scrapers) {
        this.scrapers.push(this.newScraperGroup());
      }
      this.formGroup.patchValue(settings);
    });
  }

  get scrapers(){
    return this.formGroup.controls.scrapers as IFormArray<RssScraper>;
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  editScraper(scraper: RssScraper) {
    this.editingScraper = scraper;
    this.editingIndex = this.formGroup.value!!.scrapers.indexOf(scraper);
    this.scraperFormGroup.setValue(scraper);
  }

  saveScraper() {
    if (this.editingIndex === -1) {
        const group = this.newScraperGroup();
        group.setValue(this.scraperFormGroup.value!!);
        this.scrapers.push(group);
    } else{
      this.scrapers.at(this.editingIndex).setValue(this.scraperFormGroup.value);
    }
    this.editingScraper = null;
    this.editingIndex = -1 ;
    this.scraperFormGroup.reset();
    this.save();
  }

  save() {
    this.newsService.saveRssSettings(this.formGroup.value!!).subscribe({
      error: err => {
        this.errorService.showErrorDialog(this.errorService.getMessage(err));
      }
  });
  }

  removeScraper(index: number) {
    (this.scrapers as FormArray).removeAt(index);
    this.save();
  }

  private newScraperGroup() {
    return this.formBuilder.group<RssScraper>({
      url: [null, Validators.required],
      community_ids: [[]],
      group_type: [NewsGroupType.CITY],
    });
  }

  addRss() {
    this.editingScraper = {
      url: '',
      group_type: NewsGroupType.CITY,
      community_ids: [],
    };
    this.scraperFormGroup.setValue(this.editingScraper);
    this.editingIndex = -1;
  }
}
