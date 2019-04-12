import { STEPPER_GLOBAL_OPTIONS } from '@angular/cdk/stepper';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnChanges,
  Output,
  QueryList,
  SimpleChanges,
  ViewChild,
  ViewChildren,
} from '@angular/core';
import { NgForm } from '@angular/forms';
import { MatDialog, MatDialogConfig, MatStep } from '@angular/material';
import { TranslateService } from '@ngx-translate/core';
import { Budget } from '../../../shared/billing/billing';
import { COST_PER_VIEW, VIEWS_PER_CENT } from '../../../shared/billing/consts';
import { SimpleDialogComponent, SimpleDialogData } from '../../../shared/dialog/simple-dialog.component';
import { UploadedFile } from '../../../shared/images';
import { Loadable } from '../../../shared/loadable/loadable';
import { AppStatistics, ServiceIdentityInfo } from '../../../shared/rogerthat';
import { UploadImageDialogComponent, UploadImageDialogConfig } from '../../../shared/upload-image-dialog/upload-image-dialog.component';
import { GENDERS } from '../../consts';
import {
  CreateNews,
  Gender,
  MediaType,
  NewsActionButton,
  NewsActionButtonType,
  NewsItemType,
  NewsOptions,
  NewsSettingsTag,
  SimpleApp,
  UINewsActionButton,
} from '../../interfaces';

interface AppWithUsers extends SimpleApp {
  reach: string;
}

@Component({
  selector: 'oca-edit-news',
  templateUrl: './edit-news.component.html',
  styleUrls: [ './edit-news.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [ {
    provide: STEPPER_GLOBAL_OPTIONS, useValue: { showError: true },
  } ],
})
export class EditNewsComponent implements OnChanges {
  @ViewChildren(MatStep) steps: QueryList<MatStep>;
  @ViewChildren(NgForm) forms: QueryList<NgForm>;
  @ViewChild('scheduledTime') scheduledTime: ElementRef<HTMLInputElement>;

  @Input() set newsItem(value: CreateNews) {
    if (this._newsItem) {
      this.changed.emit(value);
    }
    this._newsItem = value;
  }

  get newsItem() {
    return this._newsItem;
  }

  @Input() currency = '€';
  @Input() status: Loadable;
  @Input() options: Loadable<NewsOptions>;
  @Input() published = false;
  @Input() apps: Loadable<SimpleApp[]>;
  @Input() appStats: Loadable<AppStatistics[]>;
  @Input() serviceInfo: Loadable<ServiceIdentityInfo>;
  @Input() actionButtons: Loadable<UINewsActionButton[]>;
  @Input() budget: Loadable<Budget>;

  @Output() save = new EventEmitter<CreateNews>();
  @Output() changed = new EventEmitter<CreateNews>();
  @Output() chargeBudget = new EventEmitter();
  NewsItemType = NewsItemType;
  GENDERS = GENDERS;

  scheduledDate: Date;
  minDate = new Date();
  maxDate = new Date(this.minDate.getTime() + 86400 * 29 * 1000);
  actionButton: UINewsActionButton | null = null;
  NewsActionButtonType = NewsActionButtonType;
  localNewsEnabled = true;
  regionalNewsEnabled = false;
  appsWithStats: AppWithUsers[] = [];
  estimatedReach = '';
  estimatedCost = '';
  budgetLeft = '';
  hasScheduledAt = false;
  hasTargetAudience = false;

  private _newsItem: CreateNews;

