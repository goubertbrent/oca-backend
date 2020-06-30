import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { HoplrComment, HoplrRate } from '../../hoplr';

@Component({
  selector: 'hoplr-feed-comment',
  templateUrl: './feed-comment.component.html',
  styleUrls: ['./feed-comment.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FeedCommentComponent {
  @Input() comment: HoplrComment;
  @Input() rates?: HoplrRate[];
}
