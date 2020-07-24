import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  EventEmitter,
  Input,
  OnChanges,
  Output,
  SimpleChanges,
} from '@angular/core';
import { NgForm } from '@angular/forms';
import { MatChipEvent } from '@angular/material/chips';
import { MatDialog, MatDialogConfig } from '@angular/material/dialog';
import { MatSelect, MatSelectChange } from '@angular/material/select';
import { TranslateService } from '@ngx-translate/core';
import {
  App,
  AppStatisticsMapping,
  BaseMedia,
  CreateNews,
  Gender,
  MediaType,
  NewsActionButton,
  NewsActionButtonType,
  NewsGroupType,
  NewsLocation,
  NewsOptions,
  NewsTargetAudience,
  UINewsActionButton,
} from '@oca/web-shared';
import { EASYMDE_OPTIONS } from '../../../../environments/config';
import { DEFAULT_AVATAR_URL } from '../../../consts';
import { BrandingSettings } from '../../../shared/interfaces/oca';
import { ServiceIdentityInfo } from '../../../shared/interfaces/rogerthat';
import { Loadable } from '../../../shared/loadable/loadable';
import { UploadedFileResult, UploadFileDialogComponent, UploadFileDialogConfig } from '../../../shared/upload-file';
import { GENDER_OPTIONS, NEWS_MEDIA_TYPE_OPTIONS } from '../../consts';
import {
  NewsAppMapPickerDialogComponent,
  NewsAppMapPickerDialogData,
} from '../news-app-map-picker-dialog/news-app-map-picker-dialog.component';

