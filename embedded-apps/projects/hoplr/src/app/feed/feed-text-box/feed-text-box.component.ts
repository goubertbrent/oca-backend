import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

@Component({
  selector: 'hoplr-feed-text-box',
  templateUrl: './feed-text-box.component.html',
  styleUrls: ['./feed-text-box.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FeedTextBoxComponent {
  @Input() title: string | null = null;
}
