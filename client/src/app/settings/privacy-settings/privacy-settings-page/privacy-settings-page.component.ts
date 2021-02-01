import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { MatSlideToggleChange } from '@angular/material/slide-toggle';
import { updateItem } from '../../../shared/util';
import { PrivacySettings, PrivacySettingsGroup } from '../../service-info/service-info';
import { SettingsService } from '../../settings.service';

@Component({
  selector: 'oca-privacy-settings-page',
  templateUrl: './privacy-settings-page.component.html',
  styleUrls: ['./privacy-settings-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PrivacySettingsPageComponent implements OnInit {
  settingsGroups: PrivacySettingsGroup[] = [];

  constructor(private service: SettingsService,
              private changeDetectorRef: ChangeDetectorRef) {
  }

  ngOnInit(): void {
    this.service.getPrivacySettings().subscribe(result => {
      this.settingsGroups = result;
      this.changeDetectorRef.markForCheck();
    });
  }

  settingToggled(item: PrivacySettings, $event: MatSlideToggleChange) {
    const setting = { ...item, enabled: $event.checked };
    for (const group of this.settingsGroups){
      if (group.items.includes(item)) {
        group.items = updateItem(group.items, setting, 'type');
      }
    }
    this.service.savePrivacySettings(setting).subscribe();
  }
}
