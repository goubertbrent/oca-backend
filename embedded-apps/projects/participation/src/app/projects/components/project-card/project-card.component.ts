import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnChanges, Output, SimpleChanges } from '@angular/core';
import { Project, ProjectDetails } from '../../projects';

const MAX_PERCENT = 89;  // height % of the colored trophy when there's 0 progress. 0 % -> fully colored
@Component({
  selector: 'pp-project-card',
  templateUrl: 'project-card.component.html',
  styleUrls: ['./project-card.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProjectCardComponent implements OnChanges {
  @Input() project: Project;
  @Input() detailsLoading: boolean;
  @Input() projectDetails: ProjectDetails | null;
  @Output() projectClicked = new EventEmitter<Project>();

  projectProgress = 0;
  personalCount = 0;
  totalCount = 0;
  uiPercent = `${MAX_PERCENT}%`;


  ngOnChanges(changes: SimpleChanges): void {
    if (changes.projectDetails) {
      this.reCalulate();
    }
  }

  private reCalulate() {
    let percent = 0;
    let personalCount = 0;
    let totalCount = 0;
    if (this.projectDetails) {
      totalCount = this.projectDetails.statistics.total;
      const currentActions = Math.min(this.projectDetails.action_count, this.projectDetails.statistics.total);
      percent = Math.floor(100 * currentActions / this.projectDetails.action_count);
      if (this.projectDetails.statistics.personal) {
        personalCount = this.projectDetails.statistics.personal.total;
      }
    }
    this.projectProgress = percent;
    const uiPercent = Math.round(MAX_PERCENT - (percent / 100) * MAX_PERCENT);
    this.uiPercent = `${uiPercent}%`;
    this.personalCount = personalCount;
    this.totalCount = totalCount;
  }
}
