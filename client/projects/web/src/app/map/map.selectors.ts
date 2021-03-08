import {createFeatureSelector, createSelector} from '@ngrx/store';
import {mapFeatureKey, MapState} from './map.reducer';
import {SelectedMarker} from "./marker.model";
import {MapListSectionItemType, MapSectionType} from "@oca/web-shared";

export const selectMapState = createFeatureSelector<MapState>(mapFeatureKey);

export const getSelectedMarker = createSelector(selectMapState, state => removeUnsupportedItems(state.selectedMarker))
export const getLayerId = createSelector(selectMapState, state => state.selectedLayerId)

const SUPPORTED_SECTION_TYPES: MapSectionType[] = [
  MapSectionType.NEWS,
  MapSectionType.TEXT,
  MapSectionType.MEDIA,
  MapSectionType.NEWS_GROUP,
  MapSectionType.LIST
]
const SUPPORTED_LIST_ITEM_TYPES: MapListSectionItemType[] = [
  MapListSectionItemType.LINK,
  MapListSectionItemType.DYNAMIC_OPENING_HOURS,
  MapListSectionItemType.EXPANDABLE
]

function removeUnsupportedItems(marker: SelectedMarker | null): SelectedMarker | null {

  if (!marker)
    return null;
  return {
    ...marker, properties: {
      ...marker.properties,
      sections: marker.properties.sections
        .filter(section => SUPPORTED_SECTION_TYPES.includes(section.type))
        .map(section => {
          if (section.type === MapSectionType.LIST) {
            return {
              ...section, items: section.items.filter(item => {
                if (item.type == MapListSectionItemType.LINK) {
                  if (item.url?.startsWith('open://')) {
                    return false;
                  }
                }
                return SUPPORTED_LIST_ITEM_TYPES.includes(item.type);
              })
            }
          }
          return section;
        })
    }
  }
}
