const domain = process.env.SHOPIFY_SHOP_DOMAIN
const token = process.env.SHOPIFY_ADMIN_API_TOKEN
const version = process.env.SHOPIFY_API_VERSION || '2024-04'
export async function shopifyGraphQL(query: string, variables = {}) {
  const res = await fetch('https://' + domain + '/admin/api/' + version + '/graphql.json', {
    method: 'POST',
    headers: { 'X-Shopify-Access-Token': token!, 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, variables })
  })
  return res.json()
}
export async function getOrders(limit = 10) {
  return shopifyGraphQL('{ orders(first:' + limit + ') { edges { node { id name totalPriceSet { shopMoney { amount currencyCode } } displayFinancialStatus createdAt } } } }')
}
export async function getProducts(limit = 10) {
  return shopifyGraphQL('{ products(first:' + limit + ') { edges { node { id title status totalInventory priceRangeV2 { minVariantPrice { amount currencyCode } } } } } }')
}