  constructor(private _matDialog: MatDialog,
              private _translate: TranslateService,
              private _changeDetectorRef: ChangeDetectorRef) {
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (this.actionButtons.data && this.newsItem && this.newsItem.action_button) {
      this.setActionButton(this.newsItem.action_button);
    }
    if (changes.newsItem && changes.newsItem.currentValue) {
      const news: CreateNews = changes.newsItem.currentValue;
      if (news.scheduled_at > 0) {
        this.hasScheduledAt = true;
        this.scheduledDate = new Date(changes.newsItem.currentValue.scheduled_at * 1000);
      }
      this.updateDate();
      this.setTimeInput();
      this.hasTargetAudience = this.newsItem.target_audience !== null;
    }
    if (changes.newsItem || changes.serviceInfo) {
      if (this.newsItem && this.serviceInfo.data) {
        this.localNewsEnabled = this.newsItem.app_ids.includes(this.serviceInfo.data.default_app);
        this.setRegionalNewsEnabled();
      }
    }
    if ((changes.apps || changes.appStats) && (this.appStats && this.appStats.data && this.apps && this.apps.data)) {
      const usersPerApp: { [ key: string ]: number } = {};
      for (const stat of this.appStats.data) {
        usersPerApp[ stat.app_id ] = stat.total_user_count;
      }
      this.appsWithStats = this.apps.data.map(app => ({
        id: app.id,
        name: app.name,
        reach: this.getEstimatedReach(usersPerApp[ app.id ]),
      }));
      this.calculateTotals();
    }
    if ((changes.budget || changes.options) && (this.budget.data && this.options.data)) {
      this.setBudget(this.budget.data, this.options.data);
    }
  }

  showImageDialog() {
    const config: MatDialogConfig<UploadImageDialogConfig> = {
      data: {
        type: 'news',
        title: this._translate.instant('oca.image'),
      },
    };
    this._matDialog.open(UploadImageDialogComponent, config).afterClosed().subscribe((result?: UploadedFile) => {
      if (result) {
        this.newsItem = {
          ...this.newsItem,
          media: { type: MediaType.IMAGE, content: result.url },
        };
        this._changeDetectorRef.markForCheck();
      }
    });
  }

  actionButtonSelected() {
    if (this.actionButtons.data && this.actionButton) {
      this.newsItem = { ...this.newsItem, action_button: this.actionButton.button };
    }
  }

  compareActionButtons(toCompare: UINewsActionButton, selectedValue: UINewsActionButton | null) {
    if (!selectedValue) {
      return false;
    }
    return toCompare.type === selectedValue.type && toCompare.button.id === selectedValue.button.id;
  }

  setActionButton(button?: NewsActionButton) {
    if (!button) {
      this.actionButton = null;
      return;
    }
    if (this.actionButtons.data) {
      this.actionButton = this.actionButtons.data.find(b => b.button.id === button.id) || null;
      if (!this.actionButton) {
        return;
      }
      switch (this.actionButton.type) {
        case NewsActionButtonType.PHONE:
          this.actionButton.phone = button.action.split('tel://')[ 0 ];
          break;
        case NewsActionButtonType.EMAIL:
          this.actionButton.email = button.action.split('mailto://')[ 0 ];
          break;
        default:
          this.actionButton.button.action = button.action;
      }
    }
  }

  updateButton() {
    if (this.actionButton) {
      switch (this.actionButton.type) {
        case NewsActionButtonType.PHONE:
          this.actionButton.button.action = 'tel://' + this.actionButton.phone;
          break;
        case NewsActionButtonType.EMAIL:
          this.actionButton.button.action = 'mailto://' + this.actionButton.email;
          break;
      }
    }
  }

  toggleScheduledAt() {
    if (this.hasScheduledAt) {
      this.scheduledDate = new Date();
      this.updateDate();
      this.setTimeInput();
    } else {
      this.newsItem = { ...this.newsItem, scheduled_at: 0 };
    }
  }

  updateDate() {
    let scheduledAt: Date | null = null;
    if (this.scheduledDate) {
      scheduledAt = new Date(this.scheduledDate.getTime());
      const timeDate = this.scheduledTime.nativeElement.valueAsDate as Date | undefined;
      if (timeDate) {
        scheduledAt.setHours(timeDate.getUTCHours());
        scheduledAt.setMinutes(timeDate.getUTCMinutes());
      }
    }
    this.newsItem = { ...this.newsItem, scheduled_at: scheduledAt ? scheduledAt.getTime() / 1000 : 0 };
  }

