import { ChangeDetectionStrategy, Component, ViewEncapsulation } from '@angular/core';

/**
 * Empty component with a router outlet which is needed because ios refuses to show the initial component otherwise, for some reason.
 */
@Component({
  selector: 'trash-main-component',
  templateUrl: './main-component.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class MainComponentComponent {
}
