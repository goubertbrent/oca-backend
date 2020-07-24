import { ChangeDetectionStrategy, Component, Input, OnChanges, SimpleChanges, ViewEncapsulation } from '@angular/core';
import { AppStatisticsMapping } from '@oca/web-shared';
import { getCost, getReach } from '../../utils';

@Component({
  selector: 'oca-news-reach',
  templateUrl: './news-reach.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class NewsReachComponent implements OnChanges {
  @Input() defaultAppId: string;
  @Input() appIds: string[];
  @Input() appStatistics: AppStatisticsMapping;
  reach: {
    total: string;
    cost: string;
  };

  ngOnChanges(changes: SimpleChanges): void {
    if (this.appIds && this.appStatistics) {
      this.calculateReach();
    }
  }

  private calculateReach() {
    let totalUsers = 0;
    let costUsers = 0;
    for (const appId of this.appIds) {
      if (appId in this.appStatistics) {
        const usersInApp = this.appStatistics[ appId ].total_user_count;
        totalUsers += usersInApp;
        // Default app id is free
        const costCount = this.defaultAppId === appId ? 0 : usersInApp;
        costUsers += costCount;
      }
    }
    const total = getReach(totalUsers);
    const costTotal = getReach(costUsers);
    this.reach = {
      total: `${total.lowerGuess} - ${total.higherGuess}`,
      cost: getCost('€', costTotal.lowerGuess, costTotal.higherGuess),
    };
  }
}
