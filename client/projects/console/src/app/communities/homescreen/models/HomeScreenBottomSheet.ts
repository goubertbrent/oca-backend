// tslint:disable
/**
 * Our City App
 * Our City App internal apis
 *
 * The version of the OpenAPI document: 0.0.1
 * 
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */

import {
    HomeScreenBottomSheetHeader,
} from './';

/**
 * @export
 * @interface HomeScreenBottomSheet
 */
export interface HomeScreenBottomSheet {
    /**
     * @type {HomeScreenBottomSheetHeader}
     * @memberof HomeScreenBottomSheet
     */
    header: HomeScreenBottomSheetHeader;
    /**
     * @type {Array<{ [key: string]: object; }>}
     * @memberof HomeScreenBottomSheet
     */
    rows: Array<{ [key: string]: object; }>;
}