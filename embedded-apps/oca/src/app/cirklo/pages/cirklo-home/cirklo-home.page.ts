import { ChangeDetectionStrategy, Component, ViewEncapsulation } from '@angular/core';

type Tab = { label: string; route: string; iconName: string | null; iconSrc: string | null };

@Component({
  selector: 'app-cirklo-home',
  templateUrl: './cirklo-home.page.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class CirkloHomePage {
  tabs: Tab[] = [
    { label: 'app.oca.vouchers', route: 'vouchers', iconName: null, iconSrc: '/assets/icon/cirklo/business-and-finance.svg' },
    { label: 'app.oca.merchants', route: 'merchants', iconName: 'cart', iconSrc: null },
    { label: 'app.oca.info', route: 'info', iconName: null, iconSrc: '/assets/icon/cirklo/cirklo_light_white_filled.svg' },
  ];
  pageTitle = '';

  setTitle({ tab }: { tab: string }) {
    this.pageTitle = this.tabs.find(t => t.route === tab)?.label ?? '';
  }
}
