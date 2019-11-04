import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { Platform } from '@ionic/angular';

@Component({
  selector: 'app-back-button',
  templateUrl: './back-button.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BackButtonComponent implements OnInit {
  backButtonIcon = 'arrow-left';

  constructor(private platform: Platform) {
  }

  ngOnInit() {
    const isIOS = this.platform.is('ios');
    let icon: string;
    if (isIOS && rogerthat.menuItem && rogerthat.menuItem.hashedTag) {
      icon = 'menu';
    } else {
      icon = 'arrow-back';
    }
    this.backButtonIcon = icon;
  }

  exit() {
    rogerthat.app.exit();
  }
}
