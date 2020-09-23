import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { NavigationItem } from '../../interfaces/misc.interfaces';

@Component({
  selector: 'rcc-navigation-cards',
  templateUrl: 'navigation-cards.component.html',
  styleUrls: ['./navigation-card.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NavigationCardsComponent {
  colorClasses = [ 'bg-red', 'bg-purple', 'bg-blue', 'bg-cyan', 'bg-yellow', 'bg-gray', 'bg-orange', 'bg-blue-gray' ];
  @Input() navigationItems: NavigationItem[];

  getBgClass(index: number) {
    const i = index > (this.colorClasses.length - 1) ? index - this.colorClasses.length : index;
    return this.colorClasses[ i ];
  }
}
