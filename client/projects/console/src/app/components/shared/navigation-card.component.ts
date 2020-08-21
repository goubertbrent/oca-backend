import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { NavigationItem } from '../../interfaces/misc.interfaces';

// todo should always be the same height
@Component({
  selector: 'rcc-navigation-cards',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'navigation-cards.component.html',
  styles: [ `
    a {
      text-decoration: none;
    }

    mat-card-title {
      font-size: 1.2em !important;
    }` ],
})
export class NavigationCardsComponent {
  colorClasses = [ 'bg-red', 'bg-purple', 'bg-blue', 'bg-cyan', 'bg-yellow', 'bg-gray', 'bg-orange', 'bg-blue-gray' ];
  @Input() navigationItems: NavigationItem[];

  getBgClass(index: number) {
    const i = index > (this.colorClasses.length - 1) ? index - this.colorClasses.length : index;
    return this.colorClasses[ i ];
  }

  isFa(iconName: string) {
    return iconName.startsWith('fa-');
  }
}
