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
    HomeScreenBottomNavigation,
    HomeScreenBottomSheet,
    HomeScreenContent,
} from './';

/**
 * @export
 * @interface HomeScreen
 */
export interface HomeScreen {
    /**
     * @type {number}
     * @memberof HomeScreen
     */
    version: number;
    /**
     * @type {HomeScreenContent}
     * @memberof HomeScreen
     */
    content: HomeScreenContent;
    /**
     * @type {HomeScreenBottomNavigation}
     * @memberof HomeScreen
     */
    bottom_navigation: HomeScreenBottomNavigation;
    /**
     * @type {HomeScreenBottomSheet}
     * @memberof HomeScreen
     */
    bottom_sheet: HomeScreenBottomSheet;
    /**
     * Language to use when the user his language is not one of the available ones in the translation mapping
     * @type {string}
     * @memberof HomeScreen
     */
    default_language: string;
    /**
     * Translations for any string which could be translated on the homescreen. Properties that should be translated should contain a $ prefix. For example, label -> $trash_calendar
     * @type {{ [key: string]: { [key: string]: string; }; }}
     * @memberof HomeScreen
     */
    translations: { [key: string]: { [key: string]: string; }; };
}