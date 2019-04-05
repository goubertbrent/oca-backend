import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { Loadable } from './loadable';

@Component({
  selector: 'oca-loadable',
  templateUrl: './loadable.component.html',
  styleUrls: [ './loadable.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LoadableComponent {
  @Input() loadable: Loadable<any>;
}
