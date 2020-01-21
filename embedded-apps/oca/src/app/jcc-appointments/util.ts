import { Product, ProductDetails } from './appointments';


export function fixProducts(products: Product[]): void {
  for (const product of products) {
    // Because of course it's a string containing a number
    product.productMaxCountForEvent = parseInt(product.productMaxCountForEvent as unknown as string, 10);
  }
}

export function fixProductDetails(product: ProductDetails): ProductDetails {
  // is actually a string
  const maxCountForEvent = parseInt(product.maxCountForEvent as unknown as string, 10);
  // decode from base64 to html
  const body = atob(typeof product.requisites === 'string' ? product.requisites : product.requisites[ 0 ]);
  // Extract content from <body> tag
  const dom = new DOMParser().parseFromString(body, 'text/html');
  const bodyNode = dom.getElementsByTagName('body').item(0);
  const requisites = bodyNode ? bodyNode.innerHTML : '';
  return { ...product, requisites, maxCountForEvent };
}

export function fixProductsDetailsMapping(products: { [ key: string ]: ProductDetails }) {
  const fixed: { [ key: string ]: ProductDetails } = {};
  for (const key of Object.keys(products)) {
    fixed[ key ] = fixProductDetails(products[ key ]);
  }
  return fixed;
}
