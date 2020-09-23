import { ChangeDetectionStrategy, Component, Input, OnChanges, SimpleChanges, ViewEncapsulation } from '@angular/core';
import { NewsCommunityMapping } from '../../news';
import { getCost, getReach } from '../../utils';

@Component({
  selector: 'oca-news-reach',
  templateUrl: './news-reach.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class NewsReachComponent implements OnChanges {
  @Input() defaultCommunityId: number;
  @Input() communityIds: number[];
  @Input() communityMapping: NewsCommunityMapping;
  reach: {
    total: string;
    cost: string;
  };

  ngOnChanges(changes: SimpleChanges): void {
    if (this.communityIds && this.communityMapping) {
      this.calculateReach();
    }
  }

  private calculateReach() {
    let totalUsers = 0;
    let costUsers = 0;
    for (const communityId of this.communityIds) {
      if (communityId in this.communityMapping) {
        const usersInCommunity = this.communityMapping[ communityId ].total_user_count;
        totalUsers += usersInCommunity;
        // Default app id is free
        const costCount = this.defaultCommunityId === communityId ? 0 : usersInCommunity;
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
