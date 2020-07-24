import { NewsItem, NewsItemBasicStatistics } from '@oca/web-shared';

export interface NewsListItem extends NewsItem {
  statistics?: NewsItemBasicStatistics;
}
