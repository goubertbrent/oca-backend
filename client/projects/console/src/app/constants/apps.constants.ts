import { NavigationAction } from '../interfaces';

export const enum HomescreenStyle {
  BRANDING = 'branding',
  NEWS = 'news',
  MESSAGING = 'messaging',
  TWO_BY_THREE = '2x3',
  THREE_BY_THREE = '3x3'
}

export const HOMESCREEN_STYLES: HomescreenStyle[] = [ HomescreenStyle.BRANDING, HomescreenStyle.NEWS,
  HomescreenStyle.MESSAGING, HomescreenStyle.MESSAGING, HomescreenStyle.TWO_BY_THREE, HomescreenStyle.THREE_BY_THREE ];
/**
 * Possible actions on a NavigationItem.
 * These are also translation keys, so when adding something don't forget to add a translation.
 */
export const NAVIGATION_ACTIONS: NavigationAction[] = [
  { value: 'news', action_type: null, label: 'rcc.news'},
  { value: 'messages', action_type: null, label: 'rcc.messages'},
  { value: 'scan', action_type: null, label: 'rcc.scan'},
  { value: 'services', action_type: null, label: 'rcc.services'},
  { value: 'friends', action_type: null, label: 'rcc.friends'},
  { value: 'directory', action_type: null, label: 'rcc.directory'},
  { value: 'profile', action_type: null, label: 'rcc.profile'},
  { value: 'more', action_type: null, label: 'rcc.more'},
  { value: 'settings', action_type: null, label: 'rcc.settings'},
  { value: 'community_services', action_type: null, label: 'rcc.community_services'},
  { value: 'merchants', action_type: null, label: 'rcc.merchants'},
  { value: 'associations', action_type: null, label: 'rcc.associations'},
  { value: 'emergency_services', action_type: null, label: 'rcc.emergency_services'},
  { value: 'stream', action_type: null, label: 'rcc.stream'},
  { value: 'qrcode', action_type: null, label: 'rcc.qrcode'},
  { value: 'jobs', action_type: null, label: 'rcc.jobs'},
  { value: 'app', action_type: 'open', label: 'rcc.app'},
  { value: 'gipod', action_type: 'map', label: 'rcc.gipod'},
  { value: 'services', action_type: 'map', label: 'rcc.services'},
  { value: 'reports', action_type: 'map', label: 'rcc.reports'},
];

export const NAVIGATION_ACTION_TYPES = [
  { value: null, label: 'rcc.open_activity' },
  { value: 'action', label: 'rcc.list_services_with_action' },
  { value: 'map', label: 'rcc.map' },
  { value: 'click', label: 'rcc.open_menu_item_of_service' },
  { value: 'embedded-app', label: 'rcc.open_embedded_application' },
  { value: 'open', label: 'rcc.open' },
];

export const COLLAPSE_NAVIGATION_ACTIONS = [
  'services', 'emergency_services', 'community_services', 'merchants', 'associations' ];
export const NAVIGATION_ACTION_TRANSLATIONS = [
  'News', 'Report Card', 'Messages', 'Agenda', 'Community Services', 'Merchants', 'Associations', 'Care', 'Friends',
  'Scan', 'Profile', 'Settings', 'Trainings', 'Collegues', 'More', 'Reserve', 'Order', 'QR code', 'Jobs' ];

/**
 * Languages supported by the clients (iOS, Android)
 */
export const APP_LANGUAGES: string[] = [ 'en', 'de', 'es', 'fr', 'it', 'nl', 'pt-br', 'ro', 'ru' ];
