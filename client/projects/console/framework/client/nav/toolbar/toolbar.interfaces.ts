export const enum ToolbarItemTypes {
  ICON,
  BUTTON
}

export interface ToolbarItem {
  id: string;
  type: ToolbarItemTypes;
  label?: string;
  route?: string;
  // TODO remove as this is not serializable. Replace with new store action (ToolbarItemClicked action or something)
  onclick?: () => void;
  icon?: string; // Should be one of https://material.io/icons/
  disabled?: boolean;
  persistent?: boolean;
}
