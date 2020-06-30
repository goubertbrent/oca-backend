import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { HoplrEvent } from '../../hoplr';

@Component({
  selector: 'hoplr-event-header',
  templateUrl: './event-header.component.html',
  styleUrls: ['./event-header.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EventHeaderComponent {
  @Input() event: HoplrEvent;
}
