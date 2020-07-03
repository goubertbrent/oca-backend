import { ChangeDetectionStrategy, Component, OnInit, ViewEncapsulation } from '@angular/core';
import { Platform } from '@ionic/angular';

@Component({
  selector: 'app-back-button',
  templateUrl: './back-button.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class BackButtonComponent implements OnInit {
  backButtonIcon = 'arrow-back';

  constructor(private platform: Platform) {
  }

  ngOnInit() {
    const isIOS = this.platform.is('ios');
    let icon: string;
    if (isIOS) {
      if (rogerthat.menuItem?.hashedTag) {
        icon = 'menu';
      } else {
        icon = 'chevron-back';
      }
    } else {
      icon = 'arrow-back';
    }
    this.backButtonIcon = icon;
  }

  exit() {
    rogerthat.app.exit();
  }
}
