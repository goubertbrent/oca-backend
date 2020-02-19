// From https://github.com/ionic-team/ionic-docs/blob/8270b35cf8221f4b427e98ba1fb1fc8feff4c666/src/components/color-gen/parse-css.ts
import { Color, RGB } from './color';

export function generateColor(name: string, value: string) {
  const color = new Color(value);
  const contrast = color.contrast();
  const tint = color.tint();
  const shade = color.shade();

  return {
    name,
    value,
    valueRgb: rgbToString(color.rgb),
    contrast: contrast.hex,
    contrastRgb: rgbToString(contrast.rgb),
    tint: tint.hex,
    shade: shade.hex,
  };
}


export function rgbToString(c: RGB): string {
  return `${c.r},${c.g},${c.b}`;
}

export function setColor(name: string, value: string) {
  const color = generateColor(name, value);
  const style = document.documentElement.style;
  style.setProperty(`--ion-color-${color.name}`, color.value);
  style.setProperty(`--ion-color-${color.name}-rgb`, color.valueRgb);
  style.setProperty(`--ion-color-${color.name}-contrast`, color.contrast);
  style.setProperty(`--ion-color-${color.name}-contrast-rgb`, color.contrastRgb);
  style.setProperty(`--ion-color-${color.name}-shade`, color.shade);
  style.setProperty(`--ion-color-${color.name}-tint`, color.tint);
}