@Component({
  selector: 'oca-edit-news',
  templateUrl: './edit-news.component.html',
  styleUrls: ['./edit-news.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EditNewsComponent implements OnChanges {
  @Input() published: boolean;
  @Input() status: Loadable;
  @Input() apps: App[];
  @Input() appStatistics: AppStatisticsMapping;
  @Input() serviceInfo: ServiceIdentityInfo | null;
  @Input() options: NewsOptions | null;
  @Input() remainingBudget: string;
  @Input() brandingSettings: BrandingSettings | null;
  @Output() save = new EventEmitter<CreateNews>();
  @Output() regionalNewsToggled = new EventEmitter<boolean>();
  hasLocal = false;
  hasRegional = false;
  minDate = new Date();
  maxDate = new Date(this.minDate.getTime() + new Date(86400 * 29 * 1000).getTime());
  defaultAppId: string;
  appMapping: { [ key: string ]: App } = {};
  reach: {
    total: string;
    cost: string;
  };
  actionButton: UINewsActionButton | null = null;
  EASYMDE_OPTIONS = EASYMDE_OPTIONS;
  DEFAULT_AVATAR_URL = DEFAULT_AVATAR_URL;
  NewsActionButtonType = NewsActionButtonType;
  GENDERS = GENDER_OPTIONS;
  NEWS_MEDIA_TYPE_OPTIONS: { label: string; value: MediaType | null }[] = [];
  MediaType = MediaType;
  URL_PATTERN = '(https?:\\/\\/)?([\\w\\-])+\\.{1}([a-zA-Z]{2,63})([\\/\\w-]*)*\\/?\\??([^#\\n\\r]*)?#?([^\\n\\r]*)';
  hasGroupVisible = false;
  showGroupInfoDetails = false;
  selectedMediaType: MediaType | null = MediaType.IMAGE;

  constructor(private _matDialog: MatDialog,
              private _translate: TranslateService,
              private _changeDetectorRef: ChangeDetectorRef) {
  }

  private _newsItem: CreateNews;

  get newsItem() {
    return this._newsItem;
  }

  @Input() set newsItem(value: CreateNews) {
    this._newsItem = value;
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (this.options && this.newsItem?.action_button) {
      this.setActionButton(this.newsItem.action_button);
    }
    if (changes.newsItem?.currentValue) {
      this.groupTypeChanged();
      this.selectedMediaType = this.newsItem.media?.type ?? null;
    }
    if (changes.serviceInfo && this.serviceInfo) {
      this.defaultAppId = this.serviceInfo.default_app;
    }
    if ((changes.serviceInfo || changes.newsItem) && this.newsItem && this.serviceInfo) {
      this.hasLocal = this.newsItem.app_ids.includes(this.serviceInfo.default_app);
      this.hasRegional = !this.hasLocal || this.isRegional();
    }
    if (changes.apps && this.apps) {
      this.appMapping = {};
      for (const app of this.apps) {
        this.appMapping[ app.id ] = app;
      }
    }
    if (changes.options && this.options) {
      const mediaTypes = this.options.media_types;
      this.NEWS_MEDIA_TYPE_OPTIONS = NEWS_MEDIA_TYPE_OPTIONS.filter(o => o.value === null || mediaTypes.includes(o.value));
    }
  }

  actionButtonSelected() {
    this.newsItem = { ...this.newsItem, action_button: this.actionButton?.button ?? null };
  }

  compareActionButtons(toCompare: UINewsActionButton, selectedValue: UINewsActionButton | null) {
    if (!selectedValue) {
      return false;
    }
    return toCompare.type === selectedValue.type && toCompare.button.id === selectedValue.button.id;
  }

  setActionButton(button?: NewsActionButton | null) {
    if (!button) {
      this.actionButton = null;
      return;
    }
    if (this.options) {
      const actionButton = this.options.action_buttons.find(b => {
        switch (b.type) {
          case NewsActionButtonType.MENU_ITEM:
          case NewsActionButtonType.OPEN:
            return b.button.action === button.action;
          default:
            return b.button.id === button.id;
        }
      });
      if (!actionButton) {
        return;
      }
      this.actionButton = { ...actionButton, button };
      switch (this.actionButton.type) {
        case NewsActionButtonType.PHONE:
          this.actionButton.phone = button.action.split('tel://')[ 1 ] || button.action;
          break;
        case NewsActionButtonType.EMAIL:
          this.actionButton.email = button.action.split('mailto://')[ 1 ] || button.action;
          break;
        case NewsActionButtonType.MENU_ITEM:
          // After publishing an item, the tag is hashed. Ensure it isn't hashed twice by resetting it here.
          this.actionButton.button.action = `smi://${button.id}`;
          break;
      }
    }
  }

  updateButton(action: string) {
    if (this.actionButton) {
      const value = (action || '').trim();
      switch (this.actionButton.type) {
        case NewsActionButtonType.WEBSITE:
          if (value) {
            action = value.startsWith('http://') || value.startsWith('https://') ? value : `https://${value}`;
          }
          break;
        case NewsActionButtonType.PHONE:
          action = `tel://${value}`;
          break;
        case NewsActionButtonType.EMAIL:
          action = `mailto://${value}`;
          break;
        case NewsActionButtonType.OPEN:
          action = `open://${value}`;
          break;
        default:
          action = value;
      }
      this.newsItem = { ...this.newsItem, action_button: { ...this.actionButton.button, action } };
    } else {
      this.newsItem = { ...this.newsItem, action_button: null };
    }
    this.setActionButton(this.newsItem.action_button);
  }

  toggleScheduledAt() {
    this.newsItem = { ...this.newsItem, scheduled_at: this.newsItem.scheduled_at ? null : new Date() };
  }

  submit(form: NgForm) {
    if (form.form.valid) {
      const item = { ...this.newsItem, action_button: this.actionButton ? this.actionButton.button : null };
      this.save.emit(item);
    }
  }

  getSubmitButtonText() {
    if (this.newsItem.id) {
      return 'oca.Save';
    } else if (this.newsItem.scheduled_at) {
      return 'oca.schedule';
    } else {
      return 'oca.publish';
    }
  }

  toggleLocal() {
    const defaultAppId = (this.serviceInfo as ServiceIdentityInfo).default_app;
    let appIds: string[];
    if (this.hasLocal) {
      appIds = this.newsItem.app_ids.filter(a => a !== defaultAppId);
      this.hasRegional = true;
    } else {
      appIds = [...this.newsItem.app_ids, defaultAppId];
    }
    this.newsItem = { ...this.newsItem, app_ids: appIds };
    this.hasLocal = !this.hasLocal;
  }

  toggleRegional() {
    if (this.hasRegional) {
      this.newsItem = { ...this.newsItem, app_ids: [this.defaultAppId] };
      this.hasLocal = true;
    } else {
      this.newsItem = { ...this.newsItem, locations: null };
    }
    this.hasRegional = !this.hasRegional;
    this.regionalNewsToggled.emit(this.hasRegional);
  }

  regionalAppRemoved(event: MatChipEvent) {
    this.appsChanged(this.newsItem.app_ids.filter(a => a !== event.chip.value));
  }

  addApp($event: MatSelectChange, matSelect: MatSelect) {
    if (!this.newsItem.app_ids.includes($event.value)) {
      this.newsItem = { ...this.newsItem, app_ids: [...this.newsItem.app_ids, $event.value] };
    }
    matSelect.value = null;
  }

  appsChanged(apps: string[]) {
    this.newsItem = { ...this.newsItem, app_ids: apps };
  }

  openShop() {
    window.open('/flex/#/shop', '_blank');
  }

  toggleTargetAudience() {
    let targetAudience: NewsTargetAudience | null = null;
    if (!this.newsItem.target_audience) {
      targetAudience = { min_age: 0, max_age: 100, gender: Gender.MALE_OR_FEMALE, connected_users_only: false };
    }
    this.newsItem = { ...this.newsItem, target_audience: targetAudience };
  }

  toggleLocations() {
    let locations: NewsLocation | null = null;
    if (!this.newsItem.locations) {
      locations = { match_required: true, addresses: [], geo_addresses: [] };
    }
    this.newsItem = { ...this.newsItem, locations };
  }

  addAttachment() {
    const config: MatDialogConfig<UploadFileDialogConfig> = {
      data: {
        uploadPrefix: 'news',
        title: this._translate.instant('oca.add-attachment'),
        accept: 'image/*,application/pdf,video/mp4',
      },
    };
    this._matDialog.open(UploadFileDialogComponent, config).afterClosed().subscribe((result?: UploadedFileResult) => {
      if (result && this.actionButton) {
        this.actionButton = { ...this.actionButton, button: { ...this.actionButton.button, action: result.getUrl() } };
        this._changeDetectorRef.markForCheck();
      }
    });
  }

  openMapDialog() {
    if (this.published) {
      return;
    }
    const config: MatDialogConfig<NewsAppMapPickerDialogData> = {
      data: {
        appIds: this.newsItem.app_ids,
        apps: this.apps,
        appStatistics: this.appStatistics,
        defaultAppId: this.defaultAppId,
        mapUrl: (this.options as NewsOptions).regional.map_url,
      },
      panelClass: 'map-panel',
    };
    this._matDialog.open<NewsAppMapPickerDialogComponent, NewsAppMapPickerDialogData, string[]>(NewsAppMapPickerDialogComponent, config)
      .afterClosed().subscribe(result => {
      if (result) {
        this.appsChanged(result);
        this._changeDetectorRef.markForCheck();
      }
    });
  }

  groupTypeChanged() {
    this.hasGroupVisible = this.newsItem.group_type === NewsGroupType.POLLS;
    let visibleDate: Date | null;
    if (this.hasGroupVisible) {
      if (this.newsItem.group_visible_until) {
        visibleDate = new Date(this.newsItem.group_visible_until);
      } else {
        if (this.newsItem.scheduled_at) {
          visibleDate = this.newsItem.scheduled_at;
        } else {
          visibleDate = new Date();
        }
        // Default to 2 weeks after publishing the news item
        visibleDate.setDate(visibleDate.getDate() + 14);
      }
    } else {
      visibleDate = null;
    }
    this.newsItem = { ...this.newsItem, group_visible_until: visibleDate };
  }

  getMinVisibleUntil() {
    return this.newsItem.scheduled_at ? this.newsItem.scheduled_at : new Date();
  }

  getGroupName() {
    const group = (this.options as NewsOptions).groups.find(g => g.group_type === this.newsItem.group_type);
    return group ? group.name : '';
  }

  setButtonCaption($event: string | null) {
    this.newsItem = {
      ...this.newsItem,
      action_button: { ...this.newsItem.action_button as NewsActionButton, caption: ($event || '').trim() },
    };
    this.setActionButton(this.newsItem.action_button);
  }

  setMedia(media: BaseMedia | null) {
    this.newsItem = { ...this.newsItem, media };
  }

  private isRegional() {
    return this.newsItem.app_ids.filter(a => a !== 'rogerthat').length > 1;
  }
}
