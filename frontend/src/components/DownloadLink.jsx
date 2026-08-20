import { BASE } from '../api/client'

export default function DownloadLink({ path, label, className = 'btn' }) {
  return (
    <a className={className} href={`${BASE}${path}`}>
      {label}
    </a>
  )
}