  private setTimeInput() {
    if (this.scheduledTime && this.scheduledDate) {
      const d = new Date(0);
      d.setUTCHours(this.scheduledDate.getHours());
      d.setUTCMinutes(this.scheduledDate.getMinutes());
      this.scheduledTime.nativeElement.valueAsDate = d;
    }
  }

  localNewsToggled() {
    const defaultAppId = (this.serviceInfo.data as ServiceIdentityInfo).default_app;
    if (this.localNewsEnabled) {
      this.newsItem = { ...this.newsItem, app_ids: [ ...this.newsItem.app_ids, defaultAppId ] };
    } else {
      this.newsItem = { ...this.newsItem, app_ids: this.newsItem.app_ids.filter(a => a !== defaultAppId) };
      this.regionalNewsEnabled = true;
    }
  }

  regionalNewsToggled() {
    const defaultAppId = (this.serviceInfo.data as ServiceIdentityInfo).default_app;
    if (!this.regionalNewsEnabled) {
      this.newsItem = { ...this.newsItem, app_ids: [ defaultAppId ] };
      this.localNewsEnabled = true;
    }
  }

  calculateTotals() {
    const totalUsers = (this.appStats.data as AppStatistics[]).reduce((result, app) => {
      if (this.newsItem.app_ids.includes(app.app_id)) {
        return result + app.total_user_count;
      }
      return result;
    }, 0);
    this.estimatedReach = this.getEstimatedReach(totalUsers);
    this.estimatedCost = this.getEstimatedCost(totalUsers);
  }

  propertyChanged(property: keyof CreateNews, value: any) {
    this.newsItem = { ...this.newsItem, [ property ]: value };
  }

  private setRegionalNewsEnabled() {
    this.regionalNewsEnabled = this.newsItem.app_ids.length > 1 || !this.localNewsEnabled;
  }

  private getEstimatedReach(reach: number) {
    // 1/8th - 1/4th of all users
    return `${Math.round(reach * 0.125)} ~ ${Math.round(reach * 0.25)}`;
  }

  private getEstimatedCost(reach: number) {
    const maxCost = reach * COST_PER_VIEW;
    // 1/8th - 1/4th of all users
    return `${this.currency} ${(maxCost * 0.125).toFixed(2)} ~ ${this.currency} ${(maxCost * 0.25).toFixed(2)}`;
  }

  private setBudget(budget: Budget, options: NewsOptions) {
    if (options.news_settings.tags.includes(NewsSettingsTag.FREE_REGIONAL_NEWS)) {
      this.budgetLeft = this._translate.instant('oca.unlimited');
    } else {
      this.budgetLeft = `${budget.balance * VIEWS_PER_CENT} ${this._translate.instant('oca.views')}`;
    }
  }

  targetAudienceToggled() {
    this.newsItem = {
      ...this.newsItem, target_audience: this.hasTargetAudience ? {
        connected_users_only: false,
        gender: Gender.MALE_OR_FEMALE,
        max_age: 125,
        min_age: 0,
      } : null,
    };
  }

  saveNews() {
    const formArray = this.forms.toArray();
    for (let i = 0; i < formArray.length; i++) {
      const form = formArray[ i ];
      if (form.invalid) {
        this.showFormError(i);
        return;
      }
    }
    this.save.emit(this.newsItem);
  }

  /**
   * Selects the step containing the invalid form field and shows an error dialog
   */
  private showFormError(index: number) {
    const step = this.steps.toArray()[ index ];
    step.hasError = true;
    step.select();
    const config: MatDialogConfig<SimpleDialogData> = {
      data: {
        title: this._translate.instant('oca.error'),
        message: this._translate.instant('oca.cannot_save_message_fields_invalid'),
        ok: this._translate.instant('oca.ok'),
      },
    };
    this._matDialog.open(SimpleDialogComponent, config);
  }
}
