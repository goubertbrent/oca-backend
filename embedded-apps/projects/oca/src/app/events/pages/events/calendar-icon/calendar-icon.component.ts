import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

@Component({
  selector: 'app-calendar-icon',
  templateUrl: './calendar-icon.component.html',
  styleUrls: ['./calendar-icon.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CalendarIconComponent {
  @Input() date: Date;
}
