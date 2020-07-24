import { initialStateResult, NewsItem, ResultState, stateError, stateLoading, stateSuccess } from '@oca/web-shared';
import { NewsActions, NewsActionTypes } from './news.actions';

export const newsFeatureKey = 'news';

export interface State {
  currentNewsItem: ResultState<NewsItem>;
}

const initialNewsState: State = {
  currentNewsItem: initialStateResult,
};

export function newsReducer(state: State = initialNewsState, action: NewsActions): State {
  switch (action.type) {
    case NewsActionTypes.GetNewsItem:
      return { currentNewsItem: stateLoading(initialNewsState.currentNewsItem.result) };
    case NewsActionTypes.GetNewsItemSuccess:
      return { currentNewsItem: stateSuccess(action.payload.data) };
    case NewsActionTypes.GetNewsItemFailure:
      return { currentNewsItem: stateError(action.error, state.currentNewsItem.result) };

  }
  return state;
}
