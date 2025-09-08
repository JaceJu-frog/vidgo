import { BACKEND } from '@/composables/ConfigAPI'
export async function getCSRFToken() {
  const res = await fetch(`${BACKEND}/api/get_csrf_token/`, {
    credentials: 'include', // keep cookies in case the view sets one
  })
  if (!res.ok) throw new Error('Could not get CSRF token')

  const { csrf_token } = await res.json() // <- extract the field
  console.log(csrf_token)
  return csrf_token // <- plain string
}

export function getCookie(name: string) {
  return (
    document.cookie
      .split('; ')
      .find((row) => row.startsWith(name + '='))
      ?.split('=')[1] || ''
  )
}
