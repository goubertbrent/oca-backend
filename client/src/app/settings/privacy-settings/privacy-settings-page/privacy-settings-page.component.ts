import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { MatSlideToggleChange } from '@angular/material/slide-toggle';
import { updateItem } from '../../../shared/util';
import { PrivacySettings } from '../../service-info/service-info';
import { SettingsService } from '../../settings.service';

@Component({
  selector: 'oca-privacy-settings-page',
  templateUrl: './privacy-settings-page.component.html',
  styleUrls: ['./privacy-settings-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PrivacySettingsPageComponent implements OnInit {
  settings: PrivacySettings[] = [];

  constructor(private service: SettingsService,
              private changeDetectorRef: ChangeDetectorRef) {
  }

  ngOnInit(): void {
    this.service.getPrivacySettings().subscribe(result => {
      this.settings = result;
      this.changeDetectorRef.markForCheck();
    });
  }

  settingToggled(item: PrivacySettings, $event: MatSlideToggleChange) {
    const setting = { ...item, enabled: $event.checked };
    this.settings = updateItem(this.settings, setting, 'type');
    this.service.savePrivacySettings(setting).subscribe();
  }
}
