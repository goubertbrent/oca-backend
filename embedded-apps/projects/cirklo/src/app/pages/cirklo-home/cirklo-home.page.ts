import { ChangeDetectionStrategy, Component, ViewEncapsulation } from '@angular/core';

type Tab = { label: string; route: string; iconName: string | null; iconSrc: string | null };

@Component({
  selector: 'cirklo-home',
  templateUrl: './cirklo-home.page.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class CirkloHomePage {
  tabs: Tab[] = [
    { label: 'app.cirklo.vouchers', route: 'vouchers', iconName: null, iconSrc: '/assets/icon/business-and-finance.svg' },
    { label: 'app.cirklo.merchants', route: 'merchants', iconName: 'cart', iconSrc: null },
    { label: 'app.cirklo.info', route: 'info', iconName: null, iconSrc: '/assets/icon/cirklo_light_white_filled.svg' },
  ];
  pageTitle = '';

  setTitle({ tab }: { tab: string }) {
    this.pageTitle = this.tabs.find(t => t.route === tab)?.label ?? '';
  }
}
