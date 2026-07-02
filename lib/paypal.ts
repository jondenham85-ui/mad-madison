const base = process.env.PAYPAL_ENV === 'live'
  ? 'https://api-m.paypal.com'
  : 'https://api-m.sandbox.paypal.com'
async function getAccessToken() {
  const creds = Buffer.from(process.env.PAYPAL_CLIENT_ID + ':' + process.env.PAYPAL_CLIENT_SECRET).toString('base64')
  const res = await fetch(base + '/v1/oauth2/token', {
    method: 'POST', headers: { Authorization: 'Basic ' + creds, 'Content-Type': 'application/x-www-form-urlencoded' },
    body: 'grant_type=client_credentials'
  })
  const data = await res.json()
  return data.access_token
}
export async function createOrder(amount: string, currency = 'USD') {
  const token = await getAccessToken()
  const res = await fetch(base + '/v2/checkout/orders', {
    method: 'POST',
    headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
    body: JSON.stringify({ intent: 'CAPTURE', purchase_units: [{ amount: { currency_code: currency, value: amount } }] })
  })
  return res.json()
}
export async function captureOrder(orderId: string) {
  const token = await getAccessToken()
  const res = await fetch(base + '/v2/checkout/orders/' + orderId + '/capture', {
    method: 'POST', headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' }
  })
  return res.json()
}
export async function getTransactions(startDate: string, endDate: string) {
  const token = await getAccessToken()
  const res = await fetch(base + '/v1/reporting/transactions?start_date=' + startDate + '&end_date=' + endDate + '&fields=all', {
    headers: { Authorization: 'Bearer ' + token }
  })
  return res.json()
}
